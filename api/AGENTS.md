# Consignes de l’API applicative

Portée : `api/`. Lire aussi `../AGENTS.md`, le contrat `../openapi.yaml` et les
décisions dans `../docs/adr/`. Ce fichier est maintenu par les Tech leads.

## Lancer et vérifier

- Depuis la racine : `npm run dev -w api` démarre l’API NestJS sur 3000 en watch mode ; `npm run build -w api` produit `dist/main.js`.
- `npm run start:prod -w api` exécute le code compilé depuis `dist/main` ; la configuration locale vient de `api/.env`, préparé depuis `.env.example` et chargé dans `src/main.ts` via `process.loadEnvFile()`.
- GET `/api/health` vérifie réellement PostgreSQL et retourne `{ status, timestamp, db }` avec `db` = `SELECT version()`. GET `/api/questions` lit les échanges ; POST `/api/questions` utilise le fournisseur IA puis insère une ligne.

## Frontières et contrat

- Les routes actuelles sont dans `src/health/` et `src/questions/`. Une modification de leur entrée, réponse ou code HTTP met à jour `../openapi.yaml` et les consommateurs.
- Le format d’erreur exposé est `{ error }`, préservé par le filtre global `src/shared/error.filter.ts`. Les exceptions levées par les services (`HttpException` 400/502/503/504) conservent leur statut ; le filtre ne détecte que les erreurs de body-parser, jamais le mot `JSON` seul.
- La connexion PostgreSQL utilise un `pg.Pool` partagé exposé via le token `PG_POOL` dans `src/database/database.module.ts`. Garder les paramètres SQL pour les valeurs fournies par le client ; le schéma du socle est dans `../db/init/001-schema.sql`.
- `../db/` est partagé avec la Data : coordonner les modifications du schéma et des données initiales avec les deux équipes, ainsi que la mise à jour des bases existantes. La connexion PostgreSQL du service Data reste à intégrer et à vérifier dans sa branche.
- `QuestionsService.ask()` dans `src/questions/questions.service.ts` utilise `AI_BASE_URL`, `AI_MODEL` et `AI_API_KEY`. Les erreurs du fournisseur restent distinctes de celles de PostgreSQL ; le délai IA est borné à 60 secondes et préservé pendant la lecture du corps de la réponse (`TimeoutError`/`AbortError` dans `response.json()` → 504, pas 502).
- L’API Data est un service distinct vérifié par `../scripts/verifier-api-data.mjs` ; sa présence ne prouve pas encore l’intégration dans l’API applicative.
- `../docs/adr/0009-api-nestjs.md` est **Acceptée** et la migration est réalisée. Toute évolution du contrat, des erreurs ou du chargement de configuration doit être documentée dans cet ADR et répercutée dans ce fichier.
- Une migration NestJS n’ajoute pas implicitement un ORM, une base ou une route métier : ces changements doivent correspondre au ticket et aux ADR concernés.
