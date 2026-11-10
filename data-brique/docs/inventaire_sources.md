# Inventaire des sources — Brique Data G15 (mis a jour le mar. 10 nov. 2026)

| #   | Source                                                                             | Usage dans le moteur                                                         | Licence                                                                      | Acces                                                    | Statut                                                                                  | Alternative                                                                                                              |
| --- | ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 1   | Open Food Facts — export parquet officiel (`food.parquet`, revision `99d3492`)     | Catalogue Flavors : produits, categories, ingredients/aromes                 | ODbL 1.0 / DbCL                                                              | Libre ; telechargement unique (8 Go) puis requete locale | **OK** — 1,10 M produits France/`fr` ; 8 943 produits Flavors retenus, 1 000 dans la v1 | API v2 `/search` (v0) ; export CSV officiel (sans colonne `lang`)                                                        |
| 2   | Open Beauty Facts — export parquet officiel (`beauty.parquet`, revision `99d3492`) | Catalogue Fragrance : savons, gels douche, parfums, deodorants               | ODbL 1.0 / DbCL                                                              | Idem OFF (68 Mo)                                         | **OK** — 18 355 produits France/`fr` ; 1 193 retenus dans la v1                         | API v2 `/search` (v0) ; export CSV/JSONL officiel                                                                        |
| 3   | IFRA Transparency List                                                             | Referentiel ingredients de parfumerie (dictionnaire de notes)                | Publication IFRA, usage informationnel — CGU a verifier avant redistribution | Fichier Excel sur ifrafragrance.org (page redirige, 301) | A telecharger manuellement                                                              | Liste INCI des 26 allergenes parfumants (Reglement UE 1223/2009, annexe III), deja utilisee dans `PARFUM_RX`             |
| 4   | API Sirene INSEE                                                                   | Entreprises clientes potentielles (NAF 11.07B boissons, 20.42Z cosmetiques…) | Licence Ouverte 2.0                                                          | Cle API via portail-api.insee.fr (compte requis)         | Cle a creer → `.env`                                                                    | **API Recherche d'entreprises** (recherche-entreprises.api.gouv.fr, sans cle, testee OK) ; stock Sirene sur data.gouv.fr |
| 5   | Commandes clients                                                                  | Historique pour scoring / reco                                               | —                                                                            | Aucune source publique                                   | A generer                                                                               | Donnees synthetiques documentees (seed fixe, regles de generation dans `docs/`)                                          |

## Jeux de donnees

| Fichier                                                          | Contenu                                                                          | Lignes |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------------- | ------ |
| `data/raw/off_obf_sample_v0.csv`                                 | v0 : API `/search`, 9 nov., sans filtre pays/langue (conservee pour comparaison) | 1 042  |
| `data/processed/sample_v1.csv`                                   | v1 : 200 Flavors par `query_category` (graine 42) + Fragrance exhaustive         | 2 193  |
| `data/processed/catalogue_complet/flavors_catalogue_complet.csv` | Tous les produits Flavors retenus, pour la V2                                    | 8 943  |

Criteres de selection (tags, filtres arome/parfum, priorites) : `scripts/criteres.py`.
Comparaison chiffree : `docs/comparaison_v0_v1.md`. Qualite : `docs/quality_report.md`.

### Perimetre v1

- Commun : `countries_tags` contient `en:france`, `lang = fr`, produit non obsolete. Nom et ingredients pris dans l'entree `fr`, sinon `main` (langue principale).
- Flavors : ingredients mentionnant un arome ; hors fromages, biscuits, alcools. Familles : `boissons_proteinees` (colonne `format` : `poudre` / `pret_a_boire`), `boissons_vegetales`, `boissons_lactees`, `desserts_aromatises`, `boissons_aromatisees` (sirops inclus).
- Fragrance : ingredients remplis. Familles : `parfums`, `savons`, `gels_douche`, et, parfumes uniquement, `deodorants`, `shampoings_gels_douche` (2-en-1), `savons_rasage`.
- Doublons : un produit recoit la premiere famille de la liste dans `criteres.py`.

## Points d'attention

- **Exports plutot qu'API** : la lecture distante du parquet par DuckDB a declenche un HTTP 429 de Hugging Face (3 000 requetes / 5 min). Le script telecharge donc chaque fichier en une requete (reprise possible) puis travaille en local. Le parquet food de 8 Go est supprime apres extraction ; il se retelecharge a l'identique grace a la revision figee.
- **Langue** : les exports CSV n'ont pas de colonne `lang`, d'ou le choix du parquet. Le texte en langue principale est stocke sous le code `main` : l'ignorer faisait perdre ~7 000 listes d'ingredients.
- **Donnees personnelles** : champs contributeurs (`creator`, `editors`, `photographers`…) exclus a l'extraction. L'API Recherche d'entreprises renvoie des `dirigeants` → a supprimer a l'ingestion.
- **Biais v1** :
  - Quota de 200 par famille : la v1 ne reflete pas les proportions du marche (4 788 boissons aromatisees contre 273 proteinees dans le catalogue).
  - Filtre arome sur les ingredients : un produit aromatise dont la liste ne cite pas l'arome est ecarte ; 100 % des Flavors v1 mentionnent un arome par construction.
  - Fragrance : savons sans filtre parfum (74 % en mentionnent un), `savons_rasage` tres petit (3).
  - `format` des proteinees : heuristique nom + tags, quelques erreurs observees (poudre classee pret-a-boire et inversement).
  - Glaces (2 275) et yaourts aux fruits (2 117) ecartes pour l'instant malgre leur pertinence.

## Reproduction

```
cd data-brique
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python scripts/extract_exports.py   # telecharge ~8 Go, ~25 min selon le debit
.venv/Scripts/python scripts/build_sample_v1.py   # v1 + catalogue complet, deterministe
.venv/Scripts/python scripts/quality_report.py
.venv/Scripts/python scripts/compare_v0_v1.py
```

v0 : `scripts/fetch_sample.py` (API, ~2 min). Metadonnees (source, revision, date, licence, filtres) : `data/processed/sample_v1.meta.json`, `data/raw/off_obf_sample_v0.meta.json`.
