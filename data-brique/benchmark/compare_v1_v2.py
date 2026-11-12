"""Comparaison rapide V1 / V2 sur les 15 briefs de benchmark/briefs_test.csv.

Usage (depuis data-brique/, Ollama lance) : .venv/Scripts/python benchmark/compare_v1_v2.py
Sortie : benchmark/sorties/comparaison_v1_v2.csv (une ligne par brief et par moteur).
"""
import sys
import time
from pathlib import Path

import pandas as pd

DOSSIER = Path(__file__).resolve().parent
sys.path.insert(0, str(DOSSIER.parent))  # racine data-brique/ pour importer src
from benchmark.run_benchmark import arome_correct  # noqa: E402
from src.moteur_v1 import MoteurV1  # noqa: E402
from src.moteur_v2 import MoteurV2  # noqa: E402


def main() -> None:
    briefs = pd.read_csv(DOSSIER / "briefs_test.csv", keep_default_na=False)
    moteurs = {"v1": MoteurV1(), "v2": MoteurV2()}
    lignes = []
    for nom, moteur in moteurs.items():
        moteur.recommander("chargement des modeles", 1)  # exclu des temps
        for b in briefs.itertuples():
            debut = time.perf_counter()
            res = moteur.recommander(b.brief, 5)
            secondes = time.perf_counter() - debut
            cats = res["top"]["query_category"].tolist()
            arome = res.get("arome")
            lignes.append({
                "moteur": nom, "id": b.id, "brief": b.brief,
                "division_attendue": b.division_attendue, "division": res["division"],
                "division_ok": res["division"] == b.division_attendue,
                "arome": arome, "arome_ok": arome_correct([arome], b.arome_attendu) if arome else False,
                "categorie_attendue": b.query_category_attendue, "top1": cats[0],
                "rang1_ok": cats[0] == b.query_category_attendue,
                "top5_ok": b.query_category_attendue in cats,
                "precision_top5": sum(c == b.query_category_attendue for c in cats) / len(cats),
                "mode": res.get("mode", "v1"), "secondes": round(secondes, 2),
                "top3": " / ".join(res["top"]["product_name"].fillna("?").head(3)),
            })
    df = pd.DataFrame(lignes)
    (DOSSIER / "sorties").mkdir(exist_ok=True)
    df.to_csv(DOSSIER / "sorties" / "comparaison_v1_v2.csv", index=False, lineterminator="\n")

    flavors = df["division_attendue"] == "flavors"
    resume = pd.DataFrame({
        "division correcte (15)": df.groupby("moteur")["division_ok"].mean(),
        "arome principal (15)": df.groupby("moteur")["arome_ok"].mean(),
        "categorie rang 1 (12 Flavors)": df[flavors].groupby("moteur")["rang1_ok"].mean(),
        "categorie top 5 (12 Flavors)": df[flavors].groupby("moteur")["top5_ok"].mean(),
        "precision top 5 (12 Flavors)": df[flavors].groupby("moteur")["precision_top5"].mean(),
        "categorie rang 1 (3 Fragrance)": df[~flavors].groupby("moteur")["rang1_ok"].mean(),
    }).mul(100).round(0)
    resume["s par brief"] = df.groupby("moteur")["secondes"].mean().round(2)
    print(resume.T.to_string())
    print()
    print(df.pivot(index="id", columns="moteur", values=["division", "top1"]).to_string())


if __name__ == "__main__":
    main()
