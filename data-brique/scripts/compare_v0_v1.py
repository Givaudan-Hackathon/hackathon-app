"""Comparaison v0 (API /search, 9 nov.) / v1 (exports officiels, 10 nov.) -> docs/comparaison_v0_v1.md

Memes definitions pour les deux versions (scripts/criteres.py).
Usage : python scripts/compare_v0_v1.py
"""
from pathlib import Path

import pandas as pd

import criteres as c

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = {
    "v0": ROOT / "data" / "raw" / "off_obf_sample_v0.csv",
    "v1": ROOT / "data" / "processed" / "sample_v1.csv",
}
RX = {"flavors": c.AROME_RX, "fragrance": c.PARFUM_RX}


def pct(x: float) -> str:
    return f"{x:.0%}"


def indicateurs(g: pd.DataFrame, division: str) -> dict:
    ing = g["ingredients_text"].fillna("")
    pays = g["countries_tags"].fillna("")
    return {
        "produits": len(g),
        "vendus en France": pct(pays.str.contains("en:france", regex=False).mean()),
        "vendus uniquement en France": pct((pays == "en:france").mean()),
        "langue fr": pct((g["lang"] == "fr").mean()),
        "ingredients remplis": pct(ing.str.strip().str.len().gt(10).mean()),
        "mention arome / parfum": pct(ing.str.contains(RX[division], regex=True).mean()),
        "query_category distinctes": g["query_category"].nunique(),
    }


def main() -> None:
    dfs = {v: pd.read_csv(p, dtype=str) for v, p in VERSIONS.items()}
    lines = [
        "# Comparaison des echantillons v0 et v1", "",
        "- **v0** : API `/search` OFF/OBF, 9 nov. 2026, tri par popularite, sans filtre pays/langue.",
        "- **v1** : exports officiels (revision figee), France + langue `fr`, categories validees,",
        "  200 Flavors par `query_category` (graine 42), Fragrance exhaustive.",
        "",
        "Definitions communes : `scripts/criteres.py` (arome = `AROME_RX`, parfum = `PARFUM_RX`).",
        "",
    ]
    for division in ("flavors", "fragrance"):
        ind = {v: indicateurs(df[df["division"] == division], division) for v, df in dfs.items()}
        lines += [f"## {division.capitalize()}", "", "| indicateur | v0 | v1 |", "|---|---|---|"]
        lines += [f"| {k} | {ind['v0'][k]} | {ind['v1'][k]} |" for k in ind["v0"]]
        lines.append("")
        for v, df in dfs.items():
            g = df[df["division"] == division]
            langues = g["lang"].value_counts(normalize=True).head(4)
            cats = g["query_category"].value_counts()
            lines += [
                f"**{v}** — langues : " + ", ".join(f"{k} {pct(x)}" for k, x in langues.items()),
                "",
                f"**{v}** — query_category : " + ", ".join(f"{k} {n}" for k, n in cats.items()),
                "",
            ]
    out = ROOT / "docs" / "comparaison_v0_v1.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
