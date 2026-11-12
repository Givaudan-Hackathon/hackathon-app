"""Mecanismes generaux de la V2.2.3 : vocabulaire d'aromes tire du catalogue, rattachement d'un
type de produit inconnu, detection des marques, vocabulaire des intentions.

Aucune liste d'aromes ecrite a la main ici : le vocabulaire vient du catalogue Flavors (mots qui
suivent « arome », « gout », « saveur » dans les noms et ingredients) et de la liste de reference
Fragrance, filtree par sa presence dans les produits alimentaires.
"""
import hashlib
import json
import re
from difflib import SequenceMatcher
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from src.moteur_v1 import normaliser
from src.moteur_v2 import AROMES_FLAVORS, AROMES_FRAGRANCE, OllamaIndisponible, _racines

# --- mots vides -------------------------------------------------------------------------------
# mots grammaticaux et mots de la demande, qui ne decrivent ni un gout ni un produit
MOTS_VIDES = set("""
a ai as au aux avec avoir c ca ce ces cet cette chez comme comment d dans de des du elle elles en
est et etre fait fais faire il ils j je l la le les leur leurs lui m ma mais me mes moi mon n ne
nos notre nous on ou par pas peu plus pour qu que quel quelle quelles quels qui sa se ses si son
sont sur ta te tes toi ton tous tout toute toutes tres tu un une vos votre vous y est-il est-ce
veux voudrais voudrait voulons voulez cherche cherchons souhaite souhaitons aimerais aimerait
besoin creer cree lancer lance developper developpe sortir sort trouver propose proposer donne
donner donnez dire dis peux pouvez puis faut voila oui non merci bonjour svp plait aide aider
truc chose trucs choses bon bonne bons bonnes meilleur meilleure meilleurs top super genial
produit produits projet projets marque marques gamme gammes idee idees nouveau nouvelle nouveaux
peut-etre peut etre plutot assez vraiment aussi encore deja toujours juste quelque quelques un peu
arome aromes gout gouts saveur saveurs parfum parfums odeur senteur note notes type genre style
bouteille bouteilles litre litres kilo kilos tonne tonnes unite unites pot pots flacon flacons
canette canettes mois semaine semaines annee par environ
doit doivent doit-etre etre sera seront soit suis sommes avez avons ont ai va vont
""".split())
# vocabulaire technique des listes d'ingredients : jamais un arome
TECHNIQUES = set("""
naturel naturels naturelle naturelles artificiel artificiels artificielle artificielles nature
natures natural naturals identique identiques extrait extraits concentre concentres colorant
colorants edulcorant edulcorants acidifiant acidifiants correcteur correcteurs conservateur
conservateurs stabilisant stabilisants emulsifiant emulsifiants antioxydant antioxydants amidon
ferments ferment dont issu issus issue avec unique original originale bio vegetaux vegetal fleur fleurs
cafeine acide acides sucre sucres sel eau lait creme fruit fruits gout saveur arome aromes
""".split())

# --- intentions -------------------------------------------------------------------------------
# question sur le service : prix, delais, livraison, cout d'un echantillon
SERVICE = re.compile(r"\b(?:prix|combien|couts?|coute\w*|tarifs?|payants?|gratuit\w*|delais?|livr\w*"
                     r"|expedi\w*|commander|commande|minimum|devis|factur\w*|paiement|payer|stocks?"
                     r"|disponibilit\w*|frais de port|contact\w*|telephone|horaires?|rendez vous)\b")
COUT = re.compile(r"\b(?:prix|combien|couts?|coute\w*|tarifs?|payants?|gratuit\w*|factur\w*)\b")
# demande de produit trop vague : relance (« je veux un truc bon », « quel est le meilleur arome »)
VAGUE = re.compile(r"\b(?:je (?:veux|voudrais|cherche|souhaite|aimerais)|j ai besoin|besoin d aide"
                   r"|aide(?:z)? moi|aider|mon (?:nouveau )?produit|ma marque|creer|lancer|developper"
                   r"|arome|gout|saveur|parfum|odeur|recette)\b")
QUESTION_MARQUE = re.compile(r"\?")


def mots(texte: str) -> list[str]:
    return re.findall(r"[a-z]+", normaliser(texte))


def _affichages(textes: pd.Series) -> dict[str, str]:
    """Forme accentuee la plus frequente de chaque mot normalise (« peche » -> « pêche »)."""
    compte: dict[str, Counter] = {}
    for texte in textes:
        for mot in re.findall(r"[a-zà-öø-ÿœ]+", texte.lower()):
            compte.setdefault(normaliser(mot), Counter())[mot] += 1
    return {cle: c.most_common(1)[0][0] for cle, c in compte.items()}


# --- vocabulaire d'aromes ---------------------------------------------------------------------
CUE = re.compile(r"\b(?:aromes?|gouts?|saveurs?)(?: naturels?| naturelles?| artificiels?)?"
                 r"(?: (?:de|d|du|des|a la|a l|au|aux))? ((?:fleurs?|noix|fruits?|feuilles?|graines?"
                 r"|zestes?|baies?) (?:de |d )(?:la |l )?[a-z]{3,}|[a-z]{3,})")
MIN_OCCURRENCES = 3  # produits qui citent le terme apres « arome / gout / saveur »
MIN_FRAGRANCE = 5  # produits alimentaires qui citent un arome de la liste Fragrance (mot entier)
SEUIL_ALIAS = 0.80  # bge-m3 : sens proche d un arome connu...
SEUIL_ORTHOGRAPHE = 0.75  # ...et orthographe proche : une variante d ecriture (faute, pluriel)


class VocabulaireAromes:
    """Aromes reconnus : liste de reference Flavors, aromes Fragrance presents dans les produits
    alimentaires, et termes tires du catalogue (« arome X », « gout X », « saveur X »).

    Les termes tires du catalogue qui sont des variantes d'un arome connu (pluriel, faute de
    frappe, synonyme : « vanile », « citrons ») lui sont rattaches par bge-m3 (alias)."""

    def __init__(self, flavors: pd.DataFrame, est_exclu, embed=None, cache: Path | None = None):
        """est_exclu(terme) : vrai pour un mot du vocabulaire du moteur (type, contrainte, marque...)."""
        textes_bruts = flavors["product_name"].fillna("") + " . " + flavors["ingredients_text"].fillna("")
        textes = textes_bruts.map(normaliser)
        self.motifs: list[tuple[str, re.Pattern]] = [(n, re.compile(m)) for n, m in AROMES_FLAVORS.items()]
        connus = {normaliser(n) for n in AROMES_FLAVORS}
        # 1. aromes Fragrance cites (mot entier) par assez de produits alimentaires
        self.depuis_fragrance = []
        for nom, motif in AROMES_FRAGRANCE.items():
            if normaliser(nom) in connus:
                continue
            entier = re.compile(rf"(?:{motif})(?:e|es|s)?\b")  # « musc » ne compte pas « muscat »
            if int(textes.str.contains(entier).sum()) >= MIN_FRAGRANCE:
                self.motifs.append((nom, entier))
                self.depuis_fragrance.append(nom)
                connus.add(normaliser(nom))
        # 2. termes tires du catalogue
        compte = Counter(t for texte in textes for t in set(CUE.findall(texte)))
        candidats = sorted(t for t, n in compte.items() if n >= MIN_OCCURRENCES and self._valide(t, est_exclu))
        candidats = [t for t in candidats if not self.extraire(t)]  # deja reconnus par un motif
        alias = self._alias(candidats, embed, cache)
        affichage = _affichages(textes_bruts)
        self.alias: dict[str, str] = {}
        self.depuis_catalogue = []
        for terme in candidats:
            if terme in alias:
                self.alias[terme] = alias[terme]
                continue
            singulier = terme[:-1] if terme.endswith("s") and terme[:-1] in candidats else None
            if singulier:
                self.alias[terme] = " ".join(affichage.get(m, m) for m in singulier.split())
                continue
            nom = " ".join(affichage.get(m, m) for m in terme.split())
            self.depuis_catalogue.append(nom)
        for terme, cible in self.alias.items():
            self.motifs.append((cible, re.compile(rf"\b{terme}s?\b")))
        for nom in self.depuis_catalogue:
            self.motifs.append((nom, re.compile(rf"\b{normaliser(nom)}s?\b")))
        # terme compose tire du catalogue (« fleur de sureau ») : son dernier mot seul suffit
        for nom in self.depuis_catalogue:
            dernier = normaliser(nom).split()[-1]
            if " de " in f" {normaliser(nom)} " and dernier not in connus and not est_exclu(dernier):
                self.motifs.append((nom, re.compile(rf"\b{dernier}s?\b")))

    @staticmethod
    def _valide(terme: str, est_exclu) -> bool:
        # terme compose (« fleur de sureau », « noix de pecan ») : c'est le dernier mot qui compte
        mot = terme.split()[-1]
        return not ({terme, mot} & (MOTS_VIDES | TECHNIQUES)) and not est_exclu(terme)

    def _alias(self, candidats: list[str], embed, cache: Path | None) -> dict[str, str]:
        """Terme -> arome connu, si bge-m3 les juge equivalents (variantes, fautes, synonymes)."""
        if not candidats or embed is None:
            return {}
        connus = [n for n, _ in self.motifs]
        cle = hashlib.sha256("\n".join(["alias", *connus, "|", *candidats]).encode()).hexdigest()
        if cache and cache.exists():
            donnees = json.loads(cache.read_text(encoding="utf-8"))
            if donnees.get("cle") == cle:
                return donnees["alias"]
        try:
            a = embed([f"arôme {c}" for c in candidats])
            b = embed([f"arôme {n}" for n in connus])
        except OllamaIndisponible:
            return {}
        sims = a @ b.T
        # variante d'ecriture seulement : sens proche (bge-m3) ET orthographe proche
        # (« vaille » -> vanille ; pas « cidre » -> citron)
        alias = {}
        for c, s in zip(candidats, sims):
            cible = connus[int(np.argmax(s))]
            if s.max() >= SEUIL_ALIAS and SequenceMatcher(None, c, normaliser(cible)).ratio() >= SEUIL_ORTHOGRAPHE:
                alias[c] = cible
        if cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps({"cle": cle, "alias": alias}, ensure_ascii=False, indent=1),
                             encoding="utf-8")
        return alias

    def extraire(self, texte: str) -> list[str]:
        """Aromes cites dans un texte, sans doublon ; un motif compose efface ce qu'il a trouve."""
        from src.moteur_v2 import EXCLUSIONS
        texte = EXCLUSIONS.sub(" ", normaliser(texte or ""))
        trouves = []
        for nom, motif in self.motifs:
            if motif.search(texte):
                if nom not in trouves:
                    trouves.append(nom)
                texte = motif.sub(" ", texte)
        return trouves

    def spans(self, texte: str) -> list[tuple[int, int]]:
        texte = normaliser(texte)
        return [m.span() for _, motif in self.motifs for m in motif.finditer(texte)]


# --- rattachement d'un type de produit inconnu ------------------------------------------------
# similarite bge-m3 maximale requise avec un produit du catalogue. Calibrage sur 18 produits
# presents et 20 absents (exemples propres, hors cas de validation) : a 0,60, aucun produit absent
# n'est rattache a tort ; lait de soja et cafe frappe (0,59) ne sont plus rattaches.
SEUIL_TYPE = 0.60
VOTES_TYPE = 8  # sur les 20 produits les plus proches, pour un type precis
ECART_TYPE = 2  # avance requise sur le deuxieme type
VOTES_GENERIQUE = 12  # pour « boisson » ou « dessert »


def rattacher_type(moteur, produit: str, types: list[str]) -> tuple[str | None, float]:
    """Type du catalogue le plus proche du produit cite (« eau gazeuse » -> boisson pétillante),
    par vote des 20 produits du catalogue les plus proches (bge-m3) ; (None, score) si le
    catalogue ne contient rien d'assez proche (« pizza »)."""
    try:
        sims = moteur._vecteurs() @ moteur._embed([produit])[0]
    except (OllamaIndisponible, FileNotFoundError):
        return None, 0.0
    proches = np.argsort(-sims)[:20]
    score = float(sims[proches[0]])
    if score < SEUIL_TYPE:
        return None, score
    df = moteur.flavors
    votes = Counter()
    generiques = Counter()
    for t in types:
        masque = moteur.masque_type(df, t)
        n = int(masque[proches].sum())
        (generiques if t in ("boisson", "dessert") else votes)[t] += n
    classement = votes.most_common(2) + [(None, 0)]
    (premier, n1), (_, n2) = classement[0], classement[1]
    if n1 >= VOTES_TYPE and n1 - n2 >= ECART_TYPE:
        return premier, score
    generique, n = generiques.most_common(1)[0]
    return (generique, score) if n >= VOTES_GENERIQUE else (None, score)


# --- marques citees par le client -------------------------------------------------------------
MIN_PRODUITS_MARQUE = 2  # marque presente sur au moins 2 produits du catalogue
MAX_INGREDIENTS = 5  # un mot frequent dans les ingredients est un mot courant, pas une marque


class Marques:
    """Marques du catalogue citees dans un message, pour ne jamais en tirer un arome.

    Une marque est retenue si elle figure sur assez de produits ; un mot seul est ecarte s'il
    est frequent dans les listes d'ingredients (mot courant) ou s'il fait partie du vocabulaire
    du moteur (arome, type, contrainte...)."""

    def __init__(self, catalogues: list[pd.DataFrame], exclus: set[str]):
        df = pd.concat([c[["brands", "ingredients_text"]] for c in catalogues])
        compte = Counter(" ".join(mots(m)) for b in df["brands"].dropna() for m in b.split(","))
        ingredients = Counter(m for t in df["ingredients_text"].fillna("") for m in set(mots(t)))
        self.formes = sorted(
            (f for f, n in compte.items() if n >= MIN_PRODUITS_MARQUE and len(f) >= 4
             and f not in exclus and f not in MOTS_VIDES and f not in TECHNIQUES
             # « Crème dessert » dans le champ brands : tous ses mots sont du vocabulaire du moteur
             and not all(m in exclus | MOTS_VIDES | TECHNIQUES for m in f.split())
             and not (" " not in f and ingredients[f] >= MAX_INGREDIENTS)),
            key=len, reverse=True)
        self._motif = re.compile(r"\b(?:" + "|".join(re.escape(f) for f in self.formes) + r")\b") \
            if self.formes else None

    def trouvees(self, texte: str) -> list[str]:
        texte = " ".join(mots(texte))
        return sorted(set(self._motif.findall(texte))) if self._motif else []

    def masquer(self, texte: str) -> str:
        """Texte normalise ou les marques sont remplacees par des espaces (meme longueur)."""
        return self._motif.sub(lambda m: " " * len(m.group(0)), texte) if self._motif else texte


# mots de lieu, de moment ou de maniere : jamais un arome (« au bord de l'eau », « a la maison »,
# « une edition d'ete », « facon mojito »)
MOTS_DE_CONTEXTE = set("""
bord bords cote coeur place maison plage mer ocean lac riviere montagne campagne ville jardin
terrasse soleil vacances voyage ete hiver printemps automne saison soir matin midi nuit journee
moment fois debut fin facon maniere mode style base niveau fond centre milieu lieu pays region
monde enfance famille fete noel edition impression ambiance esprit envie idee occasion
""".split())


def mot_de_contexte(mot: str, texte: str) -> bool:
    """Le mot decrit-il un lieu ou un contexte plutot qu'un gout ? Vrai pour un mot de
    MOTS_DE_CONTEXTE, ou un mot suivi de « de » dans le message (« au bord de », « au coeur de »,
    « a la place de »). texte : message normalise."""
    mot = normaliser(mot)
    return mot in MOTS_DE_CONTEXTE or bool(re.search(rf"\b{re.escape(mot)} (?:de|d|du|des)\b", texte))


def mots_inconnus(texte: str, spans: list[tuple[int, int]], exclus: set[str]) -> list[str]:
    """Mots du message qui ne sont ni reconnus (spans), ni vides, ni du vocabulaire du moteur, ni
    des mots de lieu ou de contexte."""
    texte = normaliser(texte)
    masque = list(texte)
    for debut, fin in (span for span in spans if span):
        masque[debut:fin] = " " * (fin - debut)
    return [m for m in re.findall(r"[a-z]+", "".join(masque))
            if len(m) >= 3 and m not in MOTS_VIDES and m not in TECHNIQUES and m not in exclus
            and m not in MOTS_DE_CONTEXTE]


def ancre_dans(terme: str | None, mots_cibles: list[str]) -> bool:
    """Le terme partage-t-il une racine avec l'un des mots cibles ?"""
    return bool(terme) and bool(_racines(terme) & _racines(" ".join(mots_cibles)))


# ce qui suit le nom du produit et n'en fait plus partie : le gout, la cible, une contrainte
FIN_DU_PRODUIT = {"a", "au", "aux", "gout", "gouts", "saveur", "saveurs", "arome", "aromes", "parfum",
                  "pour", "avec", "sans", "et", "de", "du", "des", "bio", "vegan", "je", "qui", "que"}


def groupe_produit(produit: str, message: str, max_mots: int = 3, arrets: set[str] = frozenset()) -> str:
    """Nom du produit tel que le client l'a ecrit, accents compris : « eau » -> « eau aromatisée » ;
    « pizza à la truffe » -> « pizza » (le gout n'est pas le produit)."""
    mots_produit = re.findall(r"[a-z]+", normaliser(produit))
    originaux = re.findall(r"[a-zà-öø-ÿœ]+", message.lower())
    mots_texte = [normaliser(m) for m in originaux]
    if not mots_produit:
        return produit
    debut = next((i for i in range(len(mots_texte)) if mots_texte[i] == mots_produit[0]), None)
    if debut is None:
        groupe = list(zip(mots_produit, mots_produit))
    else:
        groupe = [(mots_texte[debut], originaux[debut])]
        for normal, original in list(zip(mots_texte, originaux))[debut + 1:debut + max_mots]:
            if normal in FIN_DU_PRODUIT or normal in MOTS_VIDES or normal in arrets:
                break  # arrets : mots d'aromes deja reconnus (« smoothie mangue » -> « smoothie »)
            groupe.append((normal, original))
    coupe = next((i for i, (m, _) in enumerate(groupe) if i and m in FIN_DU_PRODUIT), len(groupe))
    return " ".join(original for _, original in groupe[:coupe])
