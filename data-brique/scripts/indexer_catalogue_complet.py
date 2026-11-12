"""Indexation bge-m3 du catalogue Flavors complet (8 943 produits), avec reprise.

Usage (depuis data-brique/, Ollama lance) : .venv/Scripts/python scripts/indexer_catalogue_complet.py
Long (~1 h 30 sur le CPU de l'equipe). Meme texte indexe et meme cle de cache que
MoteurV2.indexer() : le fichier final benchmark/cache/bge-m3_complet.npz est lu tel quel par
MoteurV2(catalogue="complet"). Un point de reprise (bge-m3_complet.partiel.npz) est ecrit tous
les 20 lots : relancer le script reprend ou il s'etait arrete.
"""
import sys
import time

import numpy as np

sys.path.insert(0, ".")
from src.moteur_v2 import MoteurV2  # noqa: E402

TAILLE_LOT = 32
POINT_REPRISE = 20  # lots

moteur = MoteurV2(catalogue="complet")
cle = moteur._cle_cache()
partiel = moteur.fichier_vecteurs.with_name(moteur.fichier_vecteurs.stem + ".partiel.npz")
morceaux, secondes = [], 0.0
if partiel.exists() and str(np.load(partiel)["cle"]) == cle:
    donnees = np.load(partiel)
    morceaux, secondes = [donnees["vecteurs"]], float(donnees["secondes"])
fait = sum(len(m) for m in morceaux)
total = len(moteur.textes)
print(f"{total} produits, reprise a {fait}", flush=True)
debut = time.perf_counter()
for i, depart in enumerate(range(fait, total, TAILLE_LOT), 1):
    morceaux.append(moteur._embed(moteur.textes[depart:depart + TAILLE_LOT]))
    fait = min(depart + TAILLE_LOT, total)
    if i % POINT_REPRISE == 0 or fait == total:
        ecoule = secondes + time.perf_counter() - debut
        np.savez(partiel, vecteurs=np.vstack(morceaux), secondes=ecoule, cle=cle)
        print(f"{fait}/{total} ({fait / total:.0%}) · {ecoule / 60:.1f} min", flush=True)
ecoule = secondes + time.perf_counter() - debut
np.savez(moteur.fichier_vecteurs, vecteurs=np.vstack(morceaux), secondes=ecoule, cle=cle)
partiel.unlink()
print(f"termine : {moteur.fichier_vecteurs} ({ecoule / 60:.1f} min)", flush=True)
