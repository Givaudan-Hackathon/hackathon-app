"""Moteur V2.2 : assistant conversationnel en mode RAG, au-dessus de l'etude de marche V2.1.

A chaque message du client :
1. Analyse : des regles suffisent pour la plupart des messages (« bonjour », « piste 2 »,
   « echantillons », type de produit, aromes de la liste de reference, contraintes, questions).
   Sinon, un seul appel a llama3.2:3b (JSON) donne a la fois l'intention et l'extraction
   (produit, division, aromes), avec les garde-fous anti-invention de la V2.
2. Projet cumule : type de produit (soda, sirop, glace...), arome principal, profil et
   contraintes (peu sucre, vegetal, bio...), mis a jour message par message.
3. Etude de marche : on garde d'abord les produits du type demande, puis ceux qui respectent les
   contraintes (labels et categories Open Food Facts), classes par similarite bge-m3 ; les 50
   premiers donnent les aromes et associations (V2.1). Une contrainte trop restrictive n'est pas
   appliquee et le bot le dit : l'etude ne quitte jamais le type de produit.
4. References : chaque piste est reliee aux references les plus proches de la banque de demo
   (codes DEMO fictifs), filtrees par application et labels demandes ; « peu sucre » ajoute la
   solution Sweetness. Sans reference proche, le bot propose une creation sur mesure.
5. Reponse : le code ecrit un brouillon factuel a partir du contexte recupere. Par defaut il est
   affiche tel quel (mode rapide) ; avec reformuler=True, llama3.2:3b le reformule et la
   reformulation est verifiee (chiffres, rapports « X des Y », aromes, codes, marques, annonce
   d'envoi), sinon le brouillon est garde.
6. Parcours : pistes -> choix -> recapitulatif du brief (codes DEMO) -> demande d'echantillons
   (brouillon de demande, rien n'est envoye).

La V2.1 (MoteurV21.pistes) et l'API ne sont pas modifiees.
"""
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from src.moteur_v1 import CATALOGUE_DEFAUT, detecter_division, normaliser
from src.moteur_v2 import (CATALOGUE_COMPLET, CACHE_DEFAUT, MODELE_EMBEDDING, MODELE_LLM,
                           N_MARCHE, OLLAMA_DEFAUT, PRODUITS, RACINE, SENSORIEL, MoteurV21,
                           OllamaIndisponible, a_la, ancre, extraire_aromes)

VERSION_V22 = "v2.2.3-mecanismes"
BANQUE_DEFAUT = RACINE / "data" / "processed" / "banque_references_demo.csv"
MIN_FILTRE = 10  # produits conformes requis pour appliquer une contrainte a l'etude
KEEP_ALIVE = "2h"  # modeles gardes en memoire entre deux messages
SEUIL_REFERENCE = 0.65  # score bge-m3 suffisant sans que la reference cite l'arome ; mesure :
# 0,58 a 0,72 quand la reference cite l'arome, 0,55 au plus sinon (durian : 0,50)
ATTRIBUTION = "Étude de marché réalisée sur des données d'Open Food Facts (ODbL)"

# --- Types de produit ---------------------------------------------------------------------------
# nom -> (motif client, motif produit sur categories + nom normalises ou None, categories du
# catalogue, application de la banque, type generique parent). Ordre : du plus precis au plus
# general (« the glace » avant « glace », « creme dessert » avant « dessert »).
TYPES = {
    "kombucha": (r"\bkombuchas?\b|kefirs? de fruits?|boissons? fermentees?",
                 r"kombucha|fermented-tea|fermented-drink|kefir|fermentee", {"boissons_aromatisees"},
                 "boissons", "boisson"),
    "boisson pétillante": (r"petillant|gazeu|\bsodas?\b|limonade|\btonic|\bbulles?\b",
                           r"carbonated|sodas|lemonade|sparkling|colas|tonic|petillant|gazeu|limonade",
                           {"boissons_aromatisees"}, "boissons", "boisson"),
    "thé glacé": (r"\bthes? glaces?\b|ice ?tea|iced tea|the froid",
                  r"iced-tea|ice-tea|the glace|ice tea|iced tea", {"boissons_aromatisees"},
                  "boissons", "boisson"),
    "sirop": (r"\bsirops?\b", r"syrup|sirop", {"boissons_aromatisees"}, "boissons", "boisson"),
    "yaourt à boire": (r"yaourts? a boire|yogourts? a boire|kefir|lait fermente",
                       r"yogurt-drink|drinkable-yog|a boire|fermented-milk-drink|kefir",
                       {"boissons_lactees", "boissons_proteinees"}, "laitier", "boisson"),
    # le nom du produit est exige : « riche en proteines » seul est une contrainte, pas un type
    "boisson protéinée": (r"boissons? (?:hyper)?proteine\w*|boissons? (?:riches?|enrichies?) en proteines"
                          r"|\bshakes?\b|proteines? en poudre|\bwhey\b", None,
                          {"boissons_proteinees"}, "boissons", "boisson"),
    "boisson lactée": (r"boissons? lactees?|laits? aromatises?|milk ?shake|boissons? au lait"
                       r"|lait (?:au|a la) ", None, {"boissons_lactees"}, "laitier", "boisson"),
    "boisson végétale": (r"boissons? vegetales?|laits? vegeta|lait d (?:amande|avoine|riz)"
                         r"|boissons? (?:au soja|a l avoine|d amande|de riz)", None,
                         {"boissons_vegetales"}, "boissons", "boisson"),
    "crème dessert": (r"cremes? desserts?|\bflans?\b|puddings?|creme (?:a la |au )?(?:vanille|chocolat"
                      r"|caramel|pistache)",
                      r"dessert-cream|creamy-pudding|cremes-dessert|pudding|flans|creme dessert"
                      r"|creme vanille|creme chocolat|creme caramel", {"desserts_aromatises"},
                      "laitier", "dessert"),
    "glace": (r"\bglaces?\b|creme glacee|sorbets?|ice cream|esquimau",
              r"ice-cream|sorbet|frozen-dessert|\bglaces?\b|creme glacee", {"desserts_aromatises"},
              "sucré", "dessert"),
    "yaourt": (r"\byaourts?\b|yogourt|fromage blanc|\bskyr\b", r"yogurt|yaourt|fromage blanc|skyr",
               {"desserts_aromatises"}, "laitier", "dessert"),
    "dessert": (r"\bdesserts?\b|patisserie|gourmandise", None, {"desserts_aromatises"}, "sucré", None),
    "boisson": (r"\bboissons?\b|\bdrinks?\b", None, {"boissons_aromatisees"}, "boissons", None),
}
SOUS_TYPES = {"boisson": "plutôt pétillante, thé glacé, sirop, lactée ou végétale",
              "dessert": "plutôt crème dessert, yaourt ou glace"}
_TYPES = {nom: (re.compile(client), re.compile(produit) if produit else None, cats, app, parent)
          for nom, (client, produit, cats, app, parent) in TYPES.items()}


def type_cite(texte: str) -> str | None:
    """Type de produit le plus precis cite dans un message ("petillante" -> boisson petillante).

    Un mot qui sert de contrainte ne donne jamais un type : dans « un yaourt riche en
    proteines », « proteines » est la contrainte « proteine », le type reste « yaourt »."""
    texte = " ".join(re.findall(r"[a-z]+", normaliser(texte)))
    contraintes = [m.span() for motif, _ in _CONTRAINTES.values() for m in motif.finditer(texte)]
    for nom, (motif, *_) in _TYPES.items():
        for m in motif.finditer(texte):
            if not any(debut <= m.start() and m.end() <= fin for debut, fin in contraintes):
                return nom
    return None


def generique(type_produit: str | None) -> str | None:
    return _TYPES[type_produit][4] or type_produit if type_produit in _TYPES else None


# --- Contraintes et profil ----------------------------------------------------------------------
# nom -> (motif client, motif produit sur labels + categories + nom ou None si Open Food Facts
# n'a pas de donnee fiable, label requis dans la banque de references ou None)
CONTRAINTES = {
    "peu sucré": (r"pas trop sucr|peu sucr|moins sucr|moins de sucre|sans sucres? ajout"
                  r"|faible(?:ment)? en sucre|leger en sucre|allege en sucre|reduit en sucre",
                  r"low-sugar|no-added-sugar|reduced-sugar|no-sugar|low-or-no-sugar|sugar-free"
                  r"|without-sugar|unsweetened|sans sucre|zero sucre|0 ?% sucre", None),
    "sans sucre": (r"sans sucre(?!s? ajout)|zero sucre|0 ?% (?:de )?sucre",
                   r"no-sugar|sugar-free|without-sugar|unsweetened|sans sucre|zero sucre", None),
    "végétal": (r"vegeta|vegan|plant.based|sans lait\b|sans produits? laitiers?",
                r"vegan|100-vegetable|no-milk|plant-based|dairy-substitutes|non-dairy|soy|almond"
                r"|oat-based|coconut|soja|vegetal", "vegan"),
    "bio": (r"\bbio\b|biologique|organic", r"organic|ab-agriculture-biologique|eu-organic|-bio-", "bio"),
    "sans gluten": (r"sans gluten|gluten.free", r"no-gluten|gluten-free", None),
    "sans lactose": (r"sans lactose|lactose.free", r"no-lactose|lactose-free|plant-based|vegan", None),
    "naturel": (r"\bnaturel|sans additif|sans colorant|sans conservateur|clean label",
                r"natural-flavors|no-artificial-flavors|no-colorings|no-additives|no-preservatives",
                "naturel"),
    "halal": (r"\bhalal\b", r"halal", "halal"),
    "casher": (r"casher|kasher|kosher", r"kosher|casher", "casher"),
    "sans allergène": (r"sans allergene|allergen.free", None, "sans allergène"),
    "moins gras": (r"moins gras|moins de (?:matieres? )?gras|allege en gras|peu gras|onctu",
                   r"low-fat|no-fat|reduced-fat|allege", None),
    "moins salé": (r"moins sal|moins de sel|peu sal|reduit en sel", r"low-salt|reduced-salt", None),
    "pour enfants": (r"enfant|\bkids?\b|bebe|gouter|\bados?\b|adolescent", None, None),
    "protéiné": (r"protein|proteine", r"proteins|protein", None),
}
# contrainte -> solution TasteSolutions de la banque
SOLUTIONS = {"peu sucré": "Sweetness", "sans sucre": "Sweetness", "moins gras": "Mouthfeel",
             "moins salé": "Saltiness"}
PROFILS = {
    "gourmand": r"gourmand", "fruité": r"fruit[ei]", "frais": r"\bfrais\b|fraich",
    "intense": r"intense|puissant|\bfort\b", "doux": r"\bdou(?:x|ce)\b|douceur|delicat",
    "acidulé": r"acidul", "léger": r"\bleger|legere\b", "original": r"original|surprenant|audacieux",
    "classique": r"classique|traditionnel|intemporel", "exotique": r"exoti",
}
# contrainte appliquee a l'etude -> adjectif qui decrit les produits etudies
ADJECTIFS = {"peu sucré": "peu sucrés", "sans sucre": "sans sucre", "végétal": "végétaux",
             "bio": "bio", "sans gluten": "sans gluten", "sans lactose": "sans lactose",
             "naturel": "sans additifs artificiels", "protéiné": "protéinés", "halal": "halal",
             "casher": "casher", "moins gras": "allégés en gras", "moins salé": "moins salés"}
PLURIELS = {"boisson pétillante": "boissons pétillantes", "thé glacé": "thés glacés",
            "sirop": "sirops", "yaourt à boire": "yaourts à boire",
            "boisson protéinée": "boissons protéinées", "boisson lactée": "boissons lactées",
            "boisson végétale": "boissons végétales", "crème dessert": "crèmes dessert",
            "glace": "glaces", "yaourt": "yaourts", "dessert": "desserts", "boisson": "boissons",
            "kombucha": "kombuchas"}
ADJECTIFS_FEMININS = {"peu sucré": "peu sucrées", "végétal": "végétales", "naturel": "sans additifs "
                      "artificiels", "protéiné": "protéinées", "moins gras": "allégées en gras",
                      "moins salé": "moins salées"}
TYPES_FEMININS = {"boisson pétillante", "boisson protéinée", "boisson lactée", "boisson végétale",
                  "crème dessert", "glace", "boisson"}  # masculins : yaourt(s), sirop, thé glacé, dessert
FEMININ_SINGULIER = {"peu sucré": "peu sucrée", "végétal": "végétale", "protéiné": "protéinée",
                     "moins salé": "moins salée", "gourmand": "gourmande", "fruité": "fruitée",
                     "frais": "fraîche", "doux": "douce", "acidulé": "acidulée", "léger": "légère",
                     "original": "originale", "exotique": "exotique"}
_CONTRAINTES = {nom: (re.compile(client), re.compile(produit) if produit else None)
                for nom, (client, produit, _) in CONTRAINTES.items()}
_PROFILS = {nom: re.compile(motif) for nom, motif in PROFILS.items()}


def extraire_contraintes(texte: str) -> list[str]:
    """Contraintes de la liste de reference citees dans un message ("pas trop sucre" -> peu sucre)."""
    texte = normaliser(texte)
    trouvees = [nom for nom, (motif, _) in _CONTRAINTES.items() if motif.search(texte)]
    if "sans sucre" in trouvees and "peu sucré" in trouvees:
        trouvees.remove("peu sucré")
    return trouvees


# contraintes qu'un client peut retirer (« finalement pas bio ») : nom -> mot dans le message
RETIRABLES = {"bio": r"bio(?:logique)?", "végétal": r"vegan|vegetal\w*|vegetaux", "naturel": r"naturel\w*",
              "halal": r"halal", "casher": r"casher|kasher|kosher", "protéiné": r"proteine\w*",
              "pour enfants": r"(?:pour )?(?:les )?enfants?", "sans gluten": r"(?:sans )?gluten",
              "sans lactose": r"(?:sans )?lactose",
              "peu sucré": r"peu sucr\w*|reduire le sucre|moins de sucre"}
_RETRAITS = {nom: re.compile(
    rf"\b(?:(?:finalement|en fait|au final) )?(?:pas|plus) (?:besoin (?:de |d |du )|forcement "
    rf"|obligatoirement |necessairement )?(?:de |du |le |la |l |en )?(?:{mot})\b"
    rf"|\bsans (?:le |la |les |l )(?:{mot})\b"
    rf"|\b(?:oublie[rz]?|retire[rz]?|enleve[rz]?|supprime[rz]?) (?:le |la |les |l )?(?:{mot})\b")
    for nom, mot in RETIRABLES.items()}


def extraire_retraits(texte: str) -> tuple[list[str], str]:
    """(contraintes retirees, texte sans les passages de retrait) : « finalement pas bio »."""
    texte = " ".join(re.findall(r"[a-z]+", normaliser(texte)))
    retirees = []
    for nom, motif in _RETRAITS.items():
        if motif.search(texte):
            retirees.append(nom)
            texte = motif.sub(" ", texte)
    return retirees, texte


VOLUME = re.compile(r"(\d{1,3}(?:[ .\u202f\u00a0]\d{3})+|\d+(?:[.,]\d+)?)\s*(?:k\s*)?"
                    r"(bouteilles?|canettes?|litres?|hl|kg|tonnes?|unites?|pots?|flacons?|cl|ml"
                    r"|exemplaires?|pieces?|briques?|cartons?|palettes?)\b")


def extraire_volume(texte: str) -> str | None:
    """Volume cite par le client (« 5 000 bouteilles »), tel qu'il l'a ecrit ; aucun calcul."""
    normalise = normaliser(texte)
    m = VOLUME.search(normalise)
    if not m:
        return None
    source = texte if len(texte) == len(normalise) else normalise
    return " ".join(source[m.start():m.end()].split())


# changement explicite de projet : on repart d'un projet vide
NOUVEAU_PROJET = re.compile(
    r"\b(?:une? autres? (?!pistes?|associations?|idees?|questions?|references?|choix|aromes?|gouts?"
    r"|contraintes?|versions?|fois|chose)\w+|nouveau projet|nouvelle demande|autre projet"
    r"|nouveau produit|nouvelle boisson|nouveau dessert|maintenant je (?:voudrais|veux|souhaite"
    r"|cherche|voudrai|aimerais)|on (?:change|passe) (?:de projet|a autre chose)|je change de projet)\b")


def extraire_profil(texte: str) -> list[str]:
    texte = normaliser(texte)
    return [nom for nom, motif in _PROFILS.items() if motif.search(texte)]


def _ajouter(liste: list[str], nouveaux: list[str]) -> None:
    liste.extend(n for n in nouveaux if n not in liste)


def _et(elements: list[str], mot: str = "et") -> str:
    """'a', 'a et b', 'a, b et c'."""
    elements = list(elements)
    return elements[0] if len(elements) == 1 else f"{', '.join(elements[:-1])} {mot} {elements[-1]}"


def _produits(n: int) -> str:
    return f"{n} produit{'s' if n > 1 else ''}"


# --- Analyse du message (intention + extraction) -------------------------------------------------
INTENTIONS = ["nouvelle_demande", "precision", "question", "question_piste", "choix_piste",
              "demande_echantillons", "hors_sujet"]
ETAPES = ["relance", "pistes", "recapitulatif", "echantillons"]
SCHEMA_ANALYSE = {
    "type": "object",
    "properties": {"intention": {"type": "string", "enum": INTENTIONS},
                   "numero_piste": {"type": "integer"},
                   "application": {"type": "string"},
                   "division": {"type": "string", "enum": ["flavors", "fragrance", "aucune"]},
                   "aromes": {"type": "array", "items": {"type": "string"}}},
    "required": ["intention", "numero_piste", "application", "division", "aromes"],
}
SYSTEME_ANALYSE = """Tu analyses le dernier message d'un client qui discute avec l'assistant \
arômes de Givaudan (arômes alimentaires : division "flavors" ; parfums pour l'hygiène et la \
cosmétique : division "fragrance"). Le client crée son propre produit. Réponds uniquement par un \
objet JSON avec les clés :
- "intention" : "nouvelle_demande" (il décrit un projet, le premier ou un projet différent), \
"precision" (il complète ou corrige le projet en cours), "question" (question générale, sans \
rapport avec les pistes : prix, délais, fonctionnement…), "question_piste" (il pose une question \
sur les pistes ou un arôme), "choix_piste" (il choisit une piste), "demande_echantillons" (il veut \
des échantillons), "hors_sujet" (salutation, remerciement, message sans rapport) ;
- "numero_piste" : le numéro de la piste choisie pour "choix_piste", sinon 0 ;
- "application" : le type de produit final cité dans le message, "" s'il n'en cite aucun ;
- "division" : "flavors" si le produit se mange ou se boit, "fragrance" s'il se sent ou \
s'applique sur le corps ("goût"/"saveur" -> flavors, "odeur"/"sent" -> fragrance), "aucune" si \
le message ne parle ni d'un produit, ni d'un goût, ni d'une odeur ;
- "aromes" : les arômes ou notes recherchés, en français, le principal en premier ; liste vide si \
le message n'en parle pas.
N'invente jamais un produit ou un arôme que le message ne suggère pas."""

ECHANTILLON = re.compile(r"echantillon")
CHOIX = re.compile(r"\b(?:je (?:prends|choisis|retiens|garde|veux|prefere)|on (?:prend|part sur)"
                   r"|va pour|ok pour|partons sur|je pars sur)\b")
NUMERO = re.compile(r"\bpiste (?:n ?)?([1-9])\b|\b(premiere|1re|deuxieme|seconde|2e|troisieme|3e)"
                    r" piste\b|\bla (premiere|deuxieme|seconde|troisieme)\b")
ORDINAUX = {"premiere": 1, "1re": 1, "deuxieme": 2, "seconde": 2, "2e": 2, "troisieme": 3, "3e": 3}
QUESTION = re.compile(r"\?|^(?:pourquoi|comment|quel|quelle|quels|quelles|qu est|c est quoi"
                      r"|est ce|lequel|laquelle|combien|ou)\b")
POLITESSE = re.compile(r"^(?:bonjour|bonsoir|salut|hello|coucou|merci(?: beaucoup)?|super|parfait"
                       r"|top|genial|d accord|ok|au revoir)(?: (?:a vous|madame|monsieur|tout le monde))?$")
APRES_GOUT = re.compile(r"\b(?:aromes?|gouts?|saveurs?)(?: (?:de|d|du|a la|a l|au|aux))? ([a-z]{3,})")
MOTS_VIDES = {"pour", "qui", "que", "plus", "moins", "tres", "assez", "bien", "dans", "avec", "sans",
              "naturel", "naturelle", "fruite", "frais", "sucre", "unique", "original", "enfance"}
ASSOCIATION = re.compile(r"association|melange|combinaison|cette piste|ces pistes|ce choix|pourquoi")


def numero_cite(message: str) -> int | None:
    m = NUMERO.search(normaliser(message))
    if not m:
        return None
    return int(m.group(1)) if m.group(1) else ORDINAUX[m.group(2) or m.group(3)]


def _mots_normalises(texte: str) -> str:
    return " ".join(re.findall(r"[a-z]+|\?", normaliser(texte)))


# --- Redaction et verification ------------------------------------------------------------------
SYSTEME_REPONSE = """Tu reformules les réponses d'un assistant arômes. Réécris la réponse prévue \
au nom de l'assistant (« je »), en vouvoyant le client, sur un ton chaleureux, avec des phrases \
courtes.
Règles strictes :
- garde chaque phrase de la réponse prévue, dans le même ordre, avec tous ses chiffres et tous \
ses codes de référence (DEMO-...) ;
- tu peux seulement rendre les phrases plus naturelles et ajouter une courte réaction au début ;
- n'ajoute aucune information, aucun arôme, aucun avis, aucune étape ;
- garde la liste numérotée des pistes si la réponse prévue en contient une ;
- n'écris jamais « monsieur » ni « madame » ;
- écris seulement la réponse reformulée."""
# exemple guide (hors parcours de test) ; sans lui, le modele oubliait des chiffres
EXEMPLES_REFORMULATION = [
    ("je voudrais un sirop",
     "J'ai bien noté votre projet : sirop. Parmi les 50 sirops du marché les plus proches, les "
     "arômes les plus courants sont : fraise (12 produits), menthe (9 produits) et citron "
     "(7 produits). Quel goût recherchez-vous ?",
     "Un sirop, très bonne idée ! Parmi les 50 sirops du marché les plus proches de votre projet, "
     "les arômes les plus courants sont la fraise (12 produits), la menthe (9 produits) et le citron "
     "(7 produits). Quel goût aimeriez-vous ?"),
]
INFOS_INCONNUES = ["prix", "délais de livraison", "quantités d'échantillons", "frais de port",
                   "dosage de l'arôme", "conformité réglementaire"]
# marques du catalogue qui sont aussi des mots courants : ignorees par la verification
MOTS_COURANTS = {"ensemble", "nature", "douceur", "douceurs", "plaisir", "plaisirs", "delice",
                 "delices", "saveurs", "original", "gourmand", "gourmande", "bonne", "simple",
                 "classique", "tradition", "envie", "passion", "authentique", "pure", "vrai"}
# fautes recurrentes de llama3.2:3b, corrigees avant verification
CORRECTIONS = [(re.compile(r"\bune excellente? choix\b", re.I), "un excellent choix"),
               (re.compile(r"\bune (?:tr[eè]s )?bon(?:ne)? choix\b", re.I), "un très bon choix"),
               (re.compile(r"\bun (excellente|bonne|super) id[eé]e\b", re.I), r"une \1 idée")]
GENRE = re.compile(r"\b(?:monsieur|madame|mademoiselle)\b")
# le prototype n'envoie rien : toute annonce d'envoi par l'assistant est refusee
ENVOI = re.compile(r"\b(?:je vais|je vous|nous allons|je peux) (?:vous )?(?:la |le |les )?"
                   r"(?:transmettre|envoyer|expedier|faire parvenir)|\bj ai (?:envoye|transmis)"
                   r"|\b(?:est|a ete) (?:envoyee?|transmise?)\b")
CODE = re.compile(r"\bDEMO-\d{3}\b")


def corriger(texte: str) -> str:
    for motif, remplacement in CORRECTIONS:
        texte = motif.sub(lambda m: (lambda r: r[0].upper() + r[1:] if m.group(0)[0].isupper()
                                     else r)(m.expand(remplacement)), texte)
    return texte


def id_piste(aromes: list[str]) -> str:
    """Identifiant stable d'une piste, tire de ses aromes : "citron-vert+citron"."""
    return "+".join(re.sub(r"[^a-z0-9]+", "-", normaliser(a)).strip("-") for a in aromes)


def libelle_piste(piste: dict) -> str:
    aromes = piste["aromes"]
    return aromes[0] if len(aromes) == 1 else " + ".join(aromes)


def _mots(texte: str) -> str:
    return f" {' '.join(re.findall(r'[a-z0-9]+', normaliser(texte)))} "


NOMBRE = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)?")
COUPLE = re.compile(r"\b(\d+) (?:des|sur|parmi(?: les)?) (?:les )?(\d+)\b")


def nombres(texte: str) -> set[str]:
    return {n.replace(",", ".") for n in NOMBRE.findall(CODE.sub(" ", texte))}


def couples_inventes(texte: str, source: str) -> list[str]:
    """Couples « X des Y » de la reponse absents de la source : chiffres vrais, mais pris dans deux
    faits differents (ex. « 6 des 19 produits » alors que 6 venait d'une autre etude)."""
    source = _mots(source)
    return [f"{x} des {y}" for x, y in COUPLE.findall(_mots(texte))
            if not re.search(rf" {x} [a-z ]{{0,40}}?\b{y}\b", source)]


def aromes_inventes(texte: str, source: str) -> list[str]:
    """Aromes de la liste de reference cites dans la reponse mais absents de la source."""
    return sorted(set(extraire_aromes(texte)) - set(extraire_aromes(source)))


def types_inventes(texte: str, source: str) -> list[str]:
    """Types de produit cites dans la reponse mais absents de la source (« 50 sirops » recopie
    de l'exemple guide alors que l'etude porte sur des boissons petillantes)."""
    texte, source = (" ".join(re.findall(r"[a-z]+", normaliser(t))) for t in (texte, source))
    return [nom for nom, (motif, *_) in _TYPES.items() if motif.search(texte) and not motif.search(source)]


PISTE = re.compile(r"^\s*([1-3])\.\s", re.M)


def codes_par_piste(texte: str) -> dict[str, set[str]]:
    """Codes DEMO de chaque piste numerotee (de « 1. » jusqu'a la piste suivante)."""
    debuts = list(PISTE.finditer(texte))
    return {m.group(1): set(CODE.findall(texte[m.end():(debuts[i + 1].start() if i + 1 < len(debuts)
                                                         else len(texte))]))
            for i, m in enumerate(debuts)}


def codes_deplaces(texte: str, source: str) -> list[str]:
    """Pistes dont les codes ne sont pas ceux du brouillon (reference mise sous la mauvaise piste)."""
    attendu, obtenu = codes_par_piste(source), codes_par_piste(texte)
    return [f"piste {n}" for n in attendu if n in obtenu and obtenu[n] != attendu[n]]


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


# --- Banque de references -----------------------------------------------------------------------

class BanqueReferences:
    """Banque de demo (codes DEMO fictifs) : references les plus proches d'un arome.

    bge-m3 compare « arome X » au texte nom + profil sensoriel + applications de chaque reference,
    apres filtre sur l'application et les labels demandes. Une reference n'est retenue que si elle
    cite l'arome (nom ou profil) ou si son score atteint SEUIL_REFERENCE.
    """

    def __init__(self, moteur: "MoteurV22", chemin: Path = BANQUE_DEFAUT):
        self.moteur = moteur
        self.df = pd.read_csv(chemin, dtype=str).fillna("")
        self.textes = (self.df["nom"] + " | " + self.df["profil_sensoriel"] + " | "
                       + self.df["applications"].str.replace("|", ", ")).tolist()
        self.aromes = [set(extraire_aromes(f"{n} {p}")) | {f} for n, p, f in
                       zip(self.df["nom"], self.df["profil_sensoriel"], self.df["famille"])]
        self.aromes_du_nom = [set(extraire_aromes(n)) for n in self.df["nom"]]
        self.labels_par_ref = [set(l.split("|")) for l in self.df["labels"]]
        self.fichier = Path(moteur.dossier_cache) / f"banque_{MODELE_EMBEDDING}.npz"
        self.vecteurs = None

    def _vecteurs(self) -> np.ndarray:
        if self.vecteurs is None:
            cle = hashlib.sha256("\n".join([MODELE_EMBEDDING, *self.textes]).encode()).hexdigest()
            if self.fichier.exists() and str(np.load(self.fichier)["cle"]) == cle:
                self.vecteurs = np.load(self.fichier)["vecteurs"]
            else:
                self.vecteurs = self.moteur._embed(self.textes)
                self.fichier.parent.mkdir(parents=True, exist_ok=True)
                np.savez(self.fichier, vecteurs=self.vecteurs, cle=cle)
        return self.vecteurs

    @staticmethod
    def fiche(ligne: pd.Series, score: float | None = None) -> dict:
        fiche = {"code": ligne["code"], "nom": ligne["nom"], "profil_sensoriel": ligne["profil_sensoriel"],
                 "forme": ligne["forme"], "labels": ligne["labels"].split("|") if ligne["labels"] else []}
        if score is not None:
            fiche["score"] = round(float(score), 3)
        return fiche

    def _masque(self, application: str | None, labels: list[str]) -> np.ndarray:
        masque = self.df["famille"].ne("solution").to_numpy()
        if application:
            masque &= self.df["applications"].str.split("|").map(lambda a: application in a).to_numpy()
        for label in labels:
            masque &= self.df["labels"].str.split("|").map(lambda l, x=label: x in l).to_numpy()
        return masque

    def chercher(self, aromes: list[str], application: str | None, labels: list[str]) -> dict:
        """{"references": [...], "manquants": [aromes sans reference], "sans_label": [...]}.

        Une reference qui couvre tous les aromes de la piste (ex. citron vert et menthe) est
        preferee ; sinon, une reference par arome."""
        try:
            vecteurs = self._vecteurs()
            requetes = self.moteur._embed([f"arôme {a}" for a in aromes] + [f"arôme {' et '.join(aromes)}"])
            scores_par_requete = requetes @ vecteurs.T
        except OllamaIndisponible:  # repli : correspondance par nom d'arome seulement
            scores_par_requete = np.zeros((len(aromes) + 1, len(self.df)), dtype=np.float32)

        def meilleure(scores, masque, cibles, strict=False):
            candidats = [i for i in np.argsort(-scores) if masque[i]
                         and (cibles <= self.aromes[i] or (not strict and scores[i] >= SEUIL_REFERENCE))]
            # d'abord les references qui portent l'arome dans leur nom, puis la version standard si
            # le bio n'est pas demande ; a egalite, l'ordre bge-m3
            candidats.sort(key=lambda i: (not cibles <= self.aromes_du_nom[i],
                                          "bio" in self.labels_par_ref[i] and "bio" not in labels))
            return candidats[0] if candidats else None

        masque = self._masque(application, labels)
        sans_labels = self._masque(application, [])
        if len(aromes) > 1:
            # reference unique pour toute l'association : seulement si elle cite chaque arome
            i = meilleure(scores_par_requete[-1], masque, set(aromes), strict=True)
            if i is not None:
                return {"references": [self.fiche(self.df.iloc[i], scores_par_requete[-1][i])],
                        "manquants": [], "sans_label": []}
        resultat = {"references": [], "manquants": [], "sans_label": []}
        for arome, scores in zip(aromes, scores_par_requete):
            i = meilleure(scores, masque, {arome})
            if i is not None:
                resultat["references"].append(self.fiche(self.df.iloc[i], scores[i]))
                continue
            j = meilleure(scores, sans_labels, {arome}) if labels else None
            if j is not None:  # existe, mais sans le label demande
                fiche = self.fiche(self.df.iloc[j], scores[j])
                resultat["sans_label"].append({"arome": arome, **fiche, "labels_manquants": [
                    label for label in labels if label not in fiche["labels"]]})
            else:
                resultat["manquants"].append(arome)
        return resultat

    def solutions(self, contraintes: list[str], application: str | None) -> list[dict]:
        noms = list(dict.fromkeys(SOLUTIONS[c] for c in contraintes if c in SOLUTIONS))
        lignes = self.df[self.df["famille"].eq("solution") & self.df["nom"].isin(noms)]
        if application:
            lignes = lignes[lignes["applications"].str.split("|").map(lambda a: application in a)]
        return [self.fiche(ligne) for _, ligne in lignes.iterrows()]


# --- Mecanismes generaux (vocabulaire, type inconnu, marques, intentions) -------------------------
from src.mecanismes_v22 import (COUT, SERVICE, VAGUE, Marques, VocabulaireAromes, groupe_produit,  # noqa: E402
                                ancre_dans, mots_inconnus, rattacher_type)


# le message evoque un gout : « gout X », « saveur X », « arome X », « au X », « a la X »
GOUT_EVOQUE = re.compile(r"\b(?:gouts?|saveurs?|aromes?|parfums?|au|aux|a la|a l)\b")


def type_et_span(texte: str) -> tuple[str | None, tuple[int, int] | None]:
    """Comme type_cite, avec la position du mot de type dans le texte (deja normalise et joint)."""
    contraintes = [m.span() for motif, _ in _CONTRAINTES.values() for m in motif.finditer(texte)]
    for nom, (motif, *_) in _TYPES.items():
        for m in motif.finditer(texte):
            if not any(debut <= m.start() and m.end() <= fin for debut, fin in contraintes):
                return nom, m.span()
    return None, None


def _masquer(texte: str, spans) -> str:
    morceaux = list(texte)
    for span in spans:
        if span:
            morceaux[span[0]:span[1]] = " " * (span[1] - span[0])
    return "".join(morceaux)


# --- Moteur : etude de marche par type puis contraintes ----------------------------------------

class MoteurV22(MoteurV21):
    """Etude de marche V2.1 restreinte au type de produit, puis aux contraintes."""

    version = VERSION_V22

    def __init__(self, catalogue: str = "auto", ollama_url: str = OLLAMA_DEFAUT,
                 dossier_cache: Path = CACHE_DEFAUT, delai_llm: float = 60.0):
        """catalogue "auto" : catalogue complet si ses vecteurs bge-m3 existent, sinon echantillon."""
        if catalogue == "auto":
            complet = Path(dossier_cache) / f"{MODELE_EMBEDDING}_complet.npz"
            catalogue = "complet" if complet.exists() else "echantillon"
        super().__init__(catalogue, ollama_url, dossier_cache, delai_llm)
        self._textes_filtre: dict[int, tuple[pd.Series, pd.Series]] = {}
        # mots du vocabulaire du moteur : jamais un arome, jamais un mot inconnu
        self.exclus = {m for nom in [*TYPES, *PLURIELS.values(), *CONTRAINTES, *PROFILS,
                                     *FEMININ_SINGULIER.values()]
                       for m in re.findall(r"[a-z]+", normaliser(nom))}
        catalogues = [pd.read_csv(CATALOGUE_DEFAUT, dtype=str)]
        if self.catalogue == "complet":
            catalogues.append(self.flavors)
        self.marques = Marques(catalogues, self.exclus)
        self._vocabulaire: VocabulaireAromes | None = None

    def est_exclu(self, terme: str) -> bool:
        """Terme du vocabulaire du moteur (type, produit, contrainte, profil) ou marque."""
        return (terme in self.exclus or bool(PRODUITS.search(terme))
                or any(motif.search(terme) for motif, *_ in _TYPES.values())
                or any(motif.search(terme) for motif, _ in _CONTRAINTES.values())
                or any(motif.search(terme) for motif in _PROFILS.values())
                or bool(self.marques.trouvees(terme)))

    @property
    def vocabulaire(self) -> VocabulaireAromes:
        """Vocabulaire d'aromes (liste de reference + Fragrance alimentaire + catalogue), construit
        a la premiere utilisation ; les alias bge-m3 sont mis en cache."""
        if self._vocabulaire is None:
            self._vocabulaire = VocabulaireAromes(
                self.flavors, self.est_exclu, embed=self._embed,
                cache=Path(self.dossier_cache) / f"vocabulaire_aromes_{self.catalogue}.json")
        return self._vocabulaire

    def aromes_du_texte(self, texte: str, division: str = "flavors") -> list[str]:
        return self.vocabulaire.extraire(texte) if division == "flavors" else extraire_aromes(texte, division)

    def _embed(self, textes: list[str]) -> np.ndarray:
        vecteurs = np.asarray(self._post("/api/embed", 120, model=MODELE_EMBEDDING, input=textes,
                                         truncate=True, keep_alive=KEEP_ALIVE)["embeddings"],
                              dtype=np.float32)
        return vecteurs / np.linalg.norm(vecteurs, axis=1, keepdims=True)

    def _textes(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        """(categories + nom, labels + categories + nom), normalises, calcules une fois par catalogue."""
        if id(df) not in self._textes_filtre:
            nom = df["product_name"].fillna("").map(normaliser)
            cats = df["categories_tags"].fillna("").str.lower()
            self._textes_filtre[id(df)] = (cats + " " + nom,
                                           df["labels_tags"].fillna("").str.lower() + " " + cats + " " + nom)
        return self._textes_filtre[id(df)]

    def _classer(self, division: str, requete: str) -> tuple[pd.DataFrame, np.ndarray, str]:
        """Tout le catalogue de la division et sa similarite a la requete."""
        if division == "flavors":
            try:
                return (self.flavors, self._vecteurs() @ self._embed([requete])[0],
                        f"{MODELE_EMBEDDING} ({self.catalogue})")
            except (OllamaIndisponible, FileNotFoundError):
                pass
        df_div, vectoriseur, matrice = self.v1.index[division]
        return df_div, cosine_similarity(vectoriseur.transform([normaliser(requete)]), matrice).ravel(), "tfidf v1"

    def masque_type(self, df: pd.DataFrame, type_produit: str) -> np.ndarray:
        _, motif, categories, _, _ = _TYPES[type_produit]
        masque = df["query_category"].isin(categories).to_numpy()
        if motif is not None:
            masque &= self._textes(df)[0].str.contains(motif).to_numpy()
        return masque

    def etude(self, division: str, arome: str | None, type_produit: str | None, requete: str,
              contraintes: list[str], k: int = 3) -> dict:
        """Pistes V2.1 sur les produits du type demande qui respectent les contraintes."""
        df, sims, recherche = self._classer(division, requete)
        retenus = np.ones(len(df), dtype=bool)
        bilan_type = None
        if division == "flavors" and type_produit in _TYPES:
            retenus = self.masque_type(df, type_produit)
            bilan_type = {"type": type_produit, "produits_du_type": int(retenus.sum())}
        textes_filtre = self._textes(df)[1]
        bilan = []
        for nom in contraintes:
            motif = _CONTRAINTES[nom][1]
            if motif is None:
                if nom not in SOLUTIONS:
                    bilan.append({"contrainte": nom, "appliquee": False,
                                  "raison": "les données du marché ne le précisent pas"})
                continue
            conformes = retenus & textes_filtre.str.contains(motif).to_numpy()
            n = int(conformes.sum())
            if n >= MIN_FILTRE:
                retenus = conformes
                bilan.append({"contrainte": nom, "appliquee": True, "produits_conformes": n})
            else:
                bilan.append({"contrainte": nom, "appliquee": False,
                              "raison": ("aucun produit du marché ne la respecte" if n == 0 else
                                         f"seulement {_produits(n)} du marché la respecte"
                                         + ("nt" if n > 1 else ""))})
        ordre = np.argsort(-sims, kind="stable")
        selection = df.iloc[ordre[retenus[ordre]][:N_MARCHE]]
        textes = selection["product_name"].fillna("") + " | " + selection["ingredients_text"].fillna("")
        marche = [self.aromes_du_texte(t, division) for t in textes]
        if arome and division == "flavors" and not self.vocabulaire.extraire(arome):
            # arome hors vocabulaire (« durian ») : compte par sa presence dans le texte du produit
            motif = re.compile(rf"\b{re.escape(normaliser(arome))}")
            marche = [a + [arome] if motif.search(normaliser(t)) and arome not in a else a
                      for a, t in zip(marche, textes)]
        etapes = {"recherche": recherche,
                  "filtre_type": type_produit if bilan_type else None,
                  "filtre_contraintes": [b["contrainte"] for b in bilan if b["appliquee"]]}
        resultat = self._pistes_depuis(division, arome, type_produit, marche, {}, etapes, "v2.2", k)
        resultat["marche"].setdefault("nb_produits_analyses", len(marche))
        resultat["marche"]["type"] = bilan_type
        resultat["marche"]["contraintes"] = bilan
        resultat["marche"]["frequence"] = dict(Counter(a for aromes in marche for a in aromes))
        return {**resultat, "version_modele": VERSION_V22}


# --- Assistant ----------------------------------------------------------------------------------

class AssistantV22:
    """Conversation complete : analyse, projet cumule, etude, references, brouillon, reformulation."""

    def __init__(self, moteur: MoteurV22 | None = None, noms: NomsDuCommerce | None = None,
                 reformuler: bool = False, banque: Path = BANQUE_DEFAUT, prechauffer: bool = False):
        """reformuler=False (defaut, mode rapide) : la reponse est le brouillon factuel.
        reformuler=True : llama3.2:3b reformule le brouillon (verifie), environ 5 fois plus lent.
        prechauffer=True : charge les deux modeles et les vecteurs tout de suite."""
        self.moteur = moteur or MoteurV22()
        self.reformuler = reformuler
        chemins = [CATALOGUE_DEFAUT] + ([CATALOGUE_COMPLET] if self.moteur.catalogue == "complet" else [])
        self.noms = noms or NomsDuCommerce(chemins)
        self.banque = BanqueReferences(self.moteur, banque)
        self.historique: list[dict] = []  # trace de la conversation (le contexte en est tire)
        self.reinitialiser()
        if prechauffer:
            self.prechauffer()

    def prechauffer(self) -> dict:
        """Charge bge-m3, llama3.2:3b, les vecteurs du catalogue et de la banque (keep_alive long)."""
        etat = {}
        for nom, action in (("vecteurs catalogue", self.moteur._vecteurs),
                            ("banque", self.banque._vecteurs),
                            ("vocabulaire d'arômes", lambda: self.moteur.vocabulaire),
                            (MODELE_LLM, lambda: self._chat([{"role": "user", "content": "ok"}],
                                                            num_predict=1))):
            try:
                action()
                etat[nom] = "ok"
            except (OllamaIndisponible, FileNotFoundError) as erreur:
                etat[nom] = f"indisponible ({erreur.__class__.__name__})"
        return etat

    def reinitialiser(self) -> None:
        self.projet = {"division": None, "type": None, "produit": None, "arome": None, "profil": [],
                       "contraintes": [], "aromes_cites": [], "volume": None, "messages": []}
        self.etude: dict | None = None  # derniere sortie de MoteurV22.etude (ou relance)
        self.etudes_precedentes: list[tuple[str, dict]] = []  # (resume, frequence des aromes)
        self.piste_choisie: dict | None = None
        self.demande_echantillons: dict | None = None
        self.hors_bornes: int | None = None  # numero de piste demande mais inexistant
        self.type_hors_catalogue = False  # produit cite sans categorie proche au catalogue
        self.marque_citee = False  # le dernier message citait une marque

    def _chat(self, messages: list[dict], format_json: dict | None = None,
              num_predict: int = 300) -> str:
        corps = {"model": MODELE_LLM, "stream": False, "keep_alive": KEEP_ALIVE, "messages": messages,
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

    # --- 1. Analyse : regles d'abord, un seul appel au modele sinon ----------------------------

    def _resume_etat(self) -> str:
        if not self.projet["messages"]:
            return "Aucun projet en cours."
        lignes = [f"Projet en cours : {' ; '.join(self.projet['messages'])}."]
        if self.pistes:
            lignes.append("Pistes proposées : " + " ; ".join(
                f"{i}. {libelle_piste(p)}" for i, p in enumerate(self.pistes, 1)) + ".")
        if self.piste_choisie:
            lignes.append(f"Piste choisie : {self.piste_choisie['numero']}.")
        return "\n".join(lignes)

    def _analyse_llm(self, message: str) -> dict:
        """Un seul appel : intention + extraction, avec les garde-fous anti-invention de la V2."""
        sortie = json.loads(self._chat(
            [{"role": "system", "content": SYSTEME_ANALYSE},
             {"role": "user", "content": f"{self._resume_etat()}\nMessage du client : « {message} »"}],
            format_json=SCHEMA_ANALYSE, num_predict=120))
        texte = normaliser(message)
        aromes = [a.strip() for a in sortie.get("aromes", []) if isinstance(a, str) and a.strip()]
        arome = aromes[0] if aromes else None
        if arome and not (ancre(arome, message) or SENSORIEL.search(texte)):
            arome = None
        application = str(sortie.get("application") or "").strip() or None
        if not (application and ancre(application, message)):
            trouve = PRODUITS.search(texte)
            application = trouve.group(0) if trouve else None
        division = sortie.get("division")
        return {"intention": sortie.get("intention") if sortie.get("intention") in INTENTIONS else None,
                "numero": sortie.get("numero_piste") or None,
                "division": division if division in ("flavors", "fragrance") else None,
                "arome": arome, "application": application}

    @staticmethod
    def _sans_reconnus(texte: str) -> str:
        """Texte sans les contraintes et le profil reconnus : « pas trop sucre » ou « fruite » ne
        doivent pas faire croire qu'un gout inconnu est decrit."""
        for motif, _ in _CONTRAINTES.values():
            texte = motif.sub(" ", texte)
        for motif in _PROFILS.values():
            texte = motif.sub(" ", texte)
        return texte

    def _sur_les_pistes(self, message: str) -> bool:
        """La question porte-t-elle sur les pistes (numero, arome cite, « cette association ») ?"""
        texte = self.moteur.marques.masquer(" ".join(re.findall(r"[a-z]+", normaliser(message))))
        return bool(numero_cite(message) or self.moteur.aromes_du_texte(texte, self.projet["division"] or "flavors")
                    or ASSOCIATION.search(normaliser(message)))

    def analyser(self, message: str) -> dict:
        """{intention, numero, division, type, arome, aromes, application, contraintes, retraits,
        profil, volume, marques, trace}.

        Regles d'abord (texte entierement reconnu : reponse rapide). llama3.2:3b n'est appele que
        s'il reste des mots inconnus alors qu'il manque l'arome ou le type, ou si un produit est
        cite sans type reconnu."""
        mots_q = _mots_normalises(message)
        texte = " ".join(re.findall(r"[a-z]+", normaliser(message)))
        projet_en_cours = bool(self.projet["messages"])
        moteur = self.moteur
        marques = moteur.marques.trouvees(texte)
        texte = moteur.marques.masquer(texte)  # jamais d'arome tire d'un nom de marque
        nouveau_projet = projet_en_cours and bool(NOUVEAU_PROJET.search(mots_q))
        retraits, sans_retraits = extraire_retraits(texte) if projet_en_cours else ([], texte)
        retraits = [r for r in retraits if r in self.projet["contraintes"]]
        type_nom, type_span = type_et_span(texte)
        texte_aromes = _masquer(texte, [type_span])  # le mot du type n'est jamais l'arome
        cites = moteur.vocabulaire.extraire(texte_aromes)
        spans = [type_span, *moteur.vocabulaire.spans(texte_aromes),
                 *[m.span() for motif, _ in _CONTRAINTES.values() for m in motif.finditer(texte)],
                 *[m.span() for motif in _PROFILS.values() for m in motif.finditer(texte)],
                 *[m.span() for motif in _RETRAITS.values() for m in motif.finditer(texte)]]
        inconnus = mots_inconnus(texte, spans, moteur.exclus)
        cite = numero_cite(message)
        a = {"intention": None, "numero": None, "division": "flavors" if type_nom else None,
             "type": type_nom, "arome": cites[0] if cites else None, "aromes": cites,
             "application": None, "contraintes": extraire_contraintes(sans_retraits),
             "retraits": retraits, "profil": extraire_profil(texte),
             "volume": extraire_volume(message), "marques": marques,
             "trace": {"modele_appele": False, "mots_inconnus": inconnus}}
        produit_cite = PRODUITS.search(texte) is not None and type_nom is None
        changement = a["type"] or a["arome"] or a["contraintes"] or a["retraits"] or a["profil"] \
            or a["volume"]
        # le modele n'est appele que s'il reste des mots inconnus alors qu'il manque l'arome (le
        # projet n'en a pas, ou le message evoque un gout) ou le type, ou si un produit est cite
        # sans type reconnu
        evoque_un_gout = bool(GOUT_EVOQUE.search(texte))
        arome_manquant = not a["arome"] and (not self.projet["arome"] or evoque_un_gout)
        type_manquant = not a["type"] and not self.projet["type"]
        besoin_modele = (bool(inconnus) and (arome_manquant or type_manquant)) \
            or (produit_cite and not self.projet["type"])

        # regles qui suffisent
        if ECHANTILLON.search(mots_q) and COUT.search(mots_q):
            a["intention"] = "question"  # « c'est combien un echantillon ? » : question de service
        elif ECHANTILLON.search(mots_q) and not nouveau_projet:
            a["intention"] = "demande_echantillons"
        elif self.pistes and cite and (CHOIX.search(mots_q) or len(mots_q.split()) <= 4):
            a["intention"], a["numero"] = "choix_piste", cite  # numero hors bornes : voir repondre
        elif nouveau_projet and not changement and not inconnus:
            a["intention"] = "nouvelle_demande"  # « nouveau projet » seul : projet vide, relance
        elif POLITESSE.search(mots_q.replace(" ?", "")):
            a["intention"] = "hors_sujet"
        elif self.pistes and QUESTION.search(mots_q) and self._sur_les_pistes(message) and not (
                a["type"] or a["contraintes"] or a["retraits"] or a["volume"]):
            a["intention"] = "question_piste"
        elif SERVICE.search(mots_q) and not (a["type"] or a["arome"] or a["contraintes"] or a["retraits"]):
            a["intention"] = "question"  # prix, delais, livraison...
        elif marques and not (a["type"] or a["arome"] or a["contraintes"] or produit_cite):
            a["intention"] = "hors_sujet"  # on ne travaille pas a partir d'une marque
        elif changement and not besoin_modele:
            a["intention"] = self._nouveau_ou_precision(a, nouveau_projet)
        elif not changement and not inconnus and not produit_cite:
            a["intention"] = self._vague_ou_hors_sujet(mots_q, projet_en_cours)
        if a["intention"]:
            a["trace"]["intention"] = a["intention"]
            return a

        # sinon : un seul appel au modele (extraction de l'arome et du produit inconnus)
        try:
            llm = self._analyse_llm(" ".join(texte.split()) if marques else message)
            a["trace"].update(modele_appele=True, intention_llm=llm["intention"])
        except (OllamaIndisponible, TypeError, ValueError, AttributeError):
            llm = {"intention": None, "numero": None, "division": None, "arome": None,
                   "application": None}
            a["trace"].update(modele_appele=True, intention_llm="indisponible")
            apres = APRES_GOUT.search(texte)  # repli : le mot qui suit « arome / gout / saveur »
            if apres and apres.group(1) in inconnus:
                llm["arome"] = apres.group(1)
            trouve = PRODUITS.search(texte)
            llm["application"] = trouve.group(0) if trouve and type_nom is None else None
        application = llm["application"] if not a["type"] else None
        if application:  # le nom du produit tel que le client l'a ecrit, sans le gout
            mots_aromes = {m for c in cites for m in re.findall(r"[a-z]+", normaliser(c))}
            application = groupe_produit(application, message, arrets=mots_aromes) or None
        if application and ancre_dans(application, [type_nom or ""]):
            application = None
        if application:
            a["application"] = application
            rattache, score = rattacher_type(moteur, application, list(TYPES))
            a["trace"]["type_rattache"] = {"produit": application, "type": rattache, "score": round(score, 3)}
            if rattache:
                a["type"] = rattache
            a["division"] = "flavors"
        # l'arome du modele doit venir d'un mot inconnu du message, et ne pas etre le produit
        arome_llm = llm["arome"]
        if arome_llm and (not ancre_dans(arome_llm, inconnus) or ancre_dans(arome_llm, [application or ""])
                          or moteur.est_exclu(normaliser(arome_llm))):
            arome_llm = None
        if not arome_llm and not cites:
            # repli : le mot inconnu qui suit « a la / au / gout / saveur » (« pizza a la truffe »)
            for m in re.finditer(GOUT_EVOQUE.pattern + r" ([a-z]{3,})", texte):
                if m.group(1) in inconnus and not ancre_dans(m.group(1), [application or ""]):
                    arome_llm = m.group(1)
                    break
        a["aromes"] = [c for c in cites if not ancre_dans(c, [application or ""])]
        if arome_llm and arome_llm.lower() not in a["aromes"]:
            a["aromes"].append(arome_llm.lower())
        a["arome"] = a["aromes"][0] if a["aromes"] else None
        a["division"] = a["division"] or ("flavors" if a["arome"] else llm["division"])
        reconnu = bool(a["type"] or a["arome"] or a["application"] or a["contraintes"]
                       or a["profil"] or a["retraits"] or a["volume"])
        if llm["intention"] == "choix_piste" and llm["numero"] and 1 <= llm["numero"] <= len(self.pistes):
            intention = "choix_piste"
        elif reconnu:
            intention = self._nouveau_ou_precision(a, nouveau_projet)
        elif self.pistes and QUESTION.search(mots_q) and self._sur_les_pistes(message):
            intention = "question_piste"
        else:
            intention = self._vague_ou_hors_sujet(mots_q, projet_en_cours)
        if nouveau_projet and intention in ("precision", "question", "question_piste", "hors_sujet"):
            intention = "nouvelle_demande"  # « une autre boisson », « maintenant je voudrais… »
        a["intention"], a["numero"] = intention, llm["numero"] if intention == "choix_piste" else None
        a["trace"]["intention"] = intention
        return a

    def _nouveau_ou_precision(self, a: dict, nouveau_projet: bool) -> str:
        projet = self.projet
        if not projet["messages"] or nouveau_projet:
            return "nouvelle_demande"
        autre_produit = (a["type"] and projet["type"] and generique(a["type"]) != generique(projet["type"])
                         and a["arome"] is not None)
        return "nouvelle_demande" if autre_produit else "precision"

    @staticmethod
    def _vague_ou_hors_sujet(mots_q: str, projet_en_cours: bool) -> str:
        """Demande de produit trop vague -> relance (nouvelle_demande sans information) ; rien sur
        un produit ni sur le service -> hors_sujet."""
        if VAGUE.search(mots_q) and not projet_en_cours:
            return "nouvelle_demande"
        return "hors_sujet"

    # --- 2 et 3. Projet et etude --------------------------------------------------------------

    def _mettre_a_jour(self, message: str, analyse: dict) -> None:
        projet = self.projet
        if analyse["division"] and not projet["division"]:
            projet["division"] = analyse["division"]
        nouveau_type = analyse["type"]
        if nouveau_type and not (projet["type"] and nouveau_type == generique(projet["type"])):
            projet["type"] = nouveau_type  # « boisson » ne remplace pas « boisson petillante »
        projet["produit"] = projet["type"] or analyse["application"] or projet["produit"]
        if analyse["arome"]:
            reference = self.moteur.aromes_du_texte(analyse["arome"], projet["division"] or "flavors")
            projet["arome"] = reference[0] if reference else analyse["arome"].lower()
        _ajouter(projet["profil"], analyse["profil"])
        _ajouter(projet["contraintes"], analyse["contraintes"])
        projet["contraintes"][:] = [c for c in projet["contraintes"] if c not in analyse.get("retraits", [])]
        if analyse.get("volume"):
            projet["volume"] = analyse["volume"]
        _ajouter(projet["aromes_cites"], ([projet["arome"]] if analyse["arome"] else [])
                 + analyse.get("aromes", []))
        if "sans sucre" in projet["contraintes"] and "peu sucré" in projet["contraintes"]:
            projet["contraintes"].remove("peu sucré")
        projet["messages"].append(message)
        self.piste_choisie, self.demande_echantillons = None, None
        self.type_hors_catalogue = projet["type"] is None and projet["produit"] is not None

    def _requete(self) -> str:
        p = self.projet
        morceaux = [p["produit"], f"goût {p['arome']}" if p["arome"] else None, *p["profil"],
                    *p["contraintes"]]
        return " ".join(m for m in morceaux if m) or " ".join(p["messages"])

    def _nom_produits(self, n: int) -> str:
        """'19 boissons pétillantes', '50 produits'."""
        if self.projet["type"] in PLURIELS:
            return f"{n} {PLURIELS[self.projet['type']] if n > 1 else self.projet['type']}"
        return _produits(n)

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
        self.etude = self.moteur.etude(p["division"], p["arome"], p["type"], self._requete(),
                                       p["contraintes"])
        marche = self.etude["marche"]
        feminin = p["type"] in TYPES_FEMININS
        filtres = [(ADJECTIFS_FEMININS if feminin else {}).get(c, ADJECTIFS[c])
                   for c in self.etude["etapes"]["filtre_contraintes"]]
        n = marche["nb_produits_analyses"]
        self.etude["resume"] = (self._nom_produits(n) + " du marché les plus proches de votre projet"
                                + (f", {'toutes' if feminin else 'tous'} {_et(filtres)}" if filtres else ""))
        self._relier_references()

    def _labels_demandes(self) -> list[str]:
        return [CONTRAINTES[c][2] for c in self.projet["contraintes"] if CONTRAINTES[c][2]]

    def _application(self) -> str | None:
        t = self.projet["type"]
        return _TYPES[t][3] if t in _TYPES else None

    def _relier_references(self) -> None:
        """Chaque piste recoit ses references de la banque ; solutions selon les contraintes."""
        if self.projet["division"] != "flavors":
            for piste in self.pistes:
                piste["references"], piste["sans_reference"] = [], piste["aromes"]
            self.etude["solutions"] = []
            return
        for piste in self.pistes:
            trouve = self.banque.chercher(piste["aromes"], self._application(), self._labels_demandes())
            piste["references"] = trouve["references"]
            piste["sans_reference"] = trouve["manquants"]
            piste["sans_label"] = trouve["sans_label"]
        self.etude["solutions"] = self.banque.solutions(self.projet["contraintes"], self._application())

    # --- 4. Brouillon factuel (contexte recupere) ---------------------------------------------

    def _projet_affiche(self) -> dict:
        p = self.projet
        return {"division": {"flavors": "arôme alimentaire", "fragrance": "parfum"}.get(p["division"]),
                "type_de_produit": p["produit"], "arome_principal": p["arome"],
                "profil_recherche": p["profil"], "contraintes": p["contraintes"]}

    def _etudies(self) -> str:
        return "étudiées" if self.projet["type"] in TYPES_FEMININS else "étudiés"

    def origine(self, piste: dict) -> str:
        """D'ou vient la piste : nombre de produits, association observee ou non."""
        marche = self.etude["marche"]
        n, principal = marche["nb_produits_analyses"], piste["aromes"][0]
        n_principal = marche.get("nb_avec_arome_principal") or 0
        if piste["type"] == "principal":
            etudies = f"{self._nom_produits(n)} {self._etudies()}"
            aucun = "aucune" if self.projet["type"] in TYPES_FEMININS else "aucun"
            return (f"l'arôme {principal} est utilisé par {n_principal} des {etudies}" if n_principal else
                    f"{aucun} des {etudies} n'utilise l'arôme {principal} : une place libre sur ce marché")
        autre = piste["aromes"][1]
        if piste.get("observee"):
            return (f"association observée : {piste['nb_produits']} des {n_principal} produits "
                    f"{a_la(principal)} étudiés y {'ajoutent' if piste['nb_produits'] > 1 else 'ajoute'} "
                    f"l'arôme {autre}")
        return (f"association pas encore observée sur ce marché (l'arôme {autre} est présent dans "
                f"{_produits(piste['nb_produits'])} étudiés) : à valider en dégustation")

    def _texte_references(self, piste: dict) -> str:
        morceaux = [f"{r['code']} {r['nom']} ({r['profil_sensoriel']} ; {r['forme']})"
                    for r in piste.get("references", [])]
        texte = ("Référence : " if len(morceaux) == 1 else "Références : ") + " + ".join(morceaux) + "." \
            if morceaux else ""
        for s in piste.get("sans_label", []):
            labels = _et(self._labels_demandes())
            texte += (f" Pas de version {labels} de l'arôme {s['arome']} dans la banque : "
                      f"{s['code']} {s['nom']} existe sans ce label.")
        if piste.get("sans_reference"):
            manquants = piste["sans_reference"]
            texte += (f" Aucune référence proche pour {'les arômes' if len(manquants) > 1 else 'l’arôme'} "
                      f"{_et(manquants)} dans la banque : une création sur mesure est possible.").replace("’", "'")
        return texte.strip()

    def _pistes_affichees(self) -> list[dict]:
        return [{"numero": i, "id": id_piste(p["aromes"]), "type": p["type"],
                 "aromes": libelle_piste(p), "liste_aromes": list(p["aromes"]),
                 "nb_produits": int(p.get("nb_produits") or 0), "explication": p["explication"],
                 "origine": self.origine(p), "references": p.get("references", []),
                 "sans_reference": p.get("sans_reference", []),
                 "references_sans_label": self._sans_label(p)}
                for i, p in enumerate(self.pistes, 1)]

    @staticmethod
    def _sans_label(piste: dict) -> list[dict]:
        """Arômes dont la référence n'a pas le label demandé : {arome, code, label_manquant}."""
        return [{"arome": s["arome"], "code": s["code"], "label_manquant": ", ".join(s["labels_manquants"])}
                for s in piste.get("sans_label", [])]

    def numero_de_piste(self, piste_id: str) -> int | None:
        """Numero (1 a 3) de la piste d'identifiant piste_id parmi les pistes actuelles."""
        return next((i for i, p in enumerate(self.pistes, 1) if id_piste(p["aromes"]) == piste_id), None)

    @property
    def etape(self) -> str:
        """Etat de la conversation apres le dernier message (voir ETAPES)."""
        if self.demande_echantillons:
            return "echantillons"
        if self.piste_choisie:
            return "recapitulatif"
        return "pistes" if self.pistes else "relance"

    def _rappel_pistes(self) -> str:
        return _et([f"{i}. {libelle_piste(p)}" for i, p in enumerate(self.pistes, 1)], "ou")

    def _resume_projet(self) -> str:
        p = self.projet
        morceaux = [" ".join(m for m in (p["produit"], a_la(p["arome"]) if p["arome"] else None) if m)]
        # accord avec le type : « boisson ... peu sucree », « yaourt ... peu sucre »
        accord = (lambda mot: FEMININ_SINGULIER.get(mot, mot)) if p["type"] in TYPES_FEMININS else str
        if p["profil"]:
            morceaux.append(_et([accord(m) for m in p["profil"]]))
        if p["contraintes"]:
            morceaux.append(_et([accord(c) for c in p["contraintes"]]))
        return ", ".join(m for m in morceaux if m)

    def _questions(self) -> list[str]:
        """Au plus 2 questions simples sur ce qui manque."""
        p, questions = self.projet, []
        if not p["produit"]:
            questions.append("Quel type de produit voulez-vous créer ?")
        elif p["type"] in SOUS_TYPES:
            questions.append(f"Quel type de {p['type']} : {SOUS_TYPES[p['type']]} ?")
        if not p["arome"]:
            questions.append("Quelle odeur recherchez-vous ?" if p["division"] == "fragrance"
                             else "Quel goût recherchez-vous ?")
        elif not p["contraintes"] and len(questions) < 2:
            questions.append("Avez-vous une contrainte : bio, vegan, peu sucré ?")
        return questions[:2]

    def _brouillon_relance(self) -> str:
        p, marche = self.projet, (self.etude or {}).get("marche") or {}
        phrases = []
        if p["produit"]:
            phrases.append(f"J'ai bien noté votre projet : {p['produit']}.")
        courants = (marche.get("aromes_frequents") or [])[:3]
        if courants and not p["arome"]:
            phrases.append(f"Parmi les {self._nom_produits(marche['nb_produits_analyses'])} du marché "
                           "les plus proches, les arômes les plus courants sont : "
                           + _et([f"{a} ({_produits(n)})" for a, n in courants]) + ".")
        elif p["arome"]:
            phrases.append(f"J'ai bien noté le goût {p['arome']}.")
        return " ".join(phrases + self._questions())

    def _brouillon_pistes(self) -> str:
        marche, etude = self.etude["marche"], self.etude
        lignes = [f"Votre projet : {self._resume_projet()}.", f"J'ai étudié les {etude['resume']}."]
        if self.type_hors_catalogue:
            lignes.append(f"Notre catalogue ne contient pas de produits de ce type (« {self.projet['produit']} ») : "
                          "j'ai étudié les produits les plus proches, le marché étudié est donc limité.")
        if marche.get("type") and marche["type"]["produits_du_type"] < N_MARCHE:
            lignes.append(f"Le catalogue ne compte que {self._nom_produits(marche['type']['produits_du_type'])} : "
                          "l'étude est donc limitée.")
        for b in marche.get("contraintes", []):
            if not b["appliquee"]:
                lignes.append(f"Je n'ai pas pu filtrer l'étude sur « {b['contrainte']} » : {b['raison']}. "
                              f"Je reste sur les {PLURIELS.get(self.projet['type'], 'produits')} et je garde "
                              "cette contrainte dans votre brief.")
        lignes.append("Voici mes pistes :")
        for q in self._pistes_affichees():
            piste = self.pistes[q["numero"] - 1]
            lignes.append(f"{q['numero']}. {q['explication']}")
            references = self._texte_references(piste)
            if references:
                lignes.append(f"   {references}")
        for s in etude.get("solutions", []):
            lignes.append(f"Pour votre contrainte de recette : {s['code']} {s['nom']} "
                          f"({s['profil_sensoriel']} ; {s['forme']}).")
        questions = ["Laquelle vous tente ?"] + [q for q in self._questions() if "contrainte" in q]
        lignes.append(" ".join(questions[:2]))
        return "\n".join(lignes)

    def _brouillon_question(self, message: str) -> str:
        """Recuperation ciblee : origine des pistes ou chiffres des aromes cites dans la question."""
        p, phrases = self.projet, []
        marche = (self.etude or {}).get("marche") or {}
        frequence = marche.get("frequence") or {}
        numero = numero_cite(message)
        cites = self.moteur.aromes_du_texte(message, p["division"] or "flavors")
        affichees = self._pistes_affichees()
        if numero and 1 <= numero <= len(self.pistes):
            q = affichees[numero - 1]
            phrases.append(f"La piste {numero}, {q['aromes']} : {q['origine']}.")
        elif numero and self.pistes:
            phrases.append(f"Je n'ai que {len(self.pistes)} piste{'s' if len(self.pistes) > 1 else ''}.")
        for arome in cites:
            numeros = [i for i, q in enumerate(self.pistes, 1) if arome in q["aromes"]]
            if numeros:
                if numero != numeros[0]:
                    q = affichees[numeros[0] - 1]
                    phrases.append(f"L'arôme {arome} est dans la piste {numeros[0]} ({q['aromes']}) : "
                                   f"{q['origine']}.")
                continue
            phrase = f"L'arôme {arome} ne fait pas partie de mes pistes."
            if marche.get("nb_produits_analyses"):
                k = frequence.get(arome, 0)
                phrase += (f" Parmi les {self.etude['resume']}, il n'apparaît que dans {_produits(k)}"
                           if k else f" Aucun des {self.etude['resume']} ne l'utilise")
                tete = max(frequence, key=frequence.get) if frequence else None
                if tete and tete != arome:
                    phrase += f", alors que l'arôme {tete} est dans {_produits(frequence[tete])}"
                phrase += "."
            phrases.append(phrase)
            avant = [(r, f) for r, f in self.etudes_precedentes if f.get(arome)]
            if avant:
                resume, f = max(avant, key=lambda rf: rf[1][arome] / max(sum(rf[1].values()), 1))
                rang = "l'arôme le plus fréquent" if max(f, key=f.get) == arome else "très présent"
                phrases.append(f"Je l'avais cité plus tôt : c'était {rang} dans une étude précédente "
                               f"({resume}), avec {_produits(f[arome])}.")
        if not phrases and self.pistes:
            # « pourquoi cette association ? » : origine de chaque association (ou de chaque piste)
            if self.piste_choisie:
                choisies = [affichees[self.piste_choisie["numero"] - 1]]
            elif ASSOCIATION.search(normaliser(message)):
                choisies = [q for q in affichees if "+" in q["aromes"]] or affichees
            else:
                choisies = affichees
            phrases += [f"Piste {q['numero']} ({q['aromes']}) : {q['origine']}." for q in choisies]
            phrases.append(f"Ces chiffres viennent des {self.etude['resume']}.")
        if not phrases:
            phrases.append("Je n'ai pas l'information pour répondre précisément à cette question : "
                           "un conseiller Givaudan pourra vous aider.")
        if self.pistes and not self.piste_choisie:
            phrases.append(f"Laquelle de mes pistes vous tente : {self._rappel_pistes()} ?")
        return " ".join(phrases)

    def _codes_choisis(self) -> tuple[list[str], list[str]]:
        piste = self.pistes[self.piste_choisie["numero"] - 1]
        return ([r["code"] for r in piste.get("references", [])],
                [s["code"] for s in self.etude.get("solutions", [])])

    def _brouillon_choix(self) -> str:
        p, c = self.projet, self.piste_choisie
        piste = self.pistes[c["numero"] - 1]
        aromes = piste["aromes"]
        brief = [p["produit"] or "type de produit à préciser",
                 f"arômes {_et(aromes)}" if len(aromes) > 1 else f"arôme {aromes[0]}"]
        if p["profil"]:
            brief.append(f"profil {_et(p['profil'])}")
        if p["contraintes"]:
            brief.append(f"contraintes : {_et(p['contraintes'])}")
        references, solutions = self._codes_choisis()
        codes = references + solutions
        phrases = [f"Excellent choix : la piste {c['numero']}, {c['aromes']}.",
                   f"Votre brief : {', '.join(brief)}."]
        if codes:
            phrases.append(f"Références retenues : {_et(codes)}.")
        if piste.get("sans_reference"):
            phrases.append(f"Pour l'arôme {_et(piste['sans_reference'])}, il faudra une création sur mesure.")
        for s in self._sans_label(piste):
            phrases.append(f"{s['code']} ({s['arome']}) n'existe pas en version {s['label_manquant']} "
                           "dans la banque.")
        phrases.append("Je peux préparer une demande d'échantillons de ces références, pour que vous "
                       "les testiez dans votre recette. Le souhaitez-vous ?")
        return " ".join(phrases)

    def brouillon(self, intention: str, message: str) -> str:
        """Reponse factuelle ecrite par le code : seule source autorisee pour la reformulation."""
        p = self.projet
        marque = ("Je ne travaille pas à partir d'une marque : décrivez-moi plutôt le goût que vous "
                  "recherchez (fruité, vanillé, acidulé…) et le type de produit.")
        if intention == "hors_sujet" and self.marque_citee and not p["messages"]:
            return marque
        if intention in ("hors_sujet", "question"):
            accueil = ("Je vous aide à trouver l'arôme de votre futur produit. Quel produit voulez-vous "
                       "créer, et quel goût imaginez-vous ?")
            if not p["messages"]:
                return (f"Bonjour ! {accueil}" if intention == "hors_sujet" else
                        f"Je n'ai pas l'information sur ce point : un conseiller Givaudan pourra vous "
                        f"répondre. {accueil}")
            debut = ("Avec plaisir !" if intention == "hors_sujet"
                     and POLITESSE.search(_mots_normalises(message).replace(" ?", ""))
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
            texte = self._brouillon_pistes() if self.pistes else self._brouillon_relance()
            if self.marque_citee:
                texte = ("Je ne travaille pas à partir d'une marque : je me base sur le goût que vous "
                         "décrivez.\n" + texte)
            return texte
        if intention == "question_piste":
            return self._brouillon_question(message)
        if intention == "choix_piste" and self.hors_bornes:
            return (f"Je n'ai que {len(self.pistes)} piste{'s' if len(self.pistes) > 1 else ''} : "
                    f"{self._rappel_pistes()}. Laquelle choisissez-vous ?")
        if intention == "choix_piste":
            return self._brouillon_choix()
        if intention == "volume":
            suite = ("Souhaitez-vous une demande d'échantillons pour la piste choisie ?"
                     if self.piste_choisie and not self.demande_echantillons else
                     "Le récapitulatif ci-dessous est à jour." if self.demande_echantillons else
                     f"Laquelle de mes pistes vous tente : {self._rappel_pistes()} ?" if self.pistes
                     else " ".join(self._questions()))
            return f"C'est noté dans votre brief. {suite}"
        if self.demande_echantillons:
            codes = self.demande_echantillons["codes_references"] + self.demande_echantillons["codes_solutions"]
            return (f"Voici le récapitulatif de votre demande d'échantillons"
                    + (f" ({_et(codes)})" if codes else "") + ", juste en dessous. Dans ce prototype, "
                    "la demande n'est pas envoyée : transmettez ce récapitulatif à un conseiller "
                    "Givaudan. Je ne connais ni les délais, ni les quantités, ni le prix : le "
                    "conseiller vous les donnera.")
        if self.pistes:
            return ("Pour préparer une demande d'échantillons, choisissez d'abord une de mes pistes : "
                    f"{self._rappel_pistes()}.")
        return ("Pour vous proposer des échantillons, décrivez-moi d'abord votre projet : quel "
                "produit, et quel goût ?")

    def obligatoires(self, intention: str, message: str) -> list[str]:
        """Mots et codes que la reformulation doit garder (en plus des chiffres du brouillon)."""
        codes = CODE.findall(self.brouillon(intention, message))
        if intention in ("nouvelle_demande", "precision") and self.pistes:
            return sorted({a for q in self.pistes for a in q["aromes"]}) + codes
        if intention == "question_piste":
            return self.moteur.aromes_du_texte(message, self.projet["division"] or "flavors") + codes
        if intention == "choix_piste" and self.piste_choisie:
            return [*self.pistes[self.piste_choisie["numero"] - 1]["aromes"], "échantillons", *codes]
        if intention == "demande_echantillons" and self.demande_echantillons:
            return ["récapitulatif", "prototype", "conseiller", *codes]
        return codes

    def contexte(self, intention: str, message: str) -> dict:
        """Contexte factuel du tour : ce que le code sait, et le brouillon qui en est tire."""
        ctx = {"etape": intention, "projet": self._projet_affiche() if self.projet["messages"] else None,
               "pistes": self._pistes_affichees() or None,
               "solutions": (self.etude or {}).get("solutions") or None,
               "piste_choisie": self.piste_choisie,
               "etude": ({"resume": self.etude.get("resume"), "type": self.etude["marche"].get("type"),
                          "aromes_frequents": self.etude["marche"].get("aromes_frequents"),
                          "contraintes": self.etude["marche"].get("contraintes")}
                         if self.etude and self.etude["marche"] else None),
               "demande_echantillons": self.demande_echantillons
               if intention == "demande_echantillons" else None,
               "informations_inconnues": INFOS_INCONNUES,
               "brouillon": self.brouillon(intention, message),
               "mots_obligatoires": self.obligatoires(intention, message) or None}
        return {cle: valeur for cle, valeur in ctx.items() if valeur is not None}

    # --- 4 bis. Reformulation par le modele (option), verifiee --------------------------------

    def verifier(self, texte: str, source: str, obligatoires: list[str] = ()) -> dict:
        """Ajouts (chiffres, rapports « X des Y », aromes, codes, marques, monsieur/madame, envoi)
        et oublis (chiffres et mots obligatoires du brouillon)."""
        autorise = source + " " + " ".join(self.projet["messages"])
        mots = _mots(texte)
        return {"chiffres_inventes": sorted(nombres(texte) - nombres(source)),
                "couples_inventes": couples_inventes(texte, source),
                "aromes_inventes": aromes_inventes(texte, autorise),
                "codes_inventes": sorted(set(CODE.findall(texte)) - set(CODE.findall(source))),
                "types_inventes": types_inventes(texte, autorise),
                "codes_deplaces": codes_deplaces(texte, source),
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
                texte = corriger(self._chat(messages, num_predict=500).strip().strip("«»\"").strip())
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
                ("arômes ajoutés", erreurs["aromes_inventes"]),
                ("codes ajoutés", erreurs["codes_inventes"]),
                ("types de produit ajoutés", erreurs["types_inventes"]),
                ("références sous la mauvaise piste", erreurs["codes_deplaces"]),
                ("noms du commerce", erreurs["noms_du_commerce"]),
                ("chiffres oubliés", erreurs["chiffres_oublies"]),
                ("mots oubliés", erreurs["mots_oublies"]),
                ("mots interdits", erreurs["genre_suppose"]),
                ("envoi annoncé alors que rien n'est envoyé", erreurs["envoi_annonce"])) if valeurs]
            messages += [{"role": "assistant", "content": texte},
                         {"role": "user", "content": "Ta reformulation ne respecte pas la réponse "
                                                     "prévue (" + " ; ".join(problemes)
                                                     + "). Recommence en gardant chaque phrase, "
                                                       "chaque chiffre et chaque code."}]
        verification["source"] = "brouillon (vérification échouée)"
        return brouillon, verification

    # --- 5. Parcours --------------------------------------------------------------------------

    def _choisir(self, numero: int) -> None:
        self.piste_choisie = {"numero": numero, "aromes": libelle_piste(self.pistes[numero - 1])}
        self.demande_echantillons = None

    def brief_final(self) -> dict | None:
        """Brief du client avec les codes DEMO retenus (apres le choix d'une piste)."""
        if not self.piste_choisie:
            return None
        p, piste = self.projet, self.pistes[self.piste_choisie["numero"] - 1]
        references, solutions = self._codes_choisis()
        return {"division": self._projet_affiche()["division"], "type_de_produit": p["produit"],
                "piste": self.piste_choisie["numero"], "aromes": piste["aromes"],
                "profil": p["profil"], "contraintes": p["contraintes"],
                "codes_references": references, "codes_solutions": solutions,
                "creation_sur_mesure": piste.get("sans_reference", []),
                "references_sans_label": self._sans_label(piste), "volume": p["volume"],
                "brief_du_client": " / ".join(p["messages"])}

    def _preparer_echantillons(self) -> None:
        self.demande_echantillons = {"statut": "brouillon, non envoyé (prototype)",
                                     "date": date.today().isoformat(), **self.brief_final()}

    def repondre(self, message: str, reformuler: bool | None = None,
                 piste_id: str | None = None) -> dict:
        """reformuler : None = reglage de l'assistant ; True/False pour ce message seulement.
        piste_id : choix de cette piste, quel que soit le message (bouton du front) ; leve
        ValueError si aucune piste actuelle n'a cet identifiant."""
        reformuler = self.reformuler if reformuler is None else reformuler
        self.marque_citee = False
        if piste_id is not None:
            numero = self.numero_de_piste(piste_id)
            if numero is None:
                raise ValueError(f"piste_id inconnu : {piste_id!r} (pistes actuelles : "
                                 f"{[id_piste(p['aromes']) for p in self.pistes]})")
            analyse = {"intention": "choix_piste", "numero": numero,
                       "trace": {"modele_appele": False, "intention": "choix_piste (piste_id)"}}
            message = message or f"je choisis la piste {numero}"
        else:
            analyse = self.analyser(message)
            self.marque_citee = bool(analyse.get("marques"))
        intention = analyse["intention"]
        self.hors_bornes = None
        seulement_volume = intention == "precision" and analyse.get("volume") and not any(
            analyse.get(cle) for cle in ("type", "arome", "application", "contraintes", "retraits",
                                         "profil"))
        if intention == "nouvelle_demande":
            self.reinitialiser()
        if seulement_volume:  # le volume complete le brief sans relancer l'etude ni le choix
            self.projet["volume"] = analyse["volume"]
            self.projet["messages"].append(message)
            if self.demande_echantillons:
                self._preparer_echantillons()
        elif intention in ("nouvelle_demande", "precision"):
            self._mettre_a_jour(message, analyse)
            self._lancer_etude()
        elif intention == "choix_piste" and not 1 <= analyse["numero"] <= len(self.pistes):
            self.hors_bornes = analyse["numero"]  # « piste 9 » : rien n'est choisi
        elif intention == "choix_piste":
            self._choisir(analyse["numero"])
        elif intention == "demande_echantillons" and self.piste_choisie:
            self._preparer_echantillons()
        contexte = self.contexte("volume" if seulement_volume else intention, message)
        if reformuler:
            texte, verification = self.rediger(message, contexte["brouillon"],
                                               contexte.get("mots_obligatoires") or [])
        else:
            texte, verification = contexte["brouillon"], {"tentatives": 0, "rejets": [],
                                                          "source": "brouillon (mode rapide)"}
        self.historique += [{"role": "user", "content": message},
                            {"role": "assistant", "content": texte}]
        p = self.projet
        compris = {"division": p["division"], "type_produit": p["produit"], "arome": p["arome"],
                   "aromes": ([p["arome"]] if p["arome"] else [])
                   + [a for a in p["aromes_cites"] if a != p["arome"]],
                   "contraintes": list(p["contraintes"]), "profil": list(p["profil"])}
        return {"intention": intention, "etape": self.etape, "compris": compris,
                "texte": texte, "projet": self._projet_affiche(),
                "pistes": self._pistes_affichees(), "solutions": (self.etude or {}).get("solutions", []),
                "piste_choisie": self.piste_choisie, "brief_final": self.brief_final(),
                # le brouillon reste renvoye tant qu'il est valide (objet complet)
                "demande_echantillons": self.demande_echantillons,
                "contexte": contexte, "verification": verification,
                "etapes": {**analyse["trace"], **((self.etude or {}).get("etapes") or {})},
                "version_modele": VERSION_V22, "attribution": ATTRIBUTION}
