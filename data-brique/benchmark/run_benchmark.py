"""Benchmark des modeles Ollama appliques au moteur : embeddings (recherche) et LLM (extraction).

Usage (depuis data-brique/, Ollama lance localement) :
    .venv/Scripts/python benchmark/run_benchmark.py
Variable optionnelle : OLLAMA_URL (defaut http://127.0.0.1:11434 ; sous Windows, "localhost"
fait d'abord une tentative IPv6 qui ajoute ~2 s a chaque requete).

1. Recherche sur le catalogue Flavors de sample_v1.csv : TF-IDF baseline (src/moteur_v1.py)
   contre nomic-embed-text, bge-m3, mxbai-embed-large. Vecteurs du catalogue en cache dans
   benchmark/cache/ (cle = modele + digest Ollama + textes indexes).
2. Extraction brief -> JSON {division, application, aromes, contraintes} par qwen2.5:1.5b,
   qwen2.5:3b, llama3.2:3b (schema JSON impose a Ollama, temperature 0).
Sorties : benchmark/sorties/ (mesures.json, mesures.md, details_recherche.csv, details_llm.csv).
"""
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import psutil
import requests
from jsonschema import Draft202012Validator
from sklearn.metrics.pairwise import cosine_similarity

DOSSIER = Path(__file__).resolve().parent
sys.path.insert(0, str(DOSSIER.parent))  # racine data-brique/ pour importer src
from src.moteur_v1 import MoteurV1, detecter_division, normaliser  # noqa: E402

OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
CACHE = DOSSIER / "cache"
SORTIES = DOSSIER / "sorties"
BRIEFS = DOSSIER / "briefs_test.csv"

K = 5
LONGUEUR_INGREDIENTS = 300
TAILLE_LOT = 32
GRAINE = 42

# prefixes (requete, document) recommandes par les fiches des modeles sur ollama.com
MODELES_EMBEDDING = {
    "nomic-embed-text": ("search_query: ", "search_document: "),
    "bge-m3": ("", ""),
    "mxbai-embed-large": ("Represent this sentence for searching relevant passages: ", ""),
}
MODELES_LLM = ["qwen2.5:1.5b", "qwen2.5:3b", "llama3.2:3b"]

SCHEMA = {
    "type": "object",
    "properties": {
        "division": {"type": "string", "enum": ["flavors", "fragrance"]},
        "application": {"type": "string"},
        "aromes": {"type": "array", "items": {"type": "string"}},
        "contraintes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["division", "application", "aromes", "contraintes"],
}
VALIDATEUR = Draft202012Validator(SCHEMA)

SYSTEME = """Tu analyses les demandes de clients de Givaudan, qui crée des arômes alimentaires \
(division "flavors") et des parfums pour l'hygiène, la cosmétique et la parfumerie \
(division "fragrance"). Les clients sont de petites marques qui décrivent leur projet avec leurs mots.
Réponds uniquement par un objet JSON avec les clés :
- "division" : "flavors" si le produit final se mange ou se boit, "fragrance" s'il se sent ou \
s'applique sur le corps ;
- "application" : le type de produit final, en quelques mots (ex. "biscuit", "shampoing") ;
- "aromes" : les arômes ou notes recherchés, en un ou deux mots chacun, en français, le principal \
en premier ; si le client évoque une sensation sans nommer d'arôme, donne l'arôme le plus probable ;
- "contraintes" : les autres exigences (sucre, origine, régime, cible, prix...), liste vide s'il \
n'y en a pas."""


# --- Ollama -------------------------------------------------------------------------------------

def ollama(chemin: str, essais: int = 4, **corps) -> dict:
    """POST vers Ollama ; reessaie les erreurs 500 (chargement d'un modele faute de RAM libre)."""
    for essai in range(essais):
        reponse = requests.post(f"{OLLAMA}{chemin}", json=corps, timeout=900)
        if reponse.status_code != 500 or essai == essais - 1:
            reponse.raise_for_status()
            return reponse.json()
        print(f"  Ollama 500 ({reponse.text[:120]}) -> nouvel essai dans {10 * 2**essai} s")
        time.sleep(10 * 2**essai)


def decharger(modele: str) -> None:
    """Libere la RAM entre deux modeles pour que les mesures ne se gênent pas."""
    route = "/api/embed" if modele in MODELES_EMBEDDING else "/api/generate"
    champ = {"input": ""} if modele in MODELES_EMBEDDING else {"prompt": ""}
    try:
        ollama(route, model=modele, keep_alive=0, **champ)
    except requests.RequestException:
        pass


def vram_utilisee(modele: str) -> int | None:
    for m in requests.get(f"{OLLAMA}/api/ps", timeout=10).json().get("models", []):
        if m["name"].startswith(modele):
            return m.get("size_vram", 0)
    return None


def embed(modele: str, textes: list[str]) -> np.ndarray:
    vecteurs = np.asarray(ollama("/api/embed", model=modele, input=textes, truncate=True,
                                 keep_alive="10m")["embeddings"], dtype=np.float32)
    return vecteurs / np.linalg.norm(vecteurs, axis=1, keepdims=True)


# --- Configuration ------------------------------------------------------------------------------

def _powershell(commande: str) -> str:
    try:
        return subprocess.run(["powershell", "-NoProfile", "-Command", commande],
                              capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def config_pc() -> dict:
    windows = platform.system() == "Windows"
    cpu = _powershell("(Get-CimInstance Win32_Processor).Name") if windows else ""
    gpu = _powershell("(Get-CimInstance Win32_VideoController).Name") if windows else ""
    return {
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "cpu": cpu or platform.processor(),
        "coeurs_physiques": psutil.cpu_count(logical=False),
        "threads": psutil.cpu_count(logical=True),
        "ram_go": round(psutil.virtual_memory().total / 1024**3, 1),
        "gpu": gpu or "inconnu",
        "python": platform.python_version(),
        "ollama": requests.get(f"{OLLAMA}/api/version", timeout=10).json()["version"],
    }


def digests() -> dict[str, str]:
    modeles = requests.get(f"{OLLAMA}/api/tags", timeout=10).json()["models"]
    return {m["name"].removesuffix(":latest"): m["digest"] for m in modeles}


# --- Partie 1 : recherche -----------------------------------------------------------------------

def texte_index(df: pd.DataFrame) -> list[str]:
    """Nom + categorie + 300 premiers caracteres des ingredients."""
    return (df["product_name"].fillna("") + " | " + df["query_category"].str.replace("_", " ")
            + " | " + df["ingredients_text"].fillna("").str[:LONGUEUR_INGREDIENTS]).tolist()


def index_embedding(modele: str, textes: list[str], prefixe: str, digest: str) -> tuple:
    """Vecteurs du catalogue (cache disque) et temps d'indexation mesure au calcul."""
    cle = hashlib.sha256("\n".join([modele, digest, prefixe, *textes]).encode()).hexdigest()
    fichier = CACHE / f"{modele.replace(':', '_')}.npz"
    if fichier.exists():
        cache = np.load(fichier)
        if str(cache["cle"]) == cle:
            return cache["vecteurs"], float(cache["secondes"]), True
    morceaux, debut = [], time.perf_counter()
    for i in range(0, len(textes), TAILLE_LOT):
        morceaux.append(embed(modele, [prefixe + t for t in textes[i:i + TAILLE_LOT]]))
    secondes = time.perf_counter() - debut
    vecteurs = np.vstack(morceaux)
    CACHE.mkdir(exist_ok=True)
    np.savez(fichier, vecteurs=vecteurs, secondes=secondes, cle=cle)
    return vecteurs, secondes, False


def evaluer_recherche(nom: str, chercher, briefs: pd.DataFrame, catalogue: pd.DataFrame,
                      details: list) -> dict:
    """chercher(brief) -> similarites sur le catalogue ; mesure le temps de chaque requete."""
    temps, top1, top5, precision, arome5 = [], [], [], [], []
    for b in briefs.itertuples():
        debut = time.perf_counter()
        sims = chercher(b.brief)
        ordre = np.argsort(-sims)[:K]
        temps.append(time.perf_counter() - debut)
        cats = catalogue["query_category"].to_numpy()[ordre]
        noms = catalogue["product_name"].fillna("").map(normaliser).to_numpy()[ordre]
        top1.append(cats[0] == b.query_category_attendue)
        top5.append(b.query_category_attendue in cats)
        precision.append(float(np.mean(cats == b.query_category_attendue)))
        arome5.append(any(a in n for a in b.arome_attendu.split("|") for n in noms))
        for rang, i in enumerate(ordre, 1):
            ligne = catalogue.iloc[i]
            details.append({"modele": nom, "id": b.id, "brief": b.brief, "rang": rang,
                            "code": ligne["code"], "product_name": ligne["product_name"],
                            "query_category": ligne["query_category"],
                            "attendue": b.query_category_attendue, "score": round(float(sims[i]), 4)})
    return {"categorie_top5_pct": 100 * np.mean(top5), "categorie_rang1_pct": 100 * np.mean(top1),
            "precision_top5_pct": 100 * np.mean(precision), "arome_dans_nom_top5_pct": 100 * np.mean(arome5),
            "ms_par_requete": 1000 * np.mean(temps)}


def partie_recherche(briefs: pd.DataFrame, digest: dict) -> tuple[list, list]:
    briefs = briefs[briefs["division_attendue"] == "flavors"]
    debut = time.perf_counter()
    moteur = MoteurV1()
    secondes_tfidf = time.perf_counter() - debut
    catalogue, vectoriseur, matrice = moteur.index["flavors"]
    print(f"[recherche] catalogue Flavors : {len(catalogue)} produits, {len(briefs)} briefs")

    lignes, details = [], []
    res = evaluer_recherche(
        "tfidf (baseline)",
        lambda brief: cosine_similarity(vectoriseur.transform([normaliser(brief)]), matrice).ravel(),
        briefs, catalogue, details)
    lignes.append({"modele": "tfidf (baseline)", "texte_indexe": "complet",
                   "indexation_s": secondes_tfidf, "cache": False, "chargement_s": 0.0,
                   "vram_octets": 0, **res})
    print(f"  tfidf : {res}")

    textes = texte_index(catalogue)
    for modele, (prefixe_requete, prefixe_document) in MODELES_EMBEDDING.items():
        debut = time.perf_counter()
        embed(modele, ["chargement"])  # chargement du modele exclu des mesures
        chargement = time.perf_counter() - debut
        vram = vram_utilisee(modele)
        vecteurs, secondes, en_cache = index_embedding(modele, textes, prefixe_document,
                                                       digest[modele])
        res = evaluer_recherche(
            modele, lambda brief: vecteurs @ embed(modele, [prefixe_requete + brief])[0],
            briefs, catalogue, details)
        lignes.append({"modele": modele, "texte_indexe": f"nom + categorie + {LONGUEUR_INGREDIENTS} car.",
                       "indexation_s": secondes, "cache": en_cache, "chargement_s": chargement,
                       "vram_octets": vram, **res})
        print(f"  {modele} : indexation {secondes:.1f} s (cache={en_cache}) {res}")
        decharger(modele)
    return lignes, details


# --- Partie 2 : LLM -----------------------------------------------------------------------------

def _mots(texte: str) -> set[str]:
    """Mots d'un arome sans accents ni marque du pluriel/feminin (fleurie = fleuri, agrumes = agrume)."""
    return {mot.rstrip("sxe") for mot in normaliser(texte).replace("-", " ").split()} - {"", "de", "d'"}


def arome_correct(aromes, attendu: str) -> bool:
    """Arome principal (1er de la liste) = un des aromes attendus, par mots entiers
    ("noix de coco" contient "coco" ; "anis" ne correspond pas a "vanille")."""
    if not isinstance(aromes, list) or not aromes or not isinstance(aromes[0], str):
        return False
    principal = _mots(aromes[0])
    return bool(principal) and any(_mots(a) <= principal or principal <= _mots(a)
                                   for a in attendu.split("|"))


def extraire(modele: str, brief: str) -> tuple[str, float]:
    debut = time.perf_counter()
    reponse = ollama("/api/chat", model=modele, stream=False, format=SCHEMA, keep_alive="10m",
                     options={"temperature": 0, "seed": GRAINE},
                     messages=[{"role": "system", "content": SYSTEME},
                               {"role": "user", "content": brief}])
    return reponse["message"]["content"], time.perf_counter() - debut


def partie_llm(briefs: pd.DataFrame) -> tuple[list, list]:
    lignes, details = [], []
    # reference : detection par mots-cles de la baseline
    divisions = [detecter_division(b)[0] for b in briefs["brief"]]
    lignes.append({"modele": "mots-cles (baseline)", "chargement_s": 0.0, "vram_octets": 0,
                   "division_pct": 100 * np.mean(np.array(divisions) == briefs["division_attendue"]),
                   "json_valide_pct": None, "arome_principal_pct": None, "s_par_brief": 0.0})
    for modele in MODELES_LLM:
        debut = time.perf_counter()
        extraire(modele, "test")  # chargement du modele exclu des mesures
        chargement = time.perf_counter() - debut
        vram = vram_utilisee(modele)
        ok_div, ok_json, ok_arome, temps = [], [], [], []
        for b in briefs.itertuples():
            brut, secondes = extraire(modele, b.brief)
            try:
                sortie = json.loads(brut)
                valide = not list(VALIDATEUR.iter_errors(sortie))
            except json.JSONDecodeError:
                sortie, valide = {}, False
            sortie = sortie if isinstance(sortie, dict) else {}
            ok_json.append(valide)
            ok_div.append(sortie.get("division") == b.division_attendue)
            ok_arome.append(arome_correct(sortie.get("aromes"), b.arome_attendu))
            temps.append(secondes)
            details.append({"modele": modele, "id": b.id, "brief": b.brief, "sortie": brut,
                            "json_valide": valide, "division_ok": ok_div[-1],
                            "arome_attendu": b.arome_attendu, "arome_ok": ok_arome[-1],
                            "secondes": round(secondes, 2)})
        ligne = {"modele": modele, "chargement_s": chargement, "vram_octets": vram,
                 "division_pct": 100 * np.mean(ok_div), "json_valide_pct": 100 * np.mean(ok_json),
                 "arome_principal_pct": 100 * np.mean(ok_arome), "s_par_brief": np.mean(temps)}
        lignes.append(ligne)
        print(f"[llm] {ligne}")
        decharger(modele)
    return lignes, details


# --- Rapport ------------------------------------------------------------------------------------

def _tableau(df: pd.DataFrame) -> str:
    entete = "| " + " | ".join(df.columns) + " |"
    separateur = "| " + " | ".join("---" for _ in df.columns) + " |"
    corps = ["| " + " | ".join("" if pd.isna(v) else str(v) for v in ligne) + " |"
             for ligne in df.itertuples(index=False)]
    return "\n".join([entete, separateur, *corps])


def ecrire_markdown(mesures: dict, det_recherche: pd.DataFrame, det_llm: pd.DataFrame) -> None:
    rech = pd.DataFrame(mesures["recherche"]).round(1)
    llm = pd.DataFrame(mesures["llm"]).round(1)
    lignes = [f"# Mesures brutes du benchmark ({mesures['date']})", "",
              "Fichier généré par `benchmark/run_benchmark.py`, ne pas éditer.", "",
              "## Configuration", "", _tableau(pd.DataFrame([mesures["config"]]).T.reset_index()
                                                 .set_axis(["clé", "valeur"], axis=1)), "",
              "## Recherche (briefs Flavors)", "", _tableau(rech), "",
              "## Extraction LLM (15 briefs)", "", _tableau(llm), "",
              "## Top 3 par brief", ""]
    for (id_, brief), groupe in det_recherche[det_recherche["rang"] <= 3].groupby(["id", "brief"]):
        lignes += [f"### {id_}. {brief}", ""]
        lignes.append(_tableau(groupe[["modele", "rang", "product_name", "query_category", "score"]]))
        lignes.append("")
    lignes += ["## Sorties LLM", ""]
    lignes.append(_tableau(det_llm[["id", "modele", "sortie", "division_ok", "arome_ok", "secondes"]]
                           .assign(sortie=lambda d: d["sortie"].str.replace("|", "/")
                                   .str.replace("\n", " "))))
    (SORTIES / "mesures.md").write_text("\n".join(lignes) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    briefs = pd.read_csv(BRIEFS, dtype={"id": int}, keep_default_na=False)
    SORTIES.mkdir(exist_ok=True)
    mesures = {"date": datetime.now().isoformat(timespec="seconds"), "config": config_pc()}
    print(mesures["config"])
    digest = digests()
    manquants = [m for m in [*MODELES_EMBEDDING, *MODELES_LLM] if m not in digest]
    if manquants:
        sys.exit(f"Modeles absents d'Ollama : {manquants} -> ollama pull <modele>")

    mesures["recherche"], det_recherche = partie_recherche(briefs, digest)
    mesures["llm"], det_llm = partie_llm(briefs)
    mesures["digests"] = {m: digest[m] for m in [*MODELES_EMBEDDING, *MODELES_LLM]}

    det_recherche, det_llm = pd.DataFrame(det_recherche), pd.DataFrame(det_llm)
    det_recherche.to_csv(SORTIES / "details_recherche.csv", index=False, lineterminator="\n")
    det_llm.to_csv(SORTIES / "details_llm.csv", index=False, lineterminator="\n")
    (SORTIES / "mesures.json").write_text(
        json.dumps(mesures, ensure_ascii=False, indent=2, default=float) + "\n",
        encoding="utf-8", newline="\n")
    ecrire_markdown(mesures, det_recherche, det_llm)
    print(f"Sorties ecrites dans {SORTIES}")


if __name__ == "__main__":
    main()
