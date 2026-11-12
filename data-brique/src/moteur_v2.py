"""Moteur V2 : brief client -> division + arome principal + top k produits.

Meme format de sortie que MoteurV1 (cles division, scores_division, top), plus arome et mode.
1. llama3.2:3b (Ollama) extrait {application, division, aromes} du brief ; on garde la division
   et le premier arome (cf. benchmark/resultats.md : les aromes suivants sont souvent inventes).
   "application" est demandee en premier pour que le modele nomme le produit avant de choisir la
   division (sans elle, "une petite creme au gout d'enfance" partait en fragrance).
2. Flavors : bge-m3 compare le brief enrichi de l'arome aux vecteurs du catalogue (cosinus).
   Fragrance : TF-IDF de la V1.
Repli : si Ollama ne repond pas, chaque etape concernee retombe sur la V1 (mots-cles, TF-IDF).
Relance : si le brief ne contient ni produit ni arome identifiable, aucune recherche n'est faite
(arome None, mode "relance") et une question est renvoyee. Conversation garde le contexte.
"""
import hashlib
import json
import os
import re
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from sklearn.metrics.pairwise import cosine_similarity

from src.moteur_v1 import COLONNES_RESULTAT, URL_PRODUIT, MoteurV1, detecter_division, normaliser

VERSION_MODELE = "v2-llama3.2-bge-m3"
RACINE = Path(__file__).resolve().parents[1]
CATALOGUE_COMPLET = RACINE / "data" / "processed" / "catalogue_complet" / "flavors_catalogue_complet.csv"
CACHE_DEFAUT = RACINE / "benchmark" / "cache"
# 127.0.0.1 et non localhost : sous Windows, localhost tente d'abord IPv6 (~2 s par requete)
OLLAMA_DEFAUT = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")

MODELE_LLM = "llama3.2:3b"
MODELE_EMBEDDING = "bge-m3"
LONGUEUR_INGREDIENTS = 300  # texte indexe identique au benchmark (vecteurs en cache reutilises)

SCHEMA = {
    "type": "object",
    "properties": {
        "application": {"type": "string"},
        "division": {"type": "string", "enum": ["flavors", "fragrance", "aucune"]},
        "aromes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["application", "division", "aromes"],
}

# prompt du benchmark sans la cle contraintes ni l'exemple "biscuit" (recopie tel quel par les
# modeles qwen), avec une regle pour les mots ambigus comme "creme" et une sortie "rien
# d'identifiable" pour les messages vagues
SYSTEME = """Tu analyses les demandes de clients de Givaudan, qui crée des arômes alimentaires \
(division "flavors") et des parfums pour l'hygiène, la cosmétique et la parfumerie \
(division "fragrance"). Les clients sont de petites marques qui décrivent leur projet avec leurs mots.
Réponds uniquement par un objet JSON avec les clés :
- "application" : le type de produit final cité par le client, en quelques mots ; "" si le \
message ne mentionne aucun produit ;
- "division" : "flavors" si le produit final se mange ou se boit, "fragrance" s'il se sent ou \
s'applique sur le corps ; un mot comme "crème" peut désigner les deux : le client qui parle de \
"goût" ou de "saveur" veut un arôme alimentaire, celui qui parle d'"odeur" ou de ce qui "sent" \
veut un parfum ; "aucune" si le message ne parle ni d'un produit, ni d'un goût, ni d'une odeur \
(salutation, question hors sujet, demande trop vague) ;
- "aromes" : les arômes ou notes recherchés, en un ou deux mots chacun, en français, le principal \
en premier ; si le client décrit un goût ou une odeur sans nommer d'arôme, donne l'arôme le plus \
probable ; liste vide si le message ne parle d'aucun goût ni d'aucune odeur.
N'invente jamais un produit ou un arôme que le message ne suggère pas."""

QUESTION_RELANCE = "Quel goût recherchez-vous ? Pour quel type de produit ?"
QUESTION_PRODUIT = "Pour quel type de produit ?"
QUESTION_AROME = {"flavors": "Quel goût recherchez-vous ?", "fragrance": "Quelle odeur recherchez-vous ?"}

# garde-fou contre l'invention : un arome deduit (ex. "vanille" pour un gout d'enfance) n'est
# accepte que si le client parle de gout, d'odeur ou d'une sensation
SENSORIEL = re.compile(r"\b(?:gout|saveur|arom|odeur|senteur|parfum|sent|fragran|note|fruit|sucr"
                       r"|acidul|gourmand|frais|fraich|epic|boise|flor|fleur)")
MOTS_GENERIQUES = {"produit", "marque", "projet", "gamme", "chose", "article", "truc", "aucun",
                   "aucune", "gout", "saveur", "odeur", "senteur", "arome"}
# noms de produits courants : repli quand le modele reformule le produit ("yaourt a boire" ->
# "boisson") et que sa reformulation n'apparait pas dans le message
PRODUITS = re.compile(
    r"\b(yaourts? a boire|yaourts?|cremes? desserts?|desserts?|cremes?|flans?|mousses?|glaces?"
    r"|boissons?|sirops?|limonades?|sodas?|jus|smoothies?|shakes?|laits?|eaux? de toilette|eaux?"
    r"|the glace|cafes?|biscuits?|gateaux?|compotes?|bonbons?|savons?|gels? douche"
    r"|shampoo?ings?|deodorants?|parfums?|bougies?|lessives?|lotions?)\b")


def _racines(texte: str) -> set[str]:
    """Racines (5 premieres lettres) des mots de 4 lettres ou plus, sans accents."""
    return {mot[:5] for mot in re.findall(r"[a-z]+", normaliser(texte))
            if len(mot) >= 4 and mot not in MOTS_GENERIQUES}


def ancre(terme: str | None, brief: str) -> bool:
    """Le terme partage-t-il au moins une racine de mot avec le brief ?"""
    return bool(terme) and bool(_racines(terme) & _racines(brief))


def texte_index(df: pd.DataFrame) -> list[str]:
    """Nom + categorie + 300 premiers caracteres des ingredients (comme le benchmark)."""
    return (df["product_name"].fillna("") + " | " + df["query_category"].str.replace("_", " ")
            + " | " + df["ingredients_text"].fillna("").str[:LONGUEUR_INGREDIENTS]).tolist()


class OllamaIndisponible(Exception):
    pass


class MoteurV2:
    version = VERSION_MODELE

    def __init__(self, catalogue: str = "echantillon", ollama_url: str = OLLAMA_DEFAUT,
                 dossier_cache: Path = CACHE_DEFAUT, delai_llm: float = 60.0):
        """catalogue : "echantillon" (Flavors de sample_v1, vecteurs du benchmark) ou "complet"
        (8 943 produits ; vecteurs a calculer une fois avec indexer(), ~1 h 30 sur CPU)."""
        if catalogue not in ("echantillon", "complet"):
            raise ValueError("catalogue doit valoir 'echantillon' ou 'complet'")
        self.catalogue = catalogue
        self.ollama_url = ollama_url.rstrip("/")
        self.dossier_cache = Path(dossier_cache)
        self.delai_llm = delai_llm
        self.v1 = MoteurV1()  # mots-cles + TF-IDF : repli et recherche Fragrance

        if catalogue == "echantillon":
            self.flavors = self.v1.index["flavors"][0]  # meme ordre que les vecteurs du benchmark
            self.fichier_vecteurs = self.dossier_cache / f"{MODELE_EMBEDDING}.npz"
        else:
            df = pd.read_csv(CATALOGUE_COMPLET, dtype=str)
            df["url_produit"] = [URL_PRODUIT[s].format(code=c)
                                 for s, c in zip(df["source"], df["code"])]
            self.flavors = df.reset_index(drop=True)
            self.fichier_vecteurs = self.dossier_cache / f"{MODELE_EMBEDDING}_complet.npz"
        self.textes = texte_index(self.flavors)
        self.vecteurs = None  # charges a la premiere requete (necessite le digest Ollama)

    # --- Ollama -------------------------------------------------------------------------------

    def _post(self, chemin: str, delai: float, **corps) -> dict:
        try:
            reponse = requests.post(f"{self.ollama_url}{chemin}", json=corps, timeout=delai)
            reponse.raise_for_status()
            return reponse.json()
        except (requests.RequestException, ValueError) as erreur:
            raise OllamaIndisponible(str(erreur)) from erreur

    def _embed(self, textes: list[str]) -> np.ndarray:
        vecteurs = np.asarray(self._post("/api/embed", 120, model=MODELE_EMBEDDING, input=textes,
                                         truncate=True, keep_alive="30m")["embeddings"],
                              dtype=np.float32)
        return vecteurs / np.linalg.norm(vecteurs, axis=1, keepdims=True)

    def _cle_cache(self) -> str:
        """Meme cle que benchmark/run_benchmark.py : modele + digest Ollama + prefixe + textes."""
        try:
            modeles = requests.get(f"{self.ollama_url}/api/tags", timeout=10).json()["models"]
        except (requests.RequestException, ValueError, KeyError) as erreur:
            raise OllamaIndisponible(str(erreur)) from erreur
        digest = next((m["digest"] for m in modeles
                       if m["name"].removesuffix(":latest") == MODELE_EMBEDDING), None)
        if digest is None:
            raise OllamaIndisponible(f"{MODELE_EMBEDDING} absent d'Ollama (ollama pull {MODELE_EMBEDDING})")
        return hashlib.sha256("\n".join([MODELE_EMBEDDING, digest, "", *self.textes]).encode()).hexdigest()

    def _vecteurs(self) -> np.ndarray:
        if self.vecteurs is None:
            cle = self._cle_cache()
            if not self.fichier_vecteurs.exists() or str(np.load(self.fichier_vecteurs)["cle"]) != cle:
                raise FileNotFoundError(
                    f"Vecteurs {MODELE_EMBEDDING} absents ou perimes : {self.fichier_vecteurs}. "
                    "Echantillon : python benchmark/run_benchmark.py ; complet : MoteurV2('complet').indexer()")
            self.vecteurs = np.load(self.fichier_vecteurs)["vecteurs"]
        return self.vecteurs

    def indexer(self, taille_lot: int = 32) -> float:
        """Calcule et met en cache les vecteurs du catalogue (long : a lancer volontairement)."""
        cle, debut = self._cle_cache(), time.perf_counter()
        morceaux = [self._embed(self.textes[i:i + taille_lot])
                    for i in range(0, len(self.textes), taille_lot)]
        secondes = time.perf_counter() - debut
        self.dossier_cache.mkdir(parents=True, exist_ok=True)
        np.savez(self.fichier_vecteurs, vecteurs=np.vstack(morceaux), secondes=secondes, cle=cle)
        self.vecteurs = None
        return secondes

    # --- Pipeline -----------------------------------------------------------------------------

    def comprendre(self, brief: str) -> tuple[str | None, str | None, str | None]:
        """llama3.2:3b -> (division, arome principal, application), sans invention :
        application et arome sont mis a None s'ils n'ont aucun appui dans le brief, division a
        None si le modele repond "aucune". Leve OllamaIndisponible."""
        reponse = self._post(
            "/api/chat", self.delai_llm, model=MODELE_LLM, stream=False, format=SCHEMA,
            keep_alive="30m", options={"temperature": 0, "seed": 42},
            messages=[{"role": "system", "content": SYSTEME}, {"role": "user", "content": brief}])
        try:
            sortie = json.loads(reponse["message"]["content"])
            division = sortie["division"]
            application = str(sortie.get("application") or "").strip() or None
            aromes = [a.strip() for a in sortie.get("aromes", []) if isinstance(a, str) and a.strip()]
        except (KeyError, TypeError, ValueError, AttributeError) as erreur:
            raise OllamaIndisponible(f"sortie LLM invalide : {erreur}") from erreur
        if division not in ("flavors", "fragrance", "aucune"):
            raise OllamaIndisponible(f"division inattendue : {division!r}")
        arome = aromes[0] if aromes else None
        if arome and not (ancre(arome, brief) or SENSORIEL.search(normaliser(brief))):
            arome = None
        if not (application and ancre(application, brief)):
            produit = PRODUITS.search(normaliser(brief))
            application = produit.group(0) if produit else None
        return (None if division == "aucune" else division), arome, application

    def _top_tfidf(self, division: str, brief: str, k: int) -> pd.DataFrame:
        """Recherche TF-IDF de la V1 (meme calcul et meme ordre que MoteurV1.recommander)."""
        df_div, vectoriseur, matrice = self.v1.index[division]
        sims = cosine_similarity(vectoriseur.transform([normaliser(brief)]), matrice).ravel()
        ordre = sims.argsort()[::-1][:k]
        top = df_div.iloc[ordre].copy()
        top["score"] = sims[ordre].round(3)
        return top[COLONNES_RESULTAT].reset_index(drop=True)

    def _top_embedding(self, requete: str, k: int) -> pd.DataFrame:
        vecteurs = self._vecteurs()
        sims = vecteurs @ self._embed([requete])[0]
        ordre = np.argsort(-sims, kind="stable")[:k]
        top = self.flavors.iloc[ordre].copy()
        top["score"] = sims[ordre].round(3)
        return top[COLONNES_RESULTAT].reset_index(drop=True)

    def _relance(self, scores_division: dict, etapes: dict) -> dict:
        return {"division": "indeterminee", "scores_division": scores_division,
                "top": pd.DataFrame(columns=COLONNES_RESULTAT), "arome": None, "application": None,
                "mode": "relance", "question": QUESTION_RELANCE, "etapes": etapes}

    def recommander(self, brief: str, k: int = 5) -> dict:
        """Sortie de MoteurV1 + arome (principal, ou None), application, mode, question, etapes.

        mode : "v2" (LLM + recherche V2), "v2_partiel" (LLM ok mais bge-m3 indisponible :
        TF-IDF V1 sur la division du LLM), "repli_v1" (Ollama indisponible : V1 complete),
        "relance" (ni produit ni arome identifiable : pas de recherche, top vide).
        question : relance a poser au client (None si la demande est complete).
        """
        division_v1, scores_division = detecter_division(brief)  # renvoye comme en V1
        try:
            division, arome, application = self.comprendre(brief)
        except OllamaIndisponible:
            etapes = {"comprehension": "mots-cles v1", "recherche": "tfidf v1"}
            if not any(scores_division.values()):
                return self._relance(scores_division, etapes)
            return {**self.v1.recommander(brief, k), "arome": None, "application": None,
                    "mode": "repli_v1", "question": None, "etapes": etapes}

        etapes, mode = {"comprehension": MODELE_LLM}, "v2"
        if arome is None and application is None:
            return self._relance(scores_division, etapes)
        if division is None:  # "aucune" alors qu'un produit ou un arome est cite
            if division_v1 == "indeterminee":
                return self._relance(scores_division, etapes)
            division = division_v1

        if division == "fragrance":
            top = self._top_tfidf(division, brief, k)
            etapes["recherche"] = "tfidf v1"
        else:
            # brief enrichi de l'arome extrait s'il n'y figure pas ("gout d'enfance" -> + "vanille")
            requete = (brief if arome is None or normaliser(arome) in normaliser(brief)
                       else f"{brief} {arome}")
            try:
                top = self._top_embedding(requete, k)
                etapes["recherche"] = f"{MODELE_EMBEDDING} ({self.catalogue})"
            except (OllamaIndisponible, FileNotFoundError):
                top = self._top_tfidf(division, requete, k)
                etapes["recherche"], mode = "tfidf v1", "v2_partiel"
        question = QUESTION_AROME[division] if arome is None else (
            QUESTION_PRODUIT if application is None else None)
        return {"division": division, "scores_division": scores_division, "top": top,
                "arome": arome, "application": application, "mode": mode, "question": question,
                "etapes": etapes}


# debuts de message qui signalent un complement ("plutot fruite", "pour des enfants")
CONNECTEURS = ("plutot", "pour", "avec", "sans", "et", "mais", "moins", "plus", "pas", "un peu",
               "en", "aussi", "par contre", "surtout", "si possible")
MOTS_COURT = 4


class Conversation:
    """Garde la demande en cours : une reponse courte la complete au lieu de la remplacer.

    Le message est un complement si une demande est en cours et que :
    - la reponse precedente etait une relance (question posee au client), ou
    - le message commence par un connecteur ("plutot", "pour", "sans"...), ou
    - le message est court (4 mots ou moins) et ne cite aucun produit.
    Sinon c'est une nouvelle demande. reinitialiser() oublie le contexte.
    fonction : ce qui repond au brief complet (defaut moteur.recommander ; V2.1 : moteur.pistes).
    """

    def __init__(self, moteur: MoteurV2, fonction=None):
        self.moteur = moteur
        self.fonction = fonction or moteur.recommander
        self.demande: str | None = None
        self.relance_en_attente = False

    def reinitialiser(self) -> None:
        self.demande, self.relance_en_attente = None, False

    def _est_complement(self, message: str) -> bool:
        if self.demande is None:
            return False
        if self.relance_en_attente:
            return True
        texte = " ".join(re.findall(r"[a-z]+", normaliser(message)))
        if any(texte == c or texte.startswith(c + " ") for c in CONNECTEURS):
            return True
        if len(texte.split()) <= MOTS_COURT:
            try:
                return self.moteur.comprendre(message)[2] is None
            except OllamaIndisponible:
                return True
        return False

    def repondre(self, message: str, k: int = 5) -> dict:
        complement = self._est_complement(message)
        brief = f"{self.demande}, {message}" if complement else message
        resultat = self.fonction(brief, k)
        self.demande = brief
        self.relance_en_attente = resultat["mode"] == "relance"
        return {**resultat, "brief": brief, "complement": complement}


# --- V2.1 : pistes d'aromes a partir d'une etude de marche interne ------------------------------
#
# Les petits clients veulent creer leur propre produit avec un arome Givaudan : le bot ne montre
# aucun produit ni aucune marque. Les produits proches du brief servent d'etude de marche interne
# (quels aromes et quelles associations le marche utilise deja).

VERSION_V21 = "v2.1-pistes-aromes"
N_MARCHE = 50  # produits proches analyses
MIN_ASSOCIATION = 3  # produits avec l'arome principal requis pour mesurer ses associations

# liste de reference : nom affiche -> motifs (texte normalise sans accents), anglais inclus car
# beaucoup de noms de produits sont en anglais. Ordre important : les motifs composes ("citron
# vert", "fleur d'oranger") sont cherches avant les simples, et le texte trouve est efface.
AROMES_FLAVORS = {
    "citron vert": r"citrons? verts?|\blimes?\b|combava",
    "fleur d'oranger": r"fleur d.oranger",
    "fruits rouges": r"fruits? rouges?|red fruits?|fruits des bois",
    "fruit de la passion": r"fruits? de la passion|passion|maracuja",
    "vanille": r"van+il+|vanilla",
    "chocolat": r"chocolat|chocolate|cacao|cocoa|\bchoco\b|schokolade",
    "caramel": r"caramel",
    "praliné": r"pralin",
    "pistache": r"pistach",
    "noisette": r"noisettes?|hazelnut|haselnuss",
    "amande": r"amandes?|almonds?",
    "coco": r"\bcoco\b|coconut",
    "café": r"\bcafe\b|coffee|\bmoka\b|cap+uc+in+o|espresso|latte",
    "thé": r"\bthe (?:vert|noir|blanc|glace)|matcha|earl grey",
    "mangue": r"mangues?|mango",
    "pêche": r"\bpeches?\b|peach",
    "abricot": r"abricots?|apricot",
    "banane": r"bananes?|banana",
    "ananas": r"ananas|pineapple",
    "fraise": r"fraises?|strawberr|erdbeer",
    "framboise": r"framboises?|raspberr|himbeer",
    "myrtille": r"myrtilles?|blueberr|bleuets?",
    "cassis": r"cassis|blackcurrant",
    "cerise": r"cerises?|cherr(?:y|ies)|griottes?",
    "mûre": r"\bmures?\b|blackberr",
    "grenade": r"\bgrenades?\b|pomegranate",
    "grenadine": r"grenadine",
    "citron": r"citrons?|lemon|limone",
    "orange": r"\boranges?\b|sanguine",
    "pamplemousse": r"pamplemousse|grapefruit",
    "yuzu": r"yuzu",
    "pomme": r"\bpommes?\b|\bapples?\b",
    "poire": r"\bpoires?\b|\bpears?\b",
    "litchi": r"litchis?|lychees?",
    "kiwi": r"\bkiwis?\b",
    "melon": r"\bmelons?\b",
    "pastèque": r"pasteques?|watermelon",
    "figue": r"\bfigues?\b",
    "menthe": r"menthe|\bmint\b|peppermint",
    "cannelle": r"cannelle|cinnamon",
    "gingembre": r"gingembre|ginger",
    "réglisse": r"reglisse|licorice",
    "speculoos": r"specul+o+s",
    "miel": r"\bmiel\b|honey",
    "biscuit": r"biscuit|cookie",
    "cola": r"\bcola\b",
}
AROMES_FRAGRANCE = {
    "fleur d'oranger": r"fleur d.oranger|neroli",
    "fleur de coton": r"fleur de coton|coton",
    "fruits rouges": r"fruits? rouges?|red fruits?",
    "lavande": r"lavande|lavandula|lavender",
    "rose": r"\brose\b|rosa damascena",
    "jasmin": r"jasmin",
    "muguet": r"muguet",
    "violette": r"violette",
    "monoï": r"monoi|tiare",
    "ylang-ylang": r"ylang",
    "verveine": r"verveine|verbena",
    "bergamote": r"bergamot|bergamia",
    "agrumes": r"agrumes?|citrus(?! (?:limon|aurantium))",
    "citron": r"citrons?|lemon|citrus limon",
    "orange": r"\boranges?\b|citrus aurantium",
    "pamplemousse": r"pamplemousse|grapefruit",
    "mandarine": r"mandarine",
    "menthe": r"menthe|\bmint\b|mentha",
    "eucalyptus": r"eucalyptus",
    "thé vert": r"the vert|green tea|camellia sinensis",
    "aloe vera": r"\baloe",
    "concombre": r"concombre|cucumber",
    "vanille": r"van+il+|vanilla",
    "fève tonka": r"tonka",
    "ambre": r"\bambre\b|\bamber\b",
    "musc": r"\bmusc|\bmusk",
    "santal": r"santal|sandalwood",
    "cèdre": r"cedre|cedarwood|cedrus",
    "vétiver": r"vetiver",
    "patchouli": r"patchouli",
    "boisé": r"\bboise|\bwoody",
    "amande": r"amandes?|almond",
    "coco": r"\bcoco\b|coconut",
    "miel": r"\bmiel\b|honey",
    "pomme": r"\bpommes?\b|\bapples?\b",
    "figue": r"\bfigues?\b",
}
# mentions qui ne sont pas un arome : acidifiant, colorant, matiere grasse, sel
EXCLUSIONS = re.compile(r"beurre de cacao|cocoa butter|jus de citron(?: concentre)?|acide citrique"
                        r"|colorant[^,;.]*caramel|caramel ordinaire|e ?150[a-d]?|fleur de sel")
_MOTIFS = {div: [(nom, re.compile(motif)) for nom, motif in aromes.items()]
           for div, aromes in (("flavors", AROMES_FLAVORS), ("fragrance", AROMES_FRAGRANCE))}


def extraire_aromes(texte: str, division: str = "flavors") -> list[str]:
    """Aromes de la liste de reference cites dans un texte (nom ou ingredients), sans doublon."""
    texte = EXCLUSIONS.sub(" ", normaliser(texte or ""))
    trouves = []
    for nom, motif in _MOTIFS[division]:
        if motif.search(texte):
            trouves.append(nom)
            texte = motif.sub(" ", texte)  # "citron vert" ne compte pas aussi "citron"
    return trouves


def _produits(n: int) -> str:
    return f"{n} produit{'s' if n > 1 else ''}"


FEMININS = {"vanille", "pistache", "noisette", "amande", "mangue", "pêche", "banane", "fraise",
            "framboise", "myrtille", "cerise", "mûre", "grenade", "grenadine", "pomme", "poire",
            "figue", "menthe", "cannelle", "réglisse", "pastèque", "fleur d'oranger", "lavande",
            "rose", "verveine", "bergamote", "mandarine", "violette", "fève tonka",
            "fleur de coton"}


def seul(arome: str) -> str:
    if arome.split()[0].endswith("s") and arome not in ("cassis", "speculoos", "ananas"):
        return "seuls"
    return "seule" if arome in FEMININS else "seul"


def a_la(arome: str) -> str:
    """'a la pistache', 'au chocolat', "a l'orange", 'aux fruits rouges'."""
    if arome.split()[0].endswith("s") and arome not in ("cassis", "speculoos", "ananas"):
        return f"aux {arome}"
    if normaliser(arome)[0] in "aeiouyh":
        return f"à l'{arome}"
    return f"à la {arome}" if arome in FEMININS else f"au {arome}"


class MoteurV21(MoteurV2):
    """V2.1 : meme comprehension (llama3.2:3b) et meme recherche (bge-m3 / TF-IDF) que la V2, mais
    la sortie est une liste de pistes d'aromes, sans produit ni marque.

    recommander() reste celui de la V2 (inchange) ; la V2.1 repond avec pistes().
    """

    version = VERSION_V21

    def _proches(self, division: str, requete: str, n: int) -> tuple[pd.DataFrame, str]:
        """Les n produits les plus proches de la requete (bge-m3 pour Flavors, sinon TF-IDF V1)."""
        if division == "flavors":
            try:
                sims = self._vecteurs() @ self._embed([requete])[0]
                proches, recherche = self.flavors.iloc[np.argsort(-sims, kind="stable")[:n]], \
                    f"{MODELE_EMBEDDING} ({self.catalogue})"
            except (OllamaIndisponible, FileNotFoundError):
                proches, recherche = None, "tfidf v1"
        else:
            proches, recherche = None, "tfidf v1"
        if proches is None:
            df_div, vectoriseur, matrice = self.v1.index[division]
            sims = cosine_similarity(vectoriseur.transform([normaliser(requete)]), matrice).ravel()
            proches = df_div.iloc[sims.argsort()[::-1][:n]]
        return proches, recherche

    def _marche(self, division: str, requete: str, n: int = N_MARCHE) -> tuple[list[list[str]], str]:
        """Aromes cites par chacun des n produits les plus proches (etude interne, non affichee)."""
        proches, recherche = self._proches(division, requete, n)
        textes = proches["product_name"].fillna("") + " | " + proches["ingredients_text"].fillna("")
        return [extraire_aromes(t, division) for t in textes], recherche

    def _relance(self, scores_division: dict, etapes: dict, question: str = QUESTION_RELANCE,
                 division: str = "indeterminee", aromes_frequents=None) -> dict:
        return {"division": division, "scores_division": scores_division, "arome": None,
                "application": None, "mode": "relance", "question": question, "pistes": [],
                "marche": {"aromes_frequents": aromes_frequents or []}, "etapes": etapes,
                "version_modele": VERSION_V21}

    def pistes(self, brief: str, k: int = 3) -> dict:
        """3 pistes : (a) arome principal seul, (b) association la plus frequente sur le marche,
        (c) association plus originale (presente mais rare). Aucun produit ni marque en sortie."""
        division_v1, scores_division = detecter_division(brief)
        try:
            division, arome, application = self.comprendre(brief)
            etapes = {"comprehension": MODELE_LLM}
            mode = "v2.1"
        except OllamaIndisponible:
            # repli : division par mots-cles, arome = 1er arome de la liste de reference cite
            division = None if division_v1 == "indeterminee" else division_v1
            cites = extraire_aromes(brief, division or "flavors")
            arome, application = (cites[0] if cites else None), None
            etapes, mode = {"comprehension": "mots-cles v1 + liste d'aromes"}, "repli_v1"
            if division is None:
                return self._relance(scores_division, etapes)

        if arome is None and application is None:
            return self._relance(scores_division, etapes)
        if division is None:
            if division_v1 == "indeterminee":
                return self._relance(scores_division, etapes)
            division = division_v1

        requete = brief if arome is None or normaliser(arome) in normaliser(brief) else f"{brief} {arome}"
        marche, etapes["recherche"] = self._marche(division, requete)
        return self._pistes_depuis(division, arome, application, marche, scores_division, etapes,
                                   mode, k)

    def _pistes_depuis(self, division: str, arome: str | None, application: str | None,
                       marche: list[list[str]], scores_division: dict, etapes: dict, mode: str,
                       k: int = 3) -> dict:
        """Pistes a partir des aromes cites par chaque produit du marche proche (V2.1 et V2.2)."""
        frequence = Counter(a for aromes in marche for a in aromes)
        etude = {"nb_produits_analyses": len(marche),
                 "aromes_frequents": frequence.most_common(5)}

        if arome is None:  # produit connu, gout inconnu : relance avec les gouts du marche
            courants = ", ".join(f"{a} ({_produits(n)})" for a, n in frequence.most_common(3))
            question = QUESTION_AROME[division] + (
                f" Pour ce type de produit, les goûts les plus courants sur le marché sont : "
                f"{courants}." if courants else "")
            return {**self._relance(scores_division, etapes, question, division,
                                    frequence.most_common(5)), "application": application}

        # arome principal ramene a la liste de reference ("noix de coco" -> "coco")
        reference = extraire_aromes(arome, division)
        principal = reference[0] if reference else arome.lower()
        avec = [a for a in marche if principal in a]  # vide si l'arome est hors liste
        n_principal = len(avec)
        etude["nb_avec_arome_principal"] = n_principal

        pistes = [{"type": "principal", "aromes": [principal], "nb_produits": n_principal,
                   "explication": (
                       f"{principal.capitalize()} {seul(principal)} : un goût franc, facile à reconnaître. "
                       + (f"{n_principal} des {len(marche)} produits les plus proches de votre "
                          f"projet l'utilisent." if n_principal else
                          f"Aucun des {len(marche)} produits les plus proches de votre projet ne "
                          "l'utilise : c'est une place encore libre sur ce marché."))}]

        associes = Counter(a for aromes in avec for a in aromes if a != principal)
        if n_principal >= MIN_ASSOCIATION and associes:
            etude["associations"] = associes.most_common()
            # (b) la plus frequente ; egalite -> arome le plus courant sur le marche, puis nom
            ordre = sorted(associes, key=lambda a: (-associes[a], -frequence[a], a))
            frequente = ordre[0]
            pistes.append({"type": "association_frequente", "aromes": [principal, frequente],
                           "nb_produits": associes[frequente], "observee": True,
                           "explication": (
                               f"{principal.capitalize()} + {frequente} : l'association la plus "
                               f"fréquente sur le marché ({_produits(associes[frequente])} sur "
                               f"{n_principal} {a_la(principal)}). Un choix rassurant, que les "
                               "consommateurs connaissent déjà.")})
            # (c) presente mais rare : la moins frequente ; egalite -> arome le plus rare du marche
            rares = sorted((a for a in associes if a != frequente),
                           key=lambda a: (associes[a], frequence[a], a))
            if rares:
                originale = rares[0]
                pistes.append({"type": "association_originale", "aromes": [principal, originale],
                               "nb_produits": associes[originale], "observee": True,
                               "explication": (
                                   f"{principal.capitalize()} + {originale} : une association "
                                   f"rare sur le marché ({_produits(associes[originale])}), qui "
                                   "peut vous démarquer tout en restant crédible.")})
        else:
            # arome principal trop rare pour mesurer ses associations : on le dit, et on s'appuie
            # sur les aromes du marche proche (association non observee, a valider en degustation)
            autres = Counter({a: n for a, n in frequence.items() if a != principal})
            if autres:
                frequente = sorted(autres, key=lambda a: (-autres[a], a))[0]
                pistes.append({"type": "association_frequente", "aromes": [principal, frequente],
                               "nb_produits": autres[frequente], "observee": False,
                               "explication": (
                                   f"{principal.capitalize()} + {frequente} : le goût {frequente} "
                                   f"est le plus présent dans les produits proches de votre projet "
                                   f"({_produits(autres[frequente])}). L'association avec "
                                   f"{principal} n'y apparaît pas encore ("
                                   + (f"{_produits(n_principal)} seulement {a_la(principal)}"
                                      if n_principal else
                                      f"aucun produit proche n'est {a_la(principal)}")
                                   + ") : à valider en dégustation.")})
                rares = sorted((a for a in autres if a != frequente), key=lambda a: (autres[a], a))
                if rares:
                    originale = rares[0]
                    pistes.append({"type": "association_originale",
                                   "aromes": [principal, originale],
                                   "nb_produits": autres[originale], "observee": False,
                                   "explication": (
                                       f"{principal.capitalize()} + {originale} : un goût rare "
                                       f"dans les produits proches ({_produits(autres[originale])})"
                                       f" et jamais associé {a_la(principal)} : une piste "
                                       "originale, à tester.")})

        question = QUESTION_PRODUIT if application is None else None
        return {"division": division, "scores_division": scores_division, "arome": principal,
                "application": application, "mode": mode, "question": question,
                "pistes": pistes[:k], "marche": etude, "etapes": etapes,
                "version_modele": VERSION_V21}
