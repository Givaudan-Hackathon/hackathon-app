"""Rapport qualite de l'echantillon OFF/OBF -> docs/quality_report.md"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "raw" / "off_obf_sample.csv", dtype=str)

# mots-cles signalant un arome / une note parfumee exploitable pour la reco
KEYWORDS = {
    "flavors": r"ar[oô]me|flavou?r|vanill|fraise|strawberr|citron|lemon|chocolat|caramel",
    "fragrance": r"parfum|fragrance|limonene|linalool|citronellol|geraniol|coumarin|lavand",
}

lines = ["# Rapport qualite — echantillon OFF/OBF", "",
         f"{len(df)} produits uniques.", ""]
for division, g in df.groupby("division"):
    lines += [f"## {division} ({len(g)} produits)", "",
              "| champ | taux de remplissage |", "|---|---|"]
    for col in ["product_name", "brands", "categories_tags", "labels_tags", "ingredients_text"]:
        filled = g[col].fillna("").str.strip().ne("").mean()
        lines.append(f"| {col} | {filled:.0%} |")
    ing = g["ingredients_text"].fillna("")
    kw = ing.str.contains(KEYWORDS[division], case=False, regex=True).mean()
    lines += ["", f"- Ingredients mentionnant un arome/une note : **{kw:.0%}**",
              f"- Langues principales : {g['lang'].value_counts().head(4).to_dict()}",
              f"- Longueur mediane ingredients_text : {int(ing.str.len().median())} caracteres",
              ""]

out = ROOT / "docs" / "quality_report.md"
out.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
