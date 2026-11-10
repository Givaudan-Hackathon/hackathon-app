# Consignes de l’API applicative

Portée : `api/`. Lire aussi `../AGENTS.md`, le contrat `../openapi.yaml` et les
décisions dans `../docs/adr/`. Ce fichier est maintenu par les Tech leads.

## Lancer et vérifier

- Depuis la racine : `npm run dev -w api` démarre le socle sur 3000 ; `npm run build -w api` compile TypeScript.
- `npm run start -w api` exécute le code compilé ; la configuration locale vient de `.env`, préparé depuis `.env.example`.
- GET `/api/health` vérifie réellement PostgreSQL. GET `/api/questions` lit les échanges ; POST `/api/questions` utilise le fournisseur IA puis insère une ligne.

## Frontières et contrat

- Les routes actuelles sont dans `src/index.ts`. Une modification de leur entrée, réponse ou code HTTP met à jour `../openapi.yaml` et les consommateurs.
- La connexion PostgreSQL utilise `pg.Pool`. Garder les paramètres SQL pour les valeurs fournies par le client ; le schéma du socle est dans `../db/init/001-schema.sql`.
- `ask()` dans `src/index.ts` utilise `AI_BASE_URL`, `AI_MODEL` et `AI_API_KEY`. Les erreurs du fournisseur restent distinctes de celles de PostgreSQL et le délai IA est borné à 60 secondes.
- L’API Data est un service distinct vérifié par `../scripts/verifier-api-data.mjs` ; sa présence ne prouve pas encore l’intégration dans l’API applicative.
- `../docs/adr/0009-api-nestjs.md` propose NestJS. Après migration validée, préserver ou faire évoluer explicitement le contrat, les erreurs et le chargement de configuration, puis actualiser les chemins de ce fichier.
- Une migration NestJS n’ajoute pas implicitement un ORM, une base ou une route métier : ces changements doivent correspondre au ticket et aux ADR concernés.
