"""Moteur V2.2 : assistant conversationnel en mode RAG, au-dessus de l'etude de marche V2.1.

A chaque message du client :
1. Intention : llama3.2:3b (JSON) classe le message (nouvelle demande, precision, question sur
   une piste, choix d'une piste, demande d'echantillons, hors sujet). Des garde-fous de code
   corrigent les cas evidents (« echantillon », « je prends la piste 2 », description sans
   question) ; l'intention donnee par le modele reste tracee dans etapes.
2. Projet cumule : produit, arome principal, profil (gourmand, fruite...) et contraintes (peu
   sucre, vegetal, bio, enfants...) sont mis a jour message par message.
3. Etude de marche : celle de la V2.1 (50 produits proches, aromes et associations), calculee sur
   les produits proches qui respectent les contraintes (labels et categories Open Food Facts),
   quand il en reste assez ; sinon la contrainte est notee et le bot le dit.
4. Reponse : le code ecrit un brouillon factuel a partir du contexte recupere (projet cumule,
   etude, pistes, chiffres ; pour une question, les chiffres des aromes cites, y compris ceux des
   etudes precedentes de la conversation). llama3.2:3b le reformule sur un ton naturel, avec un
   exemple guide (few-shot). Verification : aucun chiffre ni rapport « X des Y » ajoute, aucun
   chiffre ni mot obligatoire (aromes des pistes, « prototype »...) oublie, aucune marque ni nom
   de produit du catalogue. En cas d'echec : une seconde tentative, puis le brouillon tel quel.
   Essais ecartes : redaction libre a partir des faits (le modele 3B attribuait l'etude au client,
   recopiait ses consignes, inventait des etapes) ; reformulation avec l'historique en messages
   (il repondait au brouillon comme a un message du client).
5. Parcours : pistes -> choix d'une piste -> recapitulatif du brief -> demande d'echantillons
   (brouillon de demande, rien n'est envoye).

La V2.1 (MoteurV21.pistes) et l'API ne sont pas modifiees.
"""
import json
import re
from collections import Counter
from datetime import date

import pandas as pd

from src.moteur_v1 import CATALOGUE_DEFAUT, detecter_division, normaliser
from src.moteur_v2 import (CATALOGUE_COMPLET, MODELE_LLM, N_MARCHE, PRODUITS, QUESTION_RELANCE,
                           MoteurV21, OllamaIndisponible, a_la, extraire_aromes)

VERSION_V22 = "v2.2-rag-conversation"
N_POOL = 300  # produits proches dans lesquels on cherche ceux qui respectent les contraintes
MIN_FILTRE = 10  # en dessous, la contrainte n'est pas appliquee a l'etude (et le bot le dit)

# --- Contraintes et profil ----------------------------------------------------------------------
# nom -> (motif dans le message du client, motif dans labels/categories/nom du produit, ou None si
# Open Food Facts n'a pas de donnee fiable pour filtrer). Textes normalises, sans accents.
CONTRAINTES = {
    "peu sucré": (r"pas trop sucr|peu sucr|moins sucr|sans sucres? ajout|faible(?:ment)? en sucre"
                  r"|leger en sucre|allege en sucre|reduit en sucre",
                  r"low-sugar|no-added-sugar|reduced-sugar|no-sugar|low-or-no-sugar|sugar-free"
                  r"|without-sugar|unsweetened|sans sucre|zero sucre|0 ?% sucre"),
    "sans sucre": (r"sans sucre(?!s? ajout)|zero sucre|0 ?% (?:de )?sucre",
                   r"no-sugar|sugar-free|without-sugar|unsweetened|sans sucre|zero sucre"),
    "végétal": (r"vegeta|vegan|plant.based|sans lait\b|sans produits? laitiers?",
                r"vegan|100-vegetable|no-milk|plant-based|dairy-substitutes|non-dairy|soy|almond"
                r"|oat-based|coconut|soja|vegetal"),
    "bio": (r"\bbio\b|biologique|organic", r"organic|ab-agriculture-biologique|eu-organic|-bio-"),
    "sans gluten": (r"sans gluten|gluten.free", r"no-gluten|gluten-free"),
    "sans lactose": (r"sans lactose|lactose.free", r"no-lactose|lactose-free|plant-based|vegan"),
    "naturel": (r"\bnaturel|sans additif|sans colorant|sans conservateur|clean label",
                r"natural-flavors|no-artificial-flavors|no-colorings|no-additives|no-preservatives"),
    "pour enfants": (r"enfant|\bkids?\b|bebe|gouter|\bados?\b|adolescent", None),
    "protéiné": (r"protein|proteine", r"proteins|protein"),
}
PROFILS = {
    "gourmand": r"gourmand", "fruité": r"fruit[ei]", "frais": r"\bfrais\b|fraich",
    "intense": r"intense|puissant|\bfort\b", "doux": r"\bdou(?:x|ce)\b|douceur|delicat",
    "acidulé": r"acidul", "léger": r"\bleger|legere\b", "original": r"original|surprenant|audacieux",
    "classique": r"classique|traditionnel|intemporel",
}
# contrainte appliquee a l'etude -> adjectif qui decrit les produits etudies
ADJECTIFS = {"peu sucré": "peu sucrés", "sans sucre": "sans sucre", "végétal": "végétaux",
             "bio": "bio", "sans gluten": "sans gluten", "sans lactose": "sans lactose",
             "naturel": "sans additifs artificiels", "protéiné": "protéinés"}
_CONTRAINTES = {nom: (re.compile(client), re.compile(produit) if produit else None)
                for nom, (client, produit) in CONTRAINTES.items()}
_PROFILS = {nom: re.compile(motif) for nom, motif in PROFILS.items()}


def extraire_contraintes(texte: str) -> list[str]:
    """Contraintes de la liste de reference citees dans un message ("pas trop sucre" -> peu sucre)."""
    texte = normaliser(texte)
    trouvees = [nom for nom, (motif, _) in _CONTRAINTES.items() if motif.search(texte)]
    if "sans sucre" in trouvees and "peu sucré" in trouvees:
        trouvees.remove("peu sucré")
    return trouvees


def extraire_profil(texte: str) -> list[str]:
    texte = normaliser(texte)
    return [nom for nom, motif in _PROFILS.items() if motif.search(texte)]


def _ajouter(liste: list[str], nouveaux: list[str]) -> None:
    liste.extend(n for n in nouveaux if n not in liste)


def _et(elements: list[str]) -> str:
    """'a', 'a et b', 'a, b et c'."""
    return elements[0] if len(elements) == 1 else f"{', '.join(elements[:-1])} et {elements[-1]}"


def _produits(n: int) -> str:
    return f"{n} produit{'s' if n > 1 else ''}"


# --- Intention ----------------------------------------------------------------------------------
INTENTIONS = ["nouvelle_demande", "precision", "question_piste", "choix_piste",
              "demande_echantillons", "hors_sujet"]
SCHEMA_INTENTION = {
    "type": "object",
    "properties": {"intention": {"type": "string", "enum": INTENTIONS},
                   "numero_piste": {"type": "integer"}},
    "required": ["intention", "numero_piste"],
}
SYSTEME_INTENTION = """Tu classes le dernier message d'un client qui discute avec l'assistant \
arômes de Givaudan. Le client crée son propre produit (aliment, boisson, cosmétique) et cherche un \
arôme ou un parfum. Réponds uniquement par un objet JSON {"intention": ..., "numero_piste": ...}.
Intentions possibles :
- "nouvelle_demande" : le client décrit un projet de produit, le premier ou un projet différent \
du projet en cours ;
- "precision" : le client complète ou corrige le projet en cours (goût, type de produit, cible, \
sucre, végétal, bio...) ;
- "question_piste" : le client pose une question sur les pistes proposées ou sur un arôme \
("pourquoi... ?", "c'est quoi... ?", "lequel est le plus... ?") ;
- "choix_piste" : le client choisit une des pistes proposées ;
- "demande_echantillons" : le client veut recevoir des échantillons ou demande comment faire ;
- "hors_sujet" : salutation, remerciement, ou message sans rapport avec un projet d'arôme.
"numero_piste" : le numéro de la piste choisie pour "choix_piste", sinon 0."""

ECHANTILLON = re.compile(r"echantillon")
CHOIX = re.compile(r"\b(?:je (?:prends|choisis|retiens|garde|veux|prefere)|on (?:prend|part sur)"
                   r"|va pour|ok pour|partons sur|je pars sur)\b")
NUMERO = re.compile(r"\bpiste (?:n ?)?([1-9])\b|\b(premiere|1re|deuxieme|seconde|2e|troisieme|3e)"
                    r" piste\b|\bla (premiere|deuxieme|seconde|troisieme)\b")
ORDINAUX = {"premiere": 1, "1re": 1, "deuxieme": 2, "seconde": 2, "2e": 2, "troisieme": 3, "3e": 3}
QUESTION = re.compile(r"\?|^(?:pourquoi|comment|quel|quelle|quels|quelles|qu est|c est quoi"
                      r"|est ce|lequel|laquelle|combien|ou)\b")
POLITESSE = re.compile(r"^(?:bonjour|bonsoir|salut|hello|coucou|merci|super|parfait|top|genial"
                       r"|d accord|ok)\b")


def numero_cite(message: str) -> int | None:
    m = NUMERO.search(normaliser(message))
    if not m:
        return None
    return int(m.group(1)) if m.group(1) else ORDINAUX[m.group(2) or m.group(3)]


# --- Redaction ----------------------------------------------------------------------------------
SYSTEME_REPONSE = """Tu reformules les réponses d'un assistant arômes. Réécris la réponse prévue \
au nom de l'assistant (« je »), en vouvoyant le client, sur un ton chaleureux, avec des phrases \
courtes.
Règles strictes :
- garde chaque phrase de la réponse prévue, dans le même ordre, avec tous ses chiffres ;
- tu peux seulement rendre les phrases plus naturelles et ajouter une courte réaction au début ;
- n'ajoute aucune information, aucun avis, aucune étape ;
- garde la liste numérotée des pistes si la réponse prévue en contient une ;
- n'écris jamais « monsieur » ni « madame » ;
- écris seulement la réponse reformulée."""
# exemples guides (hors catalogue de test : sirop, yaourt) ; sans eux, le modele oubliait des
# chiffres ou commentait la reponse au lieu de la reformuler
EXEMPLES_REFORMULATION = [
    ("je voudrais un sirop",
     "J'ai bien noté votre projet : sirop. Parmi les 50 produits du marché les plus proches, les "
     "arômes les plus courants sont : fraise (12 produits), menthe (9 produits) et citron "
     "(7 produits). Pour votre produit, quel goût recherchez-vous ?",
     "Un sirop, très bonne idée ! Parmi les 50 produits du marché les plus proches de votre projet, "
     "les arômes les plus courants sont la fraise (12 produits), la menthe (9 produits) et le citron "
     "(7 produits). Quel goût aimeriez-vous pour votre sirop ?"),
    ("et le citron ?",
     "L'arôme citron ne fait pas partie de mes pistes. Parmi les 40 produits du marché les plus "
     "proches de votre projet (yaourt), il n'apparaît que dans 3 produits, alors que l'arôme fraise "
     "est dans 15 produits. Laquelle de mes pistes vous tente : 1. fraise, 2. fraise + vanille et "
     "3. fraise + rhubarbe ?",
     "Bonne question ! Le citron ne fait pas partie de mes pistes : parmi les 40 produits du marché "
     "les plus proches de votre yaourt, il n'apparaît que dans 3 produits, alors que la fraise est "
     "dans 15 produits. Laquelle de mes pistes vous tente : 1. fraise, 2. fraise + vanille ou "
     "3. fraise + rhubarbe ?"),
]
# fautes recurrentes de llama3.2:3b, corrigees avant verification
CORRECTIONS = [(re.compile(r"\bune excellente? choix\b", re.I), "un excellent choix"),
               (re.compile(r"\bune (?:tr[eè]s )?bon(?:ne)? choix\b", re.I), "un très bon choix"),
               (re.compile(r"\bun (excellente|bonne|super) id[eé]e\b", re.I), r"une \1 idée")]


def corriger(texte: str) -> str:
    for motif, remplacement in CORRECTIONS:
        texte = motif.sub(lambda m: (lambda r: r[0].upper() + r[1:] if m.group(0)[0].isupper()
                                     else r)(m.expand(remplacement)), texte)
    return texte


GENRE = re.compile(r"\b(?:monsieur|madame|mademoiselle)\b")
# le prototype n'envoie rien : toute annonce d'envoi par l'assistant est refusee
ENVOI = re.compile(r"\b(?:je vais|je vous|nous allons|je peux) (?:vous )?(?:la |le |les )?"
                   r"(?:transmettre|envoyer|expedier|faire parvenir)|\bj ai (?:envoye|transmis)"
                   r"|\b(?:est|a ete) (?:envoyee?|transmise?)\b")

INFOS_INCONNUES = ["prix", "délais de livraison", "quantités d'échantillons", "frais de port",
                   "dosage de l'arôme", "conformité réglementaire"]
# marques du catalogue qui sont aussi des mots courants : ignorees par la verification
MOTS_COURANTS = {"ensemble", "nature", "douceur", "douceurs", "plaisir", "plaisirs", "delice",
                 "delices", "saveurs", "original", "gourmand", "gourmande", "bonne", "simple",
                 "classique", "tradition", "envie", "passion", "authentique", "pure", "vrai"}


def libelle_piste(piste: dict) -> str:
    aromes = piste["aromes"]
    return aromes[0] if len(aromes) == 1 else " + ".join(aromes)


def _mots(texte: str) -> str:
    return f" {' '.join(re.findall(r'[a-z0-9]+', normaliser(texte)))} "


NOMBRE = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)?")
COUPLE = re.compile(r"\b(\d+) (?:des|sur|parmi(?: les)?) (?:les )?(\d+)\b")


def nombres(texte: str) -> set[str]:
    return {n.replace(",", ".") for n in NOMBRE.findall(texte)}


def couples_inventes(texte: str, source: str) -> list[str]:
    """Couples « X des Y » de la reponse absents de la source : chiffres vrais, mais pris dans deux
    faits differents (ex. « 6 des 19 produits » alors que 6 venait d'une autre etude)."""
    source = _mots(source)
    return [f"{x} des {y}" for x, y in COUPLE.findall(_mots(texte))
            if not re.search(rf" {x} [a-z ]{{0,40}}?\b{y}\b", source)]


class NomsDuCommerce:
    """Marques et noms de produits du catalogue, pour verifier qu'aucun n'apparait dans une reponse.

    Comparaison mot a mot sur texte normalise. Un nom qui figure aussi dans la source de la
    reponse ou dans les messages du client (ex. une marque nommee "Dessert") est ignore : c'est un
    mot du projet. Les marques qui sont des mots courants (MOTS_COURANTS) sont ignorees aussi.
    """

    def __init__(self, chemins):
        candidats = set()
        for chemin in chemins:
            df = pd.read_csv(chemin, dtype=str, usecols=["product_name", "brands"])
            candidats |= {n for n in df["product_name"].dropna() if len(n) > 6}
            candidats |= {m.strip() for b in df["brands"].dropna() for m in b.split(",")
                          if len(m.strip()) > 3}
        self.formes = {f for f in (_mots(c) for c in candidats)
                       if f.strip() and f.strip() not in MOTS_COURANTS}

    def trouves(self, texte: str, autorise: str = "") -> list[str]:
        texte, autorise = _mots(texte), _mots(autorise)
        return sorted(f.strip() for f in self.formes if f in texte and f not in autorise)


class MoteurV22(MoteurV21):
    """Etude de marche V2.1 + filtre par contraintes. La conversation est geree par AssistantV22."""

    version = VERSION_V22

    def etude(self, division: str, arome: str | None, produit: str | None, requete: str,
              contraintes: list[str], k: int = 3) -> dict:
        """Pistes V2.1 calculees sur les produits proches qui respectent les contraintes.

        Les contraintes sont appliquees l'une apres l'autre parmi les N_POOL produits les plus
        proches ; une contrainte qui laisserait moins de MIN_FILTRE produits n'est pas appliquee."""
        proches, recherche = self._proches(division, requete, N_POOL)
        textes_filtre = (proches["labels_tags"].fillna("") + " " + proches["categories_tags"].fillna("")
                         + " " + proches["product_name"].fillna("")).map(normaliser)
        retenus = pd.Series(True, index=proches.index)
        bilan = []
        for nom in contraintes:
            motif = _CONTRAINTES[nom][1]
            if motif is None:
                bilan.append({"contrainte": nom, "appliquee": False,
                              "raison": "les données du marché ne le précisent pas"})
                continue
            conformes = retenus & textes_filtre.map(lambda t: bool(motif.search(t)))
            n = int(conformes.sum())
            if n >= MIN_FILTRE:
                retenus = conformes
                bilan.append({"contrainte": nom, "appliquee": True, "produits_conformes": n})
            else:
                bilan.append({"contrainte": nom, "appliquee": False,
                              "raison": f"seulement {_produits(n)} proches la respectent"})
        selection = proches[retenus].head(N_MARCHE)
        textes = selection["product_name"].fillna("") + " | " + selection["ingredients_text"].fillna("")
        marche = [extraire_aromes(t, division) for t in textes]
        etapes = {"comprehension": MODELE_LLM, "recherche": recherche,
                  "filtre_contraintes": [b["contrainte"] for b in bilan if b["appliquee"]]}
        resultat = self._pistes_depuis(division, arome, produit, marche, {}, etapes, "v2.2", k)
        resultat["marche"].setdefault("nb_produits_analyses", len(marche))
        resultat["marche"]["contraintes"] = bilan
        resultat["marche"]["produits_proches_examines"] = len(proches)
        resultat["marche"]["frequence"] = dict(Counter(a for aromes in marche for a in aromes))
        return {**resultat, "version_modele": VERSION_V22}


class AssistantV22:
    """Conversation complete : intention, projet cumule, etude, brouillon, reformulation verifiee."""

    def __init__(self, moteur: MoteurV22 | None = None, noms: NomsDuCommerce | None = None,
                 reformuler: bool = True):
        """reformuler=False : la reponse est le brouillon factuel, sans appel de reformulation
        (plus rapide ; option --rapide du bot, parametre a exposer par l'API)."""
        self.moteur = moteur or MoteurV22()
        self.reformuler = reformuler
        chemins = [CATALOGUE_DEFAUT] + ([CATALOGUE_COMPLET] if self.moteur.catalogue == "complet" else [])
        self.noms = noms or NomsDuCommerce(chemins)
        self.historique: list[dict] = []  # trace de la conversation (le contexte en est tire)
        self.reinitialiser()

    def reinitialiser(self) -> None:
        self.projet = {"division": None, "produit": None, "arome": None, "profil": [],
                       "contraintes": [], "messages": []}
        self.etude: dict | None = None  # derniere sortie de MoteurV22.etude (ou relance)
        self.etudes_precedentes: list[tuple[str, dict]] = []  # (description, frequence des aromes)
        self.piste_choisie: dict | None = None
        self.demande_echantillons: dict | None = None

    def _chat(self, messages: list[dict], format_json: dict | None = None,
              num_predict: int = 300) -> str:
        corps = {"model": MODELE_LLM, "stream": False, "keep_alive": "30m", "messages": messages,
                 "options": {"temperature": 0, "seed": 42, "num_predict": num_predict}}
        if format_json:
            corps["format"] = format_json
        reponse = self.moteur._post("/api/chat", self.moteur.delai_llm, **corps)
        try:
            return reponse["message"]["content"]
        except (KeyError, TypeError) as erreur:
            raise OllamaIndisponible(f"reponse inattendue : {erreur}") from erreur

    @property
    def pistes(self) -> list[dict]:
        return self.etude["pistes"] if self.etude else []

    # --- 1. Intention -------------------------------------------------------------------------

    def _resume_etat(self) -> str:
        if not self.projet["messages"]:
            return "Aucun projet en cours."
        lignes = [f"Projet en cours : {' ; '.join(self.projet['messages'])}."]
        if self.pistes:
            lignes.append("Pistes proposées : " + " ; ".join(
                f"{i}. {libelle_piste(p)}" for i, p in enumerate(self.pistes, 1)) + ".")
        elif self.etude:
            lignes.append("L'assistant vient de poser une question au client.")
        if self.piste_choisie:
            lignes.append(f"Piste choisie : {self.piste_choisie['numero']}.")
        return "\n".join(lignes)

    def detecter_intention(self, message: str) -> tuple[str, int | None, dict]:
        """(intention, numero de piste choisie ou None, trace)."""
        trace = {}
        try:
            sortie = json.loads(self._chat(
                [{"role": "system", "content": SYSTEME_INTENTION},
                 {"role": "user", "content": f"{self._resume_etat()}\nMessage du client : « {message} »"}],
                format_json=SCHEMA_INTENTION, num_predict=40))
            intention = sortie.get("intention") if sortie.get("intention") in INTENTIONS else None
            numero = sortie.get("numero_piste") or None
        except (OllamaIndisponible, TypeError, ValueError, AttributeError):
            intention, numero = None, None
        trace["intention_llm"] = intention or "indisponible"

        # garde-fous : indices explicites dans le message, puis coherence avec l'etat
        texte = normaliser(message)
        mots = " ".join(re.findall(r"[a-z]+|\?", texte))
        cite = numero_cite(message)
        if ECHANTILLON.search(texte):
            intention = "demande_echantillons"
        elif self.pistes and cite and (CHOIX.search(texte) or intention == "choix_piste"):
            intention, numero = "choix_piste", cite
        elif intention is None:  # Ollama indisponible
            intention = ("question_piste" if self.pistes and QUESTION.search(mots) else
                         "precision" if self.projet["messages"] else "nouvelle_demande")
        if intention == "choix_piste" and not (numero and 1 <= numero <= len(self.pistes)):
            intention, numero = ("question_piste" if self.pistes else "precision"), None
        if intention == "question_piste" and not QUESTION.search(mots):
            intention = "precision"  # une description sans question complete le projet
        if intention in ("precision", "question_piste") and not self.projet["messages"]:
            intention = "nouvelle_demande"
        if intention == "nouvelle_demande" and self.projet["messages"]:
            # un message sans nouveau produit complete le projet ; une relance en attente aussi
            if (self.etude is not None and not self.pistes) or not PRODUITS.search(texte):
                intention = "precision"
        if intention in ("nouvelle_demande", "precision") and not self.projet["messages"] \
                and not (PRODUITS.search(texte) or extraire_aromes(texte)):
            # ni produit ni arome reconnu : la comprehension V2 confirme avant d'ouvrir un projet
            try:
                _, arome, produit = self.moteur.comprendre(message)
            except OllamaIndisponible:
                arome, produit = None, None
            if not (arome or produit):
                intention = "hors_sujet"
        trace["intention"] = intention
        return intention, (numero if intention == "choix_piste" else None), trace

    # --- 2 et 3. Projet et etude --------------------------------------------------------------

    def _mettre_a_jour(self, message: str) -> None:
        projet = self.projet
        try:
            division, arome, produit = self.moteur.comprendre(message)
        except OllamaIndisponible:
            division_v1 = detecter_division(message)[0]
            division = None if division_v1 == "indeterminee" else division_v1
            cites = extraire_aromes(message, division or "flavors")
            arome = cites[0] if cites else None
            texte = normaliser(message)
            trouve = PRODUITS.search(texte)
            # meme position dans le message d'origine (accents gardes) si la longueur n'a pas change
            source = message.lower() if len(message) == len(texte) else texte
            produit = source[trouve.start():trouve.end()] if trouve else None
        if division and not projet["division"]:
            projet["division"] = division
        if produit:
            projet["produit"] = produit
        if arome:
            reference = extraire_aromes(arome, projet["division"] or "flavors")
            projet["arome"] = reference[0] if reference else arome.lower()
        _ajouter(projet["profil"], extraire_profil(message))
        _ajouter(projet["contraintes"], extraire_contraintes(message))
        if "sans sucre" in projet["contraintes"] and "peu sucré" in projet["contraintes"]:
            projet["contraintes"].remove("peu sucré")
        projet["messages"].append(message)
        self.piste_choisie, self.demande_echantillons = None, None

    def _requete(self) -> str:
        """Requete de l'etude : projet cumule ("creme dessert gout pistache gourmand peu sucre
        vegetal") plutot que la concatenation des messages."""
        p = self.projet
        morceaux = [p["produit"], f"goût {p['arome']}" if p["arome"] else None, *p["profil"],
                    *p["contraintes"]]
        return " ".join(m for m in morceaux if m) or " ".join(p["messages"])

    def _description_etude(self) -> str:
        marche, etapes = self.etude["marche"], self.etude.get("etapes") or {}
        filtres = [ADJECTIFS[c] for c in etapes.get("filtre_contraintes") or []]
        return (f"les {marche['nb_produits_analyses']} produits du marché les plus proches de votre "
                "projet" + (f" ({self.projet['produit']})" if self.projet["produit"] else "")
                + (f", tous {_et(filtres)}" if filtres else ""))

    def _resume_etude(self) -> str:
        marche, etapes = self.etude["marche"], self.etude.get("etapes") or {}
        filtres = [ADJECTIFS[c] for c in etapes.get("filtre_contraintes") or []]
        return (f"{marche['nb_produits_analyses']} produits proches de « {self.projet['produit'] or 'votre projet'} »"
                + (f", tous {_et(filtres)}" if filtres else ""))

    def _lancer_etude(self) -> None:
        p = self.projet
        if self.etude and self.etude["marche"].get("frequence"):
            self.etudes_precedentes.append((self.etude["resume"], self.etude["marche"]["frequence"]))
        if p["division"] is None:
            division = detecter_division(" ".join(p["messages"]))[0]
            p["division"] = None if division == "indeterminee" else division
        if p["division"] is None or not (p["produit"] or p["arome"]):
            self.etude = {"mode": "relance", "pistes": [], "marche": {}, "etapes": {}}
            return
        self.etude = self.moteur.etude(p["division"], p["arome"], p["produit"], self._requete(),
                                       p["contraintes"])
        self.etude["description"] = self._description_etude()
        self.etude["resume"] = self._resume_etude()

    # --- 4. Brouillon factuel (contexte recupere) ---------------------------------------------

    def _projet_affiche(self) -> dict:
        p = self.projet
        return {"division": {"flavors": "arôme alimentaire", "fragrance": "parfum"}.get(p["division"]),
                "type_de_produit": p["produit"], "arome_principal": p["arome"],
                "profil_recherche": p["profil"], "contraintes": p["contraintes"]}

    def _pistes_affichees(self) -> list[dict]:
        return [{"numero": i, "aromes": libelle_piste(p), "explication": p["explication"]}
                for i, p in enumerate(self.pistes, 1)]

    def _rappel_pistes(self) -> str:
        return _et([f"{i}. {libelle_piste(p)}" for i, p in enumerate(self.pistes, 1)])

    def _resume_projet(self) -> str:
        p = self.projet
        morceaux = [" ".join(m for m in (p["produit"], a_la(p["arome"]) if p["arome"] else None) if m)]
        if p["profil"]:
            morceaux.append(_et(p["profil"]))
        if p["contraintes"]:
            morceaux.append(_et(p["contraintes"]))
        return ", ".join(m for m in morceaux if m)

    def _brouillon_relance(self) -> str:
        p, marche = self.projet, (self.etude or {}).get("marche") or {}
        gout = "quelle odeur recherchez-vous" if p["division"] == "fragrance" else "quel goût recherchez-vous"
        if p["produit"] and not p["arome"]:
            phrases = [f"J'ai bien noté votre projet : {p['produit']}."]
            courants = (marche.get("aromes_frequents") or [])[:3]
            if courants:
                phrases.append(f"Parmi les {marche['nb_produits_analyses']} produits du marché les plus "
                               f"proches, les arômes les plus courants sont : "
                               + _et([f"{a} ({_produits(n)})" for a, n in courants]) + ".")
            phrases.append(f"Pour votre produit, {gout} ?")
            return " ".join(phrases)
        if p["arome"] and not p["produit"]:
            return f"J'ai bien noté le goût {p['arome']}. Pour quel type de produit ?"
        return QUESTION_RELANCE

    def _brouillon_pistes(self) -> str:
        marche = self.etude["marche"]
        lignes = [f"Votre projet : {self._resume_projet()}.",
                  f"J'ai étudié {self.etude['description']}."]
        for b in marche.get("contraintes", []):
            if not b["appliquee"]:
                lignes.append(f"Je n'ai pas pu filtrer l'étude sur « {b['contrainte']} » : "
                              f"{b['raison']}. Je le garde dans votre brief.")
        lignes.append("Voici mes pistes :")
        lignes += [f"{q['numero']}. {q['explication']}" for q in self._pistes_affichees()]
        lignes.append("Laquelle vous tente ? Vous pouvez aussi me poser une question sur une piste.")
        return "\n".join(lignes)

    def _brouillon_question(self, message: str) -> str:
        """Recuperation ciblee : chiffres de chaque arome (ou piste) cite dans la question."""
        p, phrases = self.projet, []
        marche = (self.etude or {}).get("marche") or {}
        frequence = marche.get("frequence") or {}
        numero = numero_cite(message)
        if numero and 1 <= numero <= len(self.pistes):
            q = self._pistes_affichees()[numero - 1]
            phrases.append(f"La piste {numero}, {q['aromes']} : {q['explication']}")
        for arome in extraire_aromes(message, p["division"] or "flavors"):
            numeros = [i for i, q in enumerate(self.pistes, 1) if arome in q["aromes"]]
            if numeros:
                if numero != numeros[0]:
                    q = self._pistes_affichees()[numeros[0] - 1]
                    phrases.append(f"L'arôme {arome} est dans la piste {numeros[0]} : {q['explication']}")
                continue
            phrase = f"L'arôme {arome} ne fait pas partie de mes pistes."
            if marche.get("nb_produits_analyses"):
                k = frequence.get(arome, 0)
                phrase += (f" Dans mon étude actuelle ({self.etude['resume']}), il n'apparaît que "
                           f"dans {_produits(k)}" if k else
                           f" Dans mon étude actuelle ({self.etude['resume']}), aucun ne l'utilise")
                tete = max(frequence, key=frequence.get) if frequence else None
                if tete and tete != arome:
                    phrase += f", alors que l'arôme {tete} est dans {_produits(frequence[tete])}"
                phrase += "."
            phrases.append(phrase)
            avant = [(d, f) for d, f in self.etudes_precedentes if f.get(arome)]
            if avant:  # etude precedente ou cet arome pesait le plus (ex. desserts en general)
                resume, f = max(avant, key=lambda df: df[1][arome] / max(sum(df[1].values()), 1))
                rang = "l'arôme le plus fréquent" if max(f, key=f.get) == arome else "très présent"
                phrases.append(f"Je l'avais cité plus tôt : c'était {rang} dans une étude "
                               f"précédente ({resume}), avec {_produits(f[arome])}.")
        if not phrases:
            phrases.append("Je n'ai pas l'information pour répondre précisément à cette question : "
                           "un conseiller Givaudan pourra vous aider.")
        if self.pistes:
            phrases.append(f"Laquelle de mes pistes vous tente : {self._rappel_pistes()} ?")
        return " ".join(phrases)

    def _brouillon_choix(self) -> str:
        p, c = self.projet, self.piste_choisie
        aromes = self.pistes[c["numero"] - 1]["aromes"]
        brief = [p["produit"] or "type de produit à préciser", f"arômes {_et(aromes)}"
                 if len(aromes) > 1 else f"arôme {aromes[0]}"]
        if p["profil"]:
            brief.append(f"profil {_et(p['profil'])}")
        if p["contraintes"]:
            brief.append(f"contraintes : {_et(p['contraintes'])}")
        return (f"Excellent choix : la piste {c['numero']}, {c['aromes']}. "
                f"Votre brief : {', '.join(brief)}. "
                "Je peux préparer une demande d'échantillons de ces arômes, pour que vous les testiez "
                "dans votre recette. Le souhaitez-vous ?")

    def brouillon(self, intention: str, message: str) -> str:
        """Reponse factuelle ecrite par le code : seule source autorisee pour la reformulation."""
        p = self.projet
        if intention == "hors_sujet":
            if not p["messages"]:
                return ("Bonjour ! Je vous aide à trouver l'arôme de votre futur produit. Quel produit "
                        "voulez-vous créer, et quel goût ou quelle odeur imaginez-vous ?")
            debut = ("Avec plaisir !" if POLITESSE.search(" ".join(re.findall(r"[a-z]+", normaliser(message))))
                     else "Je n'ai pas l'information sur ce point : un conseiller Givaudan pourra "
                          "vous répondre.")
            suite = (f"Revenons à votre projet : laquelle de mes pistes vous tente, "
                     f"{self._rappel_pistes()} ?" if self.pistes and not self.piste_choisie else
                     "Souhaitez-vous une demande d'échantillons pour la piste choisie ?"
                     if self.piste_choisie and not self.demande_echantillons else
                     "Avez-vous une autre question sur votre projet ?" if self.pistes else
                     self._brouillon_relance())
            return f"{debut} {suite}"
        if intention in ("nouvelle_demande", "precision"):
            return self._brouillon_pistes() if self.pistes else self._brouillon_relance()
        if intention == "question_piste":
            return self._brouillon_question(message)
        if intention == "choix_piste":
            return self._brouillon_choix()
        if self.demande_echantillons:
            return ("Voici le récapitulatif de votre demande d'échantillons, juste en dessous. Dans ce "
                    "prototype, la demande n'est pas envoyée : transmettez ce récapitulatif à un "
                    "conseiller Givaudan. Je ne connais ni les délais, ni les quantités, ni le prix : "
                    "le conseiller vous les donnera.")
        if self.pistes:
            return ("Pour préparer une demande d'échantillons, choisissez d'abord une de mes pistes : "
                    f"{self._rappel_pistes()}.")
        return ("Pour vous proposer des échantillons, décrivez-moi d'abord votre projet : quel "
                "produit, et quel goût ?")

    def obligatoires(self, intention: str, message: str) -> list[str]:
        """Mots que la reformulation doit garder (en plus de tous les chiffres du brouillon)."""
        if intention in ("nouvelle_demande", "precision") and self.pistes:
            return sorted({a for q in self.pistes for a in q["aromes"]})
        if intention == "question_piste":
            return extraire_aromes(message, self.projet["division"] or "flavors")
        if intention == "choix_piste":
            return [*self.pistes[self.piste_choisie["numero"] - 1]["aromes"], "échantillons"]
        if intention == "demande_echantillons" and self.demande_echantillons:
            return ["récapitulatif", "prototype", "conseiller"]
        return []

    def contexte(self, intention: str, message: str) -> dict:
        """Contexte factuel du tour : ce que le code sait, et le brouillon qui en est tire."""
        ctx = {"etape": intention, "projet": self._projet_affiche() if self.projet["messages"] else None,
               "pistes": self._pistes_affichees() or None, "piste_choisie": self.piste_choisie,
               "etude": ({"description": self.etude.get("description"),
                          "aromes_frequents": self.etude["marche"].get("aromes_frequents"),
                          "contraintes": self.etude["marche"].get("contraintes")}
                         if self.etude and self.etude["marche"] else None),
               "demande_echantillons": self.demande_echantillons
               if intention == "demande_echantillons" else None,
               "informations_inconnues": INFOS_INCONNUES,
               "brouillon": self.brouillon(intention, message),
               "mots_obligatoires": self.obligatoires(intention, message) or None}
        return {cle: valeur for cle, valeur in ctx.items() if valeur is not None}

    # --- 4 bis. Reformulation par le modele, verifiee -----------------------------------------

    def verifier(self, texte: str, source: str, obligatoires: list[str] = ()) -> dict:
        """Ajouts (chiffres, rapports « X des Y », marques, noms de produits, monsieur/madame) et
        oublis (chiffres et mots obligatoires du brouillon)."""
        autorise = source + " " + " ".join(self.projet["messages"])
        mots = _mots(texte)
        return {"chiffres_inventes": sorted(nombres(texte) - nombres(source)),
                "couples_inventes": couples_inventes(texte, source),
                "noms_du_commerce": self.noms.trouves(texte, autorise),
                "chiffres_oublies": sorted(nombres(source) - nombres(texte)),
                "mots_oublies": [m for m in obligatoires if _mots(m) not in mots],
                "genre_suppose": GENRE.findall(normaliser(texte)),
                "envoi_annonce": [m.group(0) for m in ENVOI.finditer(" ".join(
                    re.findall(r"[a-z]+", normaliser(texte))))]}

    def rediger(self, message: str, brouillon: str, obligatoires: list[str] = ()) -> tuple[str, dict]:
        """Reformulation du brouillon par llama3.2:3b, verifiee ; sinon le brouillon tel quel."""
        messages = [{"role": "system", "content": SYSTEME_REPONSE}]
        for client, prevu, reformule in EXEMPLES_REFORMULATION:
            messages += [{"role": "user", "content": f"Message du client : « {client} »\n\n"
                                                     f"Réponse prévue par l'assistant :\n{prevu}"},
                         {"role": "assistant", "content": reformule}]
        messages.append({"role": "user", "content": f"Message du client : « {message} »\n\n"
                                                    f"Réponse prévue par l'assistant :\n{brouillon}"})
        verification = {"tentatives": 0, "rejets": []}
        for _ in range(2):
            verification["tentatives"] += 1
            try:
                texte = corriger(self._chat(messages, num_predict=450).strip().strip("«»\"").strip())
            except OllamaIndisponible:
                verification["source"] = "brouillon (Ollama indisponible)"
                return brouillon, verification
            erreurs = self.verifier(texte, brouillon, obligatoires)
            if not any(erreurs.values()):
                verification["source"] = MODELE_LLM
                return texte, verification
            verification["rejets"].append({"texte": texte, **erreurs})
            problemes = [f"{nom} : {', '.join(valeurs)}" for nom, valeurs in (
                ("chiffres ajoutés", erreurs["chiffres_inventes"]),
                ("rapports de chiffres faux", erreurs["couples_inventes"]),
                ("noms du commerce", erreurs["noms_du_commerce"]),
                ("chiffres oubliés", erreurs["chiffres_oublies"]),
                ("mots oubliés", erreurs["mots_oublies"]),
                ("mots interdits", erreurs["genre_suppose"]),
                ("envoi annoncé alors que rien n'est envoyé", erreurs["envoi_annonce"])) if valeurs]
            messages += [{"role": "assistant", "content": texte},
                         {"role": "user", "content": "Ta reformulation ne respecte pas la réponse "
                                                     "prévue (" + " ; ".join(problemes)
                                                     + "). Recommence en gardant chaque phrase et "
                                                       "chaque chiffre de la réponse prévue."}]
        verification["source"] = "brouillon (vérification échouée)"
        return brouillon, verification

    # --- 5. Parcours --------------------------------------------------------------------------

    def _choisir(self, numero: int) -> None:
        piste = self.pistes[numero - 1]
        self.piste_choisie = {"numero": numero, "aromes": libelle_piste(piste)}
        self.demande_echantillons = None

    def _preparer_echantillons(self) -> None:
        p, c = self.projet, self.piste_choisie
        self.demande_echantillons = {
            "statut": "brouillon, non envoyé (prototype)",
            "date": date.today().isoformat(),
            "division": self._projet_affiche()["division"],
            "type_de_produit": p["produit"],
            "piste": c["numero"],
            "aromes": self.pistes[c["numero"] - 1]["aromes"],
            "profil": p["profil"],
            "contraintes": p["contraintes"],
            "brief_du_client": " / ".join(p["messages"]),
        }

    def repondre(self, message: str, reformuler: bool | None = None) -> dict:
        """reformuler : None = reglage de l'assistant ; False = brouillon direct (mode rapide)."""
        reformuler = self.reformuler if reformuler is None else reformuler
        intention, numero, etapes = self.detecter_intention(message)
        if intention == "nouvelle_demande":
            self.reinitialiser()
        if intention in ("nouvelle_demande", "precision"):
            self._mettre_a_jour(message)
            self._lancer_etude()
        elif intention == "choix_piste":
            self._choisir(numero)
        elif intention == "demande_echantillons" and self.piste_choisie:
            self._preparer_echantillons()
        contexte = self.contexte(intention, message)
        if reformuler:
            texte, verification = self.rediger(message, contexte["brouillon"],
                                               contexte.get("mots_obligatoires") or [])
        else:
            texte, verification = contexte["brouillon"], {"tentatives": 0, "rejets": [],
                                                          "source": "brouillon (mode rapide)"}
        self.historique += [{"role": "user", "content": message},
                            {"role": "assistant", "content": texte}]
        return {"intention": intention, "texte": texte, "projet": self._projet_affiche(),
                "pistes": self._pistes_affichees(), "piste_choisie": self.piste_choisie,
                "demande_echantillons": contexte.get("demande_echantillons"),
                "contexte": contexte, "verification": verification,
                "etapes": {**etapes, **((self.etude or {}).get("etapes") or {})},
                "version_modele": VERSION_V22}
