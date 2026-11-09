# Hackathon Givaudan — Brique Data (équipe G15)

## Contexte

Thème 02 : plateforme de commande intelligente (Givaudan, arômes Flavors + parfums Fragrance).
Je suis Data 2. Rôle Data = construire l'intelligence derrière le prototype, exposée via API à l'équipe Tech.

## Brique Data visée

Moteur "brief client → recommandation" :

- Entrée : demande client en texte libre (ex. "boisson protéinée pour sportifs, goût vanille")
- Sortie JSON : division (flavors/fragrance), application, notes/arômes extraits, top 5 produits recommandés + score

## Sources de données (priorité : Open Data > API > scraping)

- Open Food Facts API (ODbL) — boissons/arômes
- Open Beauty Facts API (ODbL) — savons/cosmétiques parfumés
- IFRA Transparency List — ingrédients de parfumerie
- API Sirene INSEE — entreprises clientes (score de potentiel)
- Commandes : pas de source publique → données synthétiques documentées
  Règles : respecter CGU et robots.txt, rate limiting, aucune donnée personnelle, documenter source/date/licence.

Note OFF/OBF : robots.txt interdit /api aux crawlers, mais la doc API officielle autorise l'usage
avec un User-Agent identifiant et ≤ 10 req/min sur la recherche. Pour du volume → dumps officiels
(https://world.openfoodfacts.org/data), pas d'appels API en masse.

## Planning et livrables

- Lun 9 : inventaire des sources + accès + premier échantillon + qualité + alternatives
- Mar 10 (Gate 1, 16h) : dataset exploitable, baseline V1 (notebook), Swagger/OpenAPI, endpoint dummy via ngrok
- Jeu 12 : pipeline, modèle V2, validation sur 30 cas de référence avec métriques, API réelle
- Ven 13 : code + doc + procédure de reproduction, comparaison V1/V2, limites et biais

## Stack

Python 3, pandas, FastAPI (Swagger auto), ngrok, Git/GitHub. Orange Data Mining pour l'exploration.

## Conventions

- Noms en snake_case sans accents
- data/raw, data/processed, notebooks/, api/, tests/, scripts/, docs/
- Ne jamais committer de token (ngrok, API) → .env + .gitignore
