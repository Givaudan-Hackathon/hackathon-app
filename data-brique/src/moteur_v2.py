"""Moteur V2 : brief client -> division + arome principal + top k produits.

Meme format de sortie que MoteurV1 (cles division, scores_division, top), plus arome et mode.
1. llama3.2:3b (Ollama) extrait {application, division, aromes} du brief ; on garde la division
   et le premier arome (cf. benchmark/resultats.md : les aromes suivants sont souvent inventes).
   "application" est demandee en premier pour que le modele nomme le produit avant de choisir la
   division (sans elle, "une petite creme au gout d'enfance" partait en fragrance).
2. Flavors : bge-m3 compare le brief enrichi de l'arome aux vecteurs du catalogue (cosinus).
   Fragrance : TF-IDF de la V1.
Repli : si Ollama ne repond pas, chaque etape concernee retombe sur la V1 (mots-cles, TF-IDF).
"""
import hashlib
import json
import os
import time
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
        "division": {"type": "string", "enum": ["flavors", "fragrance"]},
        "aromes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["application", "division", "aromes"],
}

# prompt du benchmark sans la cle contraintes ni l'exemple "biscuit" (recopie tel quel par les
# modeles qwen), avec une regle pour les mots ambigus comme "creme"
SYSTEME = """Tu analyses les demandes de clients de Givaudan, qui crée des arômes alimentaires \
(division "flavors") et des parfums pour l'hygiène, la cosmétique et la parfumerie \
(division "fragrance"). Les clients sont de petites marques qui décrivent leur projet avec leurs mots.
Réponds uniquement par un objet JSON avec les clés :
- "application" : le type de produit final, en quelques mots ;
- "division" : "flavors" si le produit final se mange ou se boit, "fragrance" s'il se sent ou \
s'applique sur le corps ; un mot comme "crème" peut désigner les deux : le client qui parle de \
"goût" ou de "saveur" veut un arôme alimentaire, celui qui parle d'"odeur" ou de ce qui "sent" \
veut un parfum ;
- "aromes" : les arômes ou notes recherchés, en un ou deux mots chacun, en français, le principal \
en premier ; si le client évoque une sensation sans nommer d'arôme, donne l'arôme le plus probable."""


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

    def comprendre(self, brief: str) -> tuple[str, str | None]:
        """llama3.2:3b -> (division, arome principal) ; leve OllamaIndisponible."""
        reponse = self._post(
            "/api/chat", self.delai_llm, model=MODELE_LLM, stream=False, format=SCHEMA,
            keep_alive="30m", options={"temperature": 0, "seed": 42},
            messages=[{"role": "system", "content": SYSTEME}, {"role": "user", "content": brief}])
        try:
            sortie = json.loads(reponse["message"]["content"])
            division = sortie["division"]
            aromes = [a.strip() for a in sortie.get("aromes", []) if isinstance(a, str) and a.strip()]
        except (KeyError, TypeError, ValueError, AttributeError) as erreur:
            raise OllamaIndisponible(f"sortie LLM invalide : {erreur}") from erreur
        if division not in ("flavors", "fragrance"):
            raise OllamaIndisponible(f"division inattendue : {division!r}")
        return division, (aromes[0] if aromes else None)

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

    def recommander(self, brief: str, k: int = 5) -> dict:
        """Sortie de MoteurV1 + arome (principal, ou None), mode et etapes.

        mode : "v2" (LLM + recherche V2), "v2_partiel" (LLM ok mais bge-m3 indisponible :
        TF-IDF V1 sur la division du LLM), "repli_v1" (Ollama indisponible : V1 complete).
        """
        _, scores_division = detecter_division(brief)  # renvoye pour compatibilite avec la V1
        try:
            division, arome = self.comprendre(brief)
        except OllamaIndisponible:
            return {**self.v1.recommander(brief, k), "arome": None, "mode": "repli_v1",
                    "etapes": {"comprehension": "mots-cles v1", "recherche": "tfidf v1"}}

        etapes, mode = {"comprehension": MODELE_LLM}, "v2"
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
        return {"division": division, "scores_division": scores_division, "top": top,
                "arome": arome, "mode": mode, "etapes": etapes}
