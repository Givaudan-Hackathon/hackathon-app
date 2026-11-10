"""Rapport qualite de l'echantillon v1 -> docs/quality_report.md

Usage : python scripts/quality_report.py
"""
from pathlib import Path

import pandas as pd

import criteres as c

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "processed" / "sample_v1.csv", dtype=str)
RX = {"flavors": c.AROME_RX, "fragrance": c.PARFUM_RX}
CHAMPS = ["product_name", "brands", "categories_tags", "labels_tags", "ingredients_text"]


def rempli(s: pd.Series) -> pd.Series:
    return s.fillna("").str.strip().ne("")


def mention(s: pd.Series, division: str) -> float:
    return s.fillna("").str.contains(RX[division], regex=True).mean()


lines = ["# Rapport qualite — echantillon v1", "",
         f"{len(df)} produits uniques (`data/processed/sample_v1.csv`).", ""]
for division, g in df.groupby("division"):
    ing = g["ingredients_text"].fillna("")
    lines += [f"## {division} ({len(g)} produits)", "",
              "| champ | taux de remplissage |", "|---|---|"]
    lines += [f"| {col} | {rempli(g[col]).mean():.0%} |" for col in CHAMPS]
    lines += ["",
              f"- Mention arome / parfum dans les ingredients : **{mention(ing, division):.0%}**",
              f"- Longueur mediane ingredients_text : {int(ing.str.len().median())} caracteres",
              "", "| query_category | produits | marque remplie | mention arome / parfum |",
              "|---|---|---|---|"]
    for cat, gc in g.groupby("query_category"):
        lines.append(f"| {cat} | {len(gc)} | {rempli(gc['brands']).mean():.0%} "
                     f"| {mention(gc['ingredients_text'], division):.0%} |")
    lines.append("")
    if division == "flavors":
        fmt = g.loc[g["query_category"] == "boissons_proteinees", "format"].value_counts()
        lines += ["- Format des boissons proteinees : "
                  + ", ".join(f"{k} {n}" for k, n in fmt.items())
                  + " (heuristique nom + tags, quelques erreurs observees)", ""]

out = ROOT / "docs" / "quality_report.md"
out.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
