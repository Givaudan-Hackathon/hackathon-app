# Comparaison des echantillons v0 et v1

- **v0** : API `/search` OFF/OBF, 9 nov. 2026, tri par popularite, sans filtre pays/langue.
- **v1** : exports officiels (revision figee), France + langue `fr`, categories validees,
  200 Flavors par `query_category` (graine 42), Fragrance exhaustive.

Definitions communes : `scripts/criteres.py` (arome = `AROME_RX`, parfum = `PARFUM_RX`).

## Flavors

| indicateur                  | v0  | v1   |
| --------------------------- | --- | ---- |
| produits                    | 490 | 1000 |
| vendus en France            | 73% | 100% |
| vendus uniquement en France | 15% | 80%  |
| langue fr                   | 76% | 100% |
| ingredients remplis         | 97% | 100% |
| mention arome / parfum      | 35% | 100% |
| query_category distinctes   | 3   | 5    |

**v0** — langues : fr 76%, en 11%, ar 4%, es 3%

**v0** — query_category : snacks 198, dairies 192, beverages 100

**v1** — langues : fr 100%

**v1** — query_category : boissons_aromatisees 200, boissons_lactees 200, boissons_proteinees 200, boissons_vegetales 200, desserts_aromatises 200

## Fragrance

| indicateur                  | v0  | v1   |
| --------------------------- | --- | ---- |
| produits                    | 552 | 1193 |
| vendus en France            | 53% | 100% |
| vendus uniquement en France | 42% | 93%  |
| langue fr                   | 54% | 100% |
| ingredients remplis         | 67% | 100% |
| mention arome / parfum      | 60% | 92%  |
| query_category distinctes   | 3   | 6    |

**v0** — langues : fr 54%, en 22%, de 10%, nl 5%

**v0** — query_category : shower-gels 190, shampoos 185, soaps 177

**v1** — langues : fr 100%

**v1** — query_category : gels_douche 400, savons 315, deodorants 315, parfums 88, shampoings_gels_douche 72, savons_rasage 3
