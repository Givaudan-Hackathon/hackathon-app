# Inventaire des sources — Brique Data G15 (lun. 9 nov. 2026)

| #   | Source                               | Usage dans le moteur                                                         | Licence                                                                      | Acces                                                    | Statut                                                                        | Alternative                                                                                                              |
| --- | ------------------------------------ | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 1   | Open Food Facts — API v2 `/search`   | Catalogue Flavors : produits, categories, ingredients/aromes                 | ODbL 1.0 / DbCL                                                              | Libre, User-Agent identifiant, ≤ 10 req/min              | OK — 490 produits (beverages, dairies, snacks). 503 frequents → retry/backoff | Dump CSV/Parquet officiel (openfoodfacts.org/data), miroir Hugging Face `openfoodfacts/product-database`                 |
| 2   | Open Beauty Facts — API v2 `/search` | Catalogue Fragrance : savons, gels douche, shampoings                        | ODbL 1.0 / DbCL                                                              | Idem OFF                                                 | OK — 552 produits                                                             | Dump officiel OBF                                                                                                        |
| 3   | IFRA Transparency List               | Referentiel ingredients de parfumerie (dictionnaire de notes)                | Publication IFRA, usage informationnel — CGU a verifier avant redistribution | Fichier Excel sur ifrafragrance.org (page redirige, 301) | A telecharger manuellement                                                    | Liste INCI des 26 allergenes parfumants (Reglement UE 1223/2009, annexe III)                                             |
| 4   | API Sirene INSEE                     | Entreprises clientes potentielles (NAF 11.07B boissons, 20.42Z cosmetiques…) | Licence Ouverte 2.0                                                          | Cle API via portail-api.insee.fr (compte requis)         | Cle a creer → `.env`                                                          | **API Recherche d'entreprises** (recherche-entreprises.api.gouv.fr, sans cle, testee OK) ; stock Sirene sur data.gouv.fr |
| 5   | Commandes clients                    | Historique pour scoring / reco                                               | —                                                                            | Aucune source publique                                   | A generer                                                                     | Donnees synthetiques documentees (seed fixe, regles de generation dans `docs/`)                                          |

## Points d'attention

- **robots.txt OFF/OBF** interdit `/api` aux crawlers ; la doc API officielle autorise l'usage applicatif avec User-Agent et rate limit. On reste en echantillon leger, le volume passe par les dumps.
- **Donnees personnelles** : l'API Recherche d'entreprises renvoie des `dirigeants` (noms de personnes physiques) → a supprimer a l'ingestion. Ne garder que SIREN, raison sociale, NAF, tranche d'effectif, departement.
- **Biais echantillon** : tri par popularite (`unique_scans_n`) → sur-representation de la France et des grandes marques (fr = 76 % cote Flavors).
- **Qualite** : voir `docs/quality_report.md`. Fragrance : `ingredients_text` rempli a 68 % seulement ; Flavors : 99 %.

## Reproduction

```
cd data-brique
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python scripts/fetch_sample.py     # ~2 min (rate limit)
.venv/Scripts/python scripts/quality_report.py
```

Metadonnees d'extraction (date, licence, requetes) : `data/raw/off_obf_sample.meta.json`.
