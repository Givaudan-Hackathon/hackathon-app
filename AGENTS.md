# Consignes du dépôt Hackathon Givaudan

Le produit cible les petits clients qui décrivent leur projet d’arômes alimentaires
et déposent un brief. Lire `README.md` pour l’état du socle et les choix proposés.

## Lancer

- L’environnement de référence est `.devcontainer/` avec Node 24, npm 11 et PostgreSQL 17 via `compose.yaml`.
- `npm ci` utilise le lockfile racine ; conserver les workspaces `api/` et `web/` de `package.json`.
- `npm run dev` lance Express sur 3000 et Vite sur 5173 ; `api/.env.example` décrit la configuration locale.
- Vérifier le socle avec `/api/health`, puis `/api/questions` ; les routes sont dans `api/src/index.ts` et leur contrat dans `openapi.yaml`.
- Avant une PR, lancer `npm run lint`, `npm run format:check` et `npm run build`, comme `.github/workflows/ci.yml`.

## Règles

- Avant de modifier `web/` ou `api/`, lire aussi leur `AGENTS.md` : la racine porte les règles communes et le fichier local précise son composant.
- Les Data rédigent et maintiennent `data-brique/AGENTS.md` dans leur branche. Consulter ce fichier dès qu’il existe avant de modifier leur code ; son absence actuelle ne vaut pas validation des choix Data.
- React et NestJS restent des propositions documentées dans `docs/adr/`, pas des dépendances déjà installées.
- `db/` définit la base PostgreSQL commune à l’API applicative et au service Data. Les Data et les Tech leads coordonnent ses évolutions de schéma et ses données initiales ; la connexion Data reste à intégrer et à vérifier.
- `db/init/` n’est joué qu’à l’initialisation de PostgreSQL ; modifier ses scripts ne met pas à jour une base existante. Toute évolution doit préciser comment mettre à jour une base déjà initialisée.
- Le fournisseur IA du socle est appelé par `ask()` dans `api/src/index.ts` ; ses valeurs viennent de `api/.env`.
- Le script `scripts/verifier-api-data.mjs URL` vérifie le service Data par HTTP ; le dépôt commun ne confond pas dépendances Node et Python.
- Une branche par ticket part de `develop` ; la PR vise `develop` et suit `.github/pull_request_template.md`.
- Le plan et les résultats restent dans le ticket GitHub ; les brouillons Markdown vont dans `.scratch/`, ignoré par Git.

## Décisions

- Lire `docs/adr/README.md` et les ADR concernés avant de changer un composant ou ses dépendances.
- Respecter les ADR acceptés ; les propositions 0007 à 0010 demandent encore une validation. Un changement d’ADR accepté passe par une nouvelle décision explicite.
- Une modification des routes doit mettre à jour `openapi.yaml` et les consommateurs concernés dans la même PR.

## À ne pas faire

- Contourner `.husky/pre-commit` avec `--no-verify`, ajouter un `eslint-disable` ou affaiblir `qualite` pour masquer une erreur.
- Écraser les modifications locales de l’utilisateur ou les inclure dans une PR sans lien avec le ticket.
- Versionner `api/.env`, un jeton ou `db/data/` ; leurs exclusions sont dans `.gitignore`.
- Annoncer une migration React/NestJS, un essai humain ou l’intégration Data comme réalisé sur la seule présence d’un ADR proposé.
