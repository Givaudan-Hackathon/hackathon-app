"""Moteur baseline V1 : brief client -> division + top k produits.

Code partage par notebooks/baseline_v1.ipynb et api/main.py.
1. Division (Flavors / Fragrance) par comptage de mots-cles dans le brief.
2. Recherche TF-IDF du brief contre product_name + ingredients_text + query_category,
   restreinte a la division detectee, similarite cosinus.
"""
import re
import unicodedata
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

VERSION_MODELE = "baseline-v1"
CATALOGUE_DEFAUT = Path(__file__).resolve().parents[1] / "data" / "processed" / "sample_v1.csv"

URL_PRODUIT = {
    "off": "https://world.openfoodfacts.org/product/{code}",
    "obf": "https://world.openbeautyfacts.org/product/{code}",
}

MOTS_CLES = {
    "flavors": [
        "arome", "aromatise", "gout", "saveur", "boisson", "proteine", "yaourt", "lait",
        "dessert", "sirop", "soda", "the glace", "cafe", "smoothie", "creme dessert",
        "vanille", "fraise", "chocolat", "menthe", "caramel", "sportif",
    ],
    "fragrance": [
        "parfum", "senteur", "odeur", "fragrance", "savon", "deodorant", "gel douche",
        "douche", "shampoing", "cosmetique", "eau de toilette", "boise", "floral", "musc",
        "ambre", "frais", "fraiche", "hygiene", "peau",
    ],
}
# mots a matcher en entier : "frais" ne doit pas compter dans "fraise"
MOTS_ENTIERS = {"frais"}

STOP_FR = [
    "a", "au", "aux", "avec", "ce", "de", "des", "du", "en", "et", "la", "le", "les", "pour",
    "sur", "un", "une", "par", "base", "gamme", "gout",
]

COLONNES_RESULTAT = ["code", "product_name", "brands", "query_category", "format", "source",
                     "url_produit", "score"]


def normaliser(texte: str) -> str:
    """Minuscules, sans accents."""
    texte = unicodedata.normalize("NFKD", str(texte).lower())
    return "".join(ch for ch in texte if not unicodedata.combining(ch))


MOTIFS = {
    div: [re.compile(r"\b" + re.escape(mot) + (r"\b" if mot in MOTS_ENTIERS else ""))
          for mot in mots]
    for div, mots in MOTS_CLES.items()
}


def detecter_division(brief: str) -> tuple[str, dict[str, int]]:
    """Division ayant le plus de mots-cles presents ; egalite -> 'indeterminee'."""
    texte = normaliser(brief)
    scores = {div: sum(bool(m.search(texte)) for m in motifs) for div, motifs in MOTIFS.items()}
    if scores["flavors"] == scores["fragrance"]:
        return "indeterminee", scores
    return max(scores, key=scores.get), scores


def texte_produit(df: pd.DataFrame) -> pd.Series:
    return (
        df["product_name"].fillna("") + " "
        + df["ingredients_text"].fillna("") + " "
        + df["query_category"].fillna("").str.replace("_", " ")
    ).map(normaliser)


class MoteurV1:
    """Un index TF-IDF par division, pour que l'IDF reflete le vocabulaire de chacune."""

    version = VERSION_MODELE

    def __init__(self, chemin_catalogue: Path = CATALOGUE_DEFAUT):
        catalogue = pd.read_csv(chemin_catalogue, dtype=str)
        catalogue["url_produit"] = [URL_PRODUIT[s].format(code=c)
                                    for s, c in zip(catalogue["source"], catalogue["code"])]
        self.index = {}
        for division, df_div in catalogue.groupby("division"):
            vectoriseur = TfidfVectorizer(
                ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode",
                stop_words=STOP_FR,
            )
            matrice = vectoriseur.fit_transform(texte_produit(df_div))
            self.index[division] = (df_div.reset_index(drop=True), vectoriseur, matrice)

    def recommander(self, brief: str, k: int = 5) -> dict:
        division, scores_division = detecter_division(brief)
        # division indeterminee : recherche dans les deux index, meilleurs scores gardes
        divisions = list(self.index) if division == "indeterminee" else [division]
        resultats = []
        for div in divisions:
            df_div, vectoriseur, matrice = self.index[div]
            sims = cosine_similarity(vectoriseur.transform([normaliser(brief)]), matrice).ravel()
            ordre = sims.argsort()[::-1][:k]
            top = df_div.iloc[ordre].copy()
            top["score"] = sims[ordre].round(3)
            resultats.append(top)
        top_k = pd.concat(resultats).sort_values("score", ascending=False).head(k)
        return {
            "division": division,
            "scores_division": scores_division,
            "top": top_k[COLONNES_RESULTAT].reset_index(drop=True),
        }
