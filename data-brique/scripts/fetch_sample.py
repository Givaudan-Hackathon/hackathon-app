"""Premier echantillon Open Food Facts / Open Beauty Facts.

Respecte la doc API OFF : User-Agent identifiant, <= 10 req/min sur /search.
Pour du volume, utiliser les dumps officiels (https://world.openfoodfacts.org/data).
Usage : python scripts/fetch_sample.py
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

USER_AGENT = "G15-Givaudan-Hackathon/0.1 (projet etudiant)"
SLEEP_S = 7  # ~8.5 req/min < limite 10 req/min
PAGE_SIZE = 100
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

FIELDS = ",".join([
    "code", "product_name", "brands", "categories_tags", "labels_tags",
    "ingredients_text", "countries_tags", "lang",
])

# (source, base_url, division, tag de categorie)
QUERIES = [
    ("off", "https://world.openfoodfacts.org", "flavors", "beverages"),
    ("off", "https://world.openfoodfacts.org", "flavors", "dairies"),
    ("off", "https://world.openfoodfacts.org", "flavors", "snacks"),
    ("obf", "https://world.openbeautyfacts.org", "fragrance", "soaps"),
    ("obf", "https://world.openbeautyfacts.org", "fragrance", "shower-gels"),
    ("obf", "https://world.openbeautyfacts.org", "fragrance", "shampoos"),
]
PAGES_PER_QUERY = 2


def fetch(base_url: str, category: str, page: int, retries: int = 3) -> list[dict]:
    # /search OFF renvoie souvent 503 sous charge -> backoff 20s, 40s, 80s
    for attempt in range(retries + 1):
        resp = requests.get(
            f"{base_url}/api/v2/search",
            params={"categories_tags_en": category, "fields": FIELDS,
                    "page_size": PAGE_SIZE, "page": page, "sort_by": "unique_scans_n"},
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        if resp.status_code not in (429, 503) or attempt == retries:
            break
        time.sleep(20 * 2 ** attempt)
    resp.raise_for_status()
    return resp.json().get("products", [])


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    for source, base_url, division, category in QUERIES:
        for page in range(1, PAGES_PER_QUERY + 1):
            try:
                products = fetch(base_url, category, page)
            except requests.RequestException as exc:
                print(f"[warn] {source}/{category} p{page}: {exc}")
                products = []
            for p in products:
                p.update(source=source, division=division, query_category=category)
                rows.append(p)
            print(f"{source}/{category} p{page}: {len(products)} produits")
            time.sleep(SLEEP_S)

    df = pd.DataFrame(rows).drop_duplicates(subset=["source", "code"])
    for col in ("categories_tags", "labels_tags", "countries_tags"):
        df[col] = df[col].apply(lambda v: "|".join(v) if isinstance(v, list) else v)
    out = RAW_DIR / "off_obf_sample.csv"
    df.to_csv(out, index=False, encoding="utf-8")

    meta = {
        "fichier": out.name,
        "sources": {"off": "Open Food Facts", "obf": "Open Beauty Facts"},
        "licence": "ODbL 1.0 (base) / DbCL (contenu)",
        "date_extraction": fetched_at,
        "methode": "API v2 /search, tri unique_scans_n, User-Agent identifie, ~8 req/min",
        "requetes": [{"source": s, "categorie": c, "pages": PAGES_PER_QUERY} for s, _, _, c in QUERIES],
        "n_lignes": len(df),
        "donnees_personnelles": "aucune (champs produit uniquement)",
    }
    (RAW_DIR / "off_obf_sample.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out} ({len(df)} lignes)")


if __name__ == "__main__":
    main()
