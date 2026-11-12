"""Etape 2 : constitue l'echantillon v1 et le catalogue complet Flavors.

Entree : data/raw/exports/{food,beauty}_fr.parquet (scripts/extract_exports.py)
Sorties :
  data/processed/catalogue_complet/flavors_catalogue_complet.csv  (tous les produits Flavors retenus)
  data/processed/sample_v1.csv                                    (200 Flavors / query_category + Fragrance)
  data/processed/sample_v1.meta.json
Usage : python scripts/build_sample_v1.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

import criteres as c
from extract_exports import REVISION

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "data" / "raw" / "exports"
PROCESSED = ROOT / "data" / "processed"

COLONNES = [
    "code", "product_name", "brands", "categories_tags", "labels_tags", "ingredients_text",
    "countries_tags", "lang", "unique_scans_n", "completeness", "last_modified_t",
    "source", "division", "query_category", "format",
]


def _tags(v) -> list:
    """Liste de tags DuckDB (liste/ndarray) ; valeur manquante (None, NaN, NA) -> liste vide."""
    return list(v) if isinstance(v, (list, tuple, np.ndarray)) else []


def _join(v):
    tags = _tags(v)
    return "|".join(tags) if tags else None


def _case(familles, avec_filtre: bool) -> str:
    branches = []
    for fam in familles:
        nom, tags = fam[0], fam[1]
        cond = c.PROTEINE_SQL if tags is None else f"list_has_any(categories_tags, {tags})"
        if avec_filtre and fam[2]:
            cond += " AND regexp_matches(ingredients_text, $parfum)"
        branches.append(f"WHEN {cond} THEN '{nom}'")
    return "CASE " + " ".join(branches) + " END"


def flavors(con) -> pd.DataFrame:
    sql = f"""
    SELECT *, {_case(c.FLAVORS_FAMILLES, False)} AS query_category
    FROM '{(EXPORTS / "food_fr.parquet").as_posix()}'
    WHERE regexp_matches(ingredients_text, $arome)
      AND NOT list_has_any(categories_tags, {c.FLAVORS_EXCLUS})
    """
    df = con.execute(f"SELECT * FROM ({sql}) WHERE query_category IS NOT NULL",
                     {"arome": c.AROME_RX}).df()
    df["source"], df["division"] = "off", "flavors"
    poudre = (df["categories_tags"].apply(lambda t: bool(set(_tags(t)) & set(c.POUDRE_TAGS)))
              | df["product_name"].fillna("").str.contains(c.POUDRE_NOM_RX, regex=True))
    df["format"] = None
    prot = df["query_category"] == "boissons_proteinees"
    df.loc[prot, "format"] = poudre[prot].map({True: "poudre", False: "pret_a_boire"})
    return df


def fragrance(con) -> pd.DataFrame:
    sql = f"""
    SELECT *, {_case(c.FRAGRANCE_FAMILLES, True)} AS query_category
    FROM '{(EXPORTS / "beauty_fr.parquet").as_posix()}'
    WHERE length(trim(ingredients_text)) > 10
    """
    df = con.execute(f"SELECT * FROM ({sql}) WHERE query_category IS NOT NULL",
                     {"parfum": c.PARFUM_RX}).df()
    df["source"], df["division"], df["format"] = "obf", "fragrance", None
    return df


def to_csv(df: pd.DataFrame, path: Path) -> None:
    df = df[COLONNES].copy()
    for col in ("categories_tags", "labels_tags", "countries_tags"):
        df[col] = df[col].apply(_join)
    # retours chariot dans les textes saisis : LF seul, comme impose par .gitattributes
    for col in ("product_name", "brands", "ingredients_text"):
        df[col] = df[col].str.replace("\r\n", "\n").str.replace("\r", "\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")


def main() -> None:
    con = duckdb.connect()
    # tri par code avant tirage : resultat independant de l'ordre de lecture DuckDB
    flav = flavors(con).sort_values("code").reset_index(drop=True)
    frag = fragrance(con).sort_values("code").reset_index(drop=True)
    assert not flav["code"].duplicated().any() and not frag["code"].duplicated().any()

    catalogue = PROCESSED / "catalogue_complet" / "flavors_catalogue_complet.csv"
    to_csv(flav, catalogue)

    # toutes les familles Flavors depassent le quota (min 273 produits)
    assert flav["query_category"].value_counts().min() >= c.FLAVORS_PAR_CATEGORIE
    flav_sample = flav.groupby("query_category").sample(n=c.FLAVORS_PAR_CATEGORIE,
                                                        random_state=c.GRAINE)
    sample = pd.concat([flav_sample, frag], ignore_index=True)
    out = PROCESSED / "sample_v1.csv"
    to_csv(sample, out)

    meta = {
        "fichier": out.name,
        "catalogue_complet": catalogue.relative_to(PROCESSED).as_posix(),
        "sources": {"off": "Open Food Facts", "obf": "Open Beauty Facts"},
        "export": "https://huggingface.co/datasets/openfoodfacts/product-database",
        "revision_export": REVISION,
        "licence": "ODbL 1.0 (base) / DbCL (contenu)",
        "date_constitution": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "filtres": {
            "commun": "countries_tags contient en:france, lang = fr, non obsolete",
            "flavors": "ingredients mentionnant un arome, hors fromages/biscuits/alcools",
            "fragrance": "ingredients remplis ; deodorants, 2-en-1 et savons de rasage parfumes",
        },
        "echantillonnage": {
            "flavors": f"{c.FLAVORS_PAR_CATEGORIE} par query_category, graine {c.GRAINE}",
            "fragrance": "exhaustif",
        },
        "n_catalogue_flavors": len(flav),
        "n_lignes": len(sample),
        "par_query_category": sample.groupby(["division", "query_category"]).size()
        .rename("n").reset_index().to_dict("records"),
        "donnees_personnelles": "aucune (champs contributeurs exclus a l'extraction)",
    }
    out.with_suffix(".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, default=int), encoding="utf-8")
    print(f"catalogue Flavors : {len(flav)} -> {catalogue.name}")
    print(f"v1 : {len(sample)} lignes -> {out.name}")
    print(sample.groupby(["division", "query_category"]).size().to_string())
    prot = sample[sample["query_category"] == "boissons_proteinees"]
    print("format proteinees :", prot["format"].value_counts().to_dict())


if __name__ == "__main__":
    main()
