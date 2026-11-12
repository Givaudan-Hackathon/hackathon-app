"""Etape 1 : extrait le sous-ensemble France + langue francaise des exports officiels.

Source : export parquet officiel Open Food Facts / Open Beauty Facts
(https://huggingface.co/datasets/openfoodfacts/product-database, lien depuis
https://world.openfoodfacts.org/data). Revision figee pour la reproductibilite.

Chaque fichier est telecharge une seule fois en entier (une requete, reprise possible)
puis interroge en local. La lecture distante par DuckDB declenche des milliers de
requetes de plage et un 429 de Hugging Face (3000 requetes / 5 min) : a eviter.
Les champs contributeurs (creator, editors...) sont exclus de l'extraction.

Sorties (gitignore) : data/raw/exports/{food,beauty}.parquet et {food,beauty}_fr.parquet
Usage : python scripts/extract_exports.py
"""
import time
from pathlib import Path

import duckdb
import requests

REVISION = "99d3492aa6986a56a13a272c5314e80fa3850d25"  # 2026-11-10
BASE = f"https://huggingface.co/datasets/openfoodfacts/product-database/resolve/{REVISION}"
USER_AGENT = "G15-Givaudan-Hackathon/0.1 (projet etudiant)"
OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "exports"

# Textes multilingues : entree 'fr', sinon 'main' (= langue principale, donc fr ici)
QUERY = """
SELECT
    code,
    coalesce(
        list_filter(product_name, lambda x: x.lang = 'fr' AND length(trim(x.text)) > 0)[1].text,
        list_filter(product_name, lambda x: x.lang = 'main' AND length(trim(x.text)) > 0)[1].text
    ) AS product_name,
    coalesce(
        list_filter(ingredients_text, lambda x: x.lang = 'fr' AND length(trim(x.text)) > 0)[1].text,
        list_filter(ingredients_text, lambda x: x.lang = 'main' AND length(trim(x.text)) > 0)[1].text
    ) AS ingredients_text,
    brands, categories_tags, labels_tags, countries_tags, lang,
    unique_scans_n, completeness, last_modified_t
FROM '{src}'
WHERE lang = 'fr'
  AND list_contains(countries_tags, 'en:france')
  AND NOT coalesce(obsolete, false)
"""


def download(name: str) -> Path:
    """Telecharge {name}.parquet en une requete, avec reprise sur fichier .part."""
    dest = OUT_DIR / f"{name}.parquet"
    if dest.exists():
        return dest
    part = dest.with_suffix(".parquet.part")
    done = part.stat().st_size if part.exists() else 0
    headers = {"User-Agent": USER_AGENT}
    if done:
        headers["Range"] = f"bytes={done}-"
    with requests.get(f"{BASE}/{name}.parquet", headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        if done and r.status_code != 206:  # serveur sans reprise : on repart de zero
            done = 0
        with part.open("ab" if done else "wb") as f:
            for chunk in r.iter_content(chunk_size=8 << 20):
                f.write(chunk)
    part.rename(dest)
    return dest


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    for name in ("beauty", "food"):
        t0 = time.time()
        src = download(name)
        out = OUT_DIR / f"{name}_fr.parquet"
        con.sql(f"COPY ({QUERY.format(src=src.as_posix())}) TO '{out.as_posix()}' (FORMAT parquet)")
        n = con.sql(f"SELECT count(*) FROM '{out.as_posix()}'").fetchall()[0][0]
        print(f"{name}: {n} produits FR -> {out.name} ({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
