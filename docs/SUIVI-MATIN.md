# Mise en place de l'environnement : plan et suivi

Source : [Matin : l'environnement](https://learn.glassworks.tech/fullstack-setup/category/matin--lenvironnement).

Ce document suit les étapes du cours. Une étape réalisée par l'assistant et la
validation de Christopher sont cochées séparément. La copie WSL et ses contrôles
Docker/SSH sont réalisés. Les exemples du dev container sont recopiés ; sa
construction est bloquée par le téléchargement de l'image depuis Docker Desktop.

## État initial vérifié le 8 novembre 2026

- Git fonctionne et une identité est configurée.
- Le dépôt possède déjà deux commits, une branche `main` et un remote SSH
  `origin` vers `Givaudan-Hackathon/hackathon-app` sur GitHub.
- L'accès SSH à GitHub et la synchronisation distante restent à vérifier.
- Docker Desktop répond : moteur 28.5.1 et Compose v2.40.3-desktop.1.
- WSL indique Ubuntu par défaut avec WSL 2. L'intégration Docker dans Ubuntu
  reste à tester.
- VS Code et les extensions Dev Containers et WSL sont présents.
- Le projet se trouve dans `C:\Users\Christopher\Desktop\hackathon-app`.
  Le cours demande de travailler dans le système de fichiers Linux de WSL.
- Aucun fichier d'application ou de conteneur n'existe encore. Ollama n'est pas
  disponible dans le PATH Windows.
- Une suppression locale du fichier `README` était déjà présente avant
  l'intervention. Elle est conservée telle quelle, sans être attribuée à ce travail.
  Le fichier `README.md` existe toujours.

## Suivi des étapes

| Étape | Travail à réaliser | Preuve attendue | Réalisé | Validé par Christopher |
| --- | --- | --- | --- | --- |
| 0. Audit et suivi | Examiner la machine et Git ; créer ce suivi, `.gitignore` et `.gitattributes` | État initial documenté ; règles Git vérifiées | [x] | [ ] |
| 1. Choix de stack | Écrire les choix dans le README : Express/TypeScript et Vite/TypeScript acceptés ; fournisseur IA à décider avec l'équipe | Choix et décision en attente lisibles dans le README et les ADR | [x] | [ ] |
| 2. Windows et Git | Préparer une copie de travail dans Ubuntu/WSL en préservant les changements locaux ; vérifier Docker, identité et SSH depuis cet environnement | Docker fonctionne depuis WSL ; dépôt et modifications retrouvés ; accès GitHub vérifié | [x] | [ ] |
| 3. Dev container | Créer `.devcontainer/Dockerfile`, `.devcontainer/devcontainer.json` et `compose.yaml` avec le seul service `dev` | VS Code s'attache ; Node 24, npm 11 et client PostgreSQL 17 répondent | [ ] | [ ] |
| 4. Historique partagé | Repartir de `origin/develop` sur `feature/environnement-cours` après suppression de l'ancienne branche, conformément à l'ADR 0004 | Environnement enregistré sur une branche dédiée, puis publié pour revue | [x] | [ ] |
| 5. Base de données | Ajouter PostgreSQL 17, son healthcheck, `db/data/` et les scripts de `db/init/` | Deux questions de test accessibles par SQL ; données conservées après recréation du conteneur | [ ] | [ ] |
| 6. API et front de test | Créer les workspaces `api` et `web`, le lockfile unique et les scripts communs ; ajouter les routes et le proxy Vite | `/api/health` et `/api/questions` répondent ; le navigateur affiche les données ; `npm run build` passe | [ ] | [ ] |
| 7. Installation automatique | Configurer `postCreateCommand` pour `npm ci` et la copie du `.env.example` si nécessaire | Reconstruction réussie ; un `.env` existant est conservé | [ ] | [ ] |
| 8. IA | Configurer un des fournisseurs du cours ; ajouter le formulaire et POST `/api/questions` | Une question reçoit une vraie réponse et les deux sont enregistrées en base | [ ] | [ ] |
| 9. README et nouvel arrivant | Décrire les prérequis et le démarrage en trois étapes ; faire tester un clone par un coéquipier | Le coéquipier démarre avec le README seul, si possible sur un autre OS | [ ] | [ ] |

## Choix proposés pour suivre l'exemple du cours

L'API de test utilisera Express et TypeScript ; le front utilisera Vite et
TypeScript. Le poste de travail sera basé sur Node 24 et Debian trixie, avec
PostgreSQL 17. Les dépendances seront installées dans le conteneur.

Pour l'IA, le point de départ proposé est Ollama sur la machine hôte avec
`llama3.2:1b`. Le cours permet aussi une API commerciale, le service de l'équipe
Data/IA ou Ollama dans un conteneur optionnel. Le choix devra être adapté au
matériel et à l'organisation de l'équipe avant l'étape 8 ; ces options ne sont
pas toutes à installer. Une éventuelle clé restera dans un `.env` ignoré par Git.

Christopher a confirmé la stack d'exemple. Le fournisseur d'IA sera discuté
avec les équipes Data et Product Owner le lundi 9 novembre. Voir le
[journal des décisions (ADR)](decisions/README.md) pour les raisons des choix
et le statut des propositions. Le barème ne réserve pas de bonus à l'IA locale.

## Comment suivre les modifications

Git existe déjà : il n'y a pas besoin de réinitialiser le dépôt.

- `git status --short` : fichiers ajoutés, modifiés ou supprimés.
- `git diff` : changements de contenu dans les fichiers déjà suivis.
- `git diff --cached` : contenu préparé pour le prochain commit.
- `git log --oneline --graph --all` : historique des étapes enregistrées.
- Le panneau Contrôle de code source de VS Code permet d'examiner ces changements.

Un fichier nouveau doit être ouvert pour être relu : `git diff` seul ne montre
pas son contenu avant son ajout à Git.

Chaque étape donnera lieu à un commit ciblé et à une mise à jour de ce document
avec les vérifications réellement effectuées. Les publications GitHub suivront
les étapes du cours. Les changements déjà présents seront examinés séparément
avant de préparer les commits.

## Journal de l'intervention

### 8 novembre 2026 — Préparation du plan

- Lecture des six pages de la matinée et audit des prérequis locaux.
- Ajout de ce plan et de la checklist de validation.
- Ajout de `.gitattributes` pour les fins de ligne LF.
- Ajout de `.gitignore` pour les dépendances, les builds, les configurations
  locales, les données PostgreSQL et les fichiers Python locaux.
- Aucun commit ni push effectué à ce stade.
- Prochaine étape : documenter les choix de stack puis préparer le travail
  dans WSL en préservant l'état local du dépôt.

### 8 novembre 2026 — Choix et préparation de WSL

- Confirmation d'Express/TypeScript et Vite/TypeScript par Christopher.
- Repérage de `origin/develop` et du commit `cf4b7e8` sur
  `origin/feature/devcontainer`, déjà consacré au dev container.
- Ubuntu répond sous l'utilisateur `hristopherswl`. Docker y répond en version
  28.5.1 et une identité Git y est configurée.
- Le dossier `/home/hristopherswl/projets/hackathon-app` n'existait pas lors
  de la vérification initiale.
- Ajout du guide WSL, du script de copie et des trois premiers ADR.
- Copie WSL créée dans `/home/hristopherswl/projets/hackathon-app` avec le
  dossier `.git` et les modifications locales. Le dossier Windows est conservé.
- Comparaison des fichiers hors `.git` : aucune différence juste après la copie.
  Le commit courant est `6bbf0e1` et les branches distantes sont conservées.
- Le projet est bien sur le système de fichiers Linux `ext4`.
- Le contrôle SSH depuis WSL et l'ouverture de VS Code sur la copie WSL restent
  à effectuer. L'étape 2 n'est donc pas encore cochée comme entièrement réalisée.
- Aucun commit ni push effectué. Les changements restent consultables avec Git.

### 8 novembre 2026 — Reprise sur une branche dédiée

- Actualisation des références GitHub : `main` et `develop` sont au commit
  `6bbf0e1` ; l'ancienne branche contient seulement la configuration du dev container.
- Sauvegarde du commit `cf4b7e8` dans un bundle temporaire, puis suppression
  de `feature/devcontainer` sur GitHub à la demande de Christopher.
- Création de `feature/environnement-cours` depuis `origin/develop` en conservant
  les modifications locales, y compris la suppression préexistante de `README`.
- Docker Engine `28.5.1` et Compose `v2.40.3-desktop.1` répondent depuis WSL.
  L'authentification SSH GitHub réussit pour `christopherDEPASQUAL` ; le fetch
  et la suppression distante ont également réussi. Le terminal dispose de
  la CLI distante VS Code dans le contexte `WSL_DISTRO_NAME=Ubuntu`.
- Relecture des pages dev container et GitFlow du cours. Copie des quatre
  exemples : `Dockerfile`, `devcontainer.json`, `compose.yaml`, `.gitattributes`.
- `docker compose config --quiet` réussit. `docker compose build dev` et
  `docker pull` échouent avec `EOF` lors de l'accès au registre Microsoft.
  Le tag exact du cours existe et son manifeste est accessible depuis WSL.
- Ajout du [guide explicatif du dev container](DEVCONTAINER.md) et de l'ADR 0004.
- Étape 3 non cochée : aucun conteneur du projet n'est démarré ; les versions
  de Node, npm et psql ainsi que l'ouverture dans Dev Containers restent à vérifier.
- La validation de Christopher reste distincte et n'est pas cochée par l'assistant.
- Commit `e597516` publié sur `origin/feature/environnement-cours` avec les
  exemples, le README et les documents de suivi. Aucun merge vers `develop`
  ou `main` n'a été effectué. La suppression préexistante du fichier `README`
  reste une modification locale, hors de ce commit.
