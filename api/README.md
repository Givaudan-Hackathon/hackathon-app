# API Givaudan — backend NestJS

API du prototype Givaudan AI 2026. Socle NestJS 12 (ESM, Vitest), cf. [ADR 0009](../docs/adr/0009-api-nestjs.md).

## Démarrage (depuis la racine du monorepo)

```bash
npm ci                       # lockfile racine
npm run dev -w api     # watch, port 3000
npm run build -w api         # → api/dist/main.js
npm run start:prod -w api    # depuis dist/
npm run test -w api
```

## Configuration

Les variables d'environnement sont lues depuis `api/.env` (créé à partir de `api/.env.example`).

| Variable              | Description                                       | Exemple                                |
| :-------------------- | :------------------------------------------------ | :------------------------------------- |
| `DATABASE_URL`        | URL de connexion PostgreSQL                       | `postgres://app:app@db:5432/app`       |
| `AI_BASE_URL`         | URL de base pour l'API IA (Ollama)                | `http://host.docker.internal:11434/v1` |
| `AI_MODEL`            | Modèle IA à utiliser                              | `llama3.2:1b`                          |
| `AI_API_KEY`          | Clé API pour l'IA (optionnelle)                   | ` `                                    |
| `DATA_API_TIMEOUT_MS` | Délai total Python, corps inclus (1 à 120 000 ms) | `30000`                                |
| `DATA_API_BASE_URL`   | URL de base de l'API Python (Data)                | `http://localhost:8000`                |

## Lancer l'API Data (Python) en parallèle

Pour que la route `/api/conversation` fonctionne, le service FastAPI (Data) doit tourner en arrière-plan.
Depuis le dossier `data-brique/`, lancez le service Python :

```bash
# Exemple de lancement local (à adapter selon l'environnement Data)
cd data-brique
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

_Note : Si vous exposez l'API Python via `ngrok`, l'API NestJS transmet automatiquement le header `ngrok-skip-browser-warning: true` pour éviter la page d'avertissement de ngrok._

## Routes exposées

Préfixe global : `/api` (défini dans `src/main.ts`).

| Méthode | Route               | Description                                                                                                                                |
| :------ | :------------------ | :----------------------------------------------------------------------------------------------------------------------------------------- |
| GET     | `/api`              | Hello World (test de vie)                                                                                                                  |
| GET     | `/api/health`       | État de la connexion PostgreSQL (`{ status, timestamp, db }`)                                                                              |
| GET     | `/api/questions`    | Historique des 10 derniers échanges de test                                                                                                |
| POST    | `/api/questions`    | Envoie une question à Ollama et sauvegarde l'échange                                                                                       |
| POST    | `/api/conversation` | **Relais vers l'assistant Python.** Permet de construire un brief d'arôme (états : relance, affiner, pistes, recapitulatif, echantillons). |

Consultez le fichier [`openapi.yaml`](../openapi.yaml) à la racine pour le détail des schémas d'entrée et de sortie.

Le relais valide la réponse avec `src/contracts/conversation.ts`, contrat Zod
partagé avec React, et conserve les champs additionnels de Python. Le succès
renvoie **200**. Réponse illisible/incomplète : **502** ; refus Data 400/422 :
**422** ; panne Python 5xx ou 429 : **503** ; délai ou Python 504 : **504**,
y compris après réception des en-têtes. Il n’y a ni retry automatique ni réponse
fictive. `guidage: true` active les questions à choix du service Data.
