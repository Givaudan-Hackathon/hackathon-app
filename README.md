# Hackathon HETIC × Givaudan 2026

Dépôt collaboratif de l'application développée dans le cadre du hackathon HETIC × Givaudan 2026.

Pour l'atelier, nous suivons la stack de test du cours :

- API : Express et TypeScript, avec PostgreSQL 17 et Node 24.
- Front : Vite et TypeScript.
- IA : Ollama sur Windows avec le modèle local `llama3.2:1b`.

Le dev container démarre : Node 24, npm 11 et le client PostgreSQL 17 sont vérifiés.
PostgreSQL est accessible et la conservation des données après reconstruction
est validée. L'API Express et le front Vite de test sont en place.
Consulter le [plan et les vérifications](docs/SUIVI-MATIN.md), le
[guide WSL](docs/WSL.md), les [explications du dev container](docs/DEVCONTAINER.md)
et le [journal des décisions (ADR)](docs/ADR/README.md).

Le formulaire appelle maintenant `POST /api/questions`, qui interroge Ollama
et enregistre l'échange en base. Installer le serveur et le modèle sur Windows
avant de l'utiliser ; voir le [guide IA](docs/IA.md) pour les étapes et leur rôle.

La branche d'intégration est `develop`. Chaque branche de travail est mise à
jour depuis `develop`, puis relue via une pull request vers cette branche.
Une pull request de `develop` vers `main` prépare une version démontrable, selon le
[GitFlow du cours](https://learn.glassworks.tech/fullstack-setup/collaboration/gitflow).

## Démarrer l'environnement

La collaboration, les contrôles de qualité et l'ordre de revue des PR sont
décrits dans le [suivi de l'atelier 2](docs/SUIVI-APRES-MIDI.md).
Le [guide du tableau Hackathon](docs/TABLEAU-HACKATHON.md) décrit les colonnes,
les critères Ready/Done, les accès et le parcours d'un ticket jusqu'à la démo.

1. Cloner le dépôt dans le système de fichiers Linux de WSL (sous Windows),
   avec Docker Desktop et VS Code / Dev Containers disponibles.
2. Ouvrir le dossier dans VS Code puis lancer `Dev Containers: Reopen in Container`.
   Attendre la fin de l'installation automatique des dépendances et de la
   création de `api/.env` depuis `api/.env.example` s'il n'existe pas déjà.
   Après modification de Compose ou du dev container, lancer
   `Dev Containers: Rebuild Container`.
3. Dans le terminal du conteneur, à la racine du projet :

   ```bash
   npm run dev
   ```

Ouvrir [le front](http://localhost:5173) : la page doit afficher « API OK »,
la version PostgreSQL et les deux questions de test. VS Code transfère les ports
3000 et 5173 ; vérifier l'onglet **Ports** si le navigateur ne répond pas.
L'installation est exécutée par `postCreateCommand` à la création ou à la
reconstruction du conteneur. Un fichier `api/.env` existant est conservé.
Pour relancer manuellement la préparation depuis la racine du projet :

```bash
npm ci && (test -f api/.env || cp api/.env.example api/.env)
```

## Comprendre le test API et front

L'organisation suit le [cours : tester la stack](https://learn.glassworks.tech/fullstack-setup/environnement/tester-la-stack).

- `api/` contient Express et TypeScript. La connexion PostgreSQL vient de
  `api/.env`, ignoré par Git ; les valeurs locales sont dans `api/.env.example`.
- `web/` contient Vite et TypeScript. Les appels `/api` du navigateur passent
  par le proxy Vite vers l'API sur le port 3000.
- Le `package.json` racine relie les deux workspaces npm ; un seul
  `package-lock.json` fixe toutes les versions installées par `npm ci`.
- `npm run dev` démarre les deux serveurs ; **Ctrl+C** les arrête.
  `npm run dev -w api` ou `npm run dev -w web` les démarre séparément.

Dans un second terminal, vérifier l'API et compiler les deux workspaces :

```bash
curl --fail http://localhost:3000/api/health
curl --fail http://localhost:3000/api/questions
npm run build
```

`/api/health` interroge réellement PostgreSQL et renvoie sa version.
`/api/questions` renvoie les dix dernières questions, de la plus récente à la
plus ancienne. Le front affiche les questions et leurs réponses ; son formulaire
permet de créer une question et sa réponse avec Ollama à l'étape 8.

Voir le [guide PostgreSQL](docs/BASE-DE-DONNEES.md) pour les contrôles SQL et
le test de persistance.
