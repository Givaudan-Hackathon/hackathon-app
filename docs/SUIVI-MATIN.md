# Mise en place de l'environnement : plan et suivi

Source : [Matin : l'environnement](https://learn.glassworks.tech/fullstack-setup/category/matin--lenvironnement).

Ce document suit les étapes du cours. Une étape réalisée par l'assistant et la
validation de Christopher sont cochées séparément. La copie WSL et ses contrôles
Docker/SSH sont réalisés. Le dev container est démarré et ses outils sont vérifiés.
La base et sa persistance sont validées. L'API et le front de test sont créés ;
leur compilation, les routes et l'affichage dans Chromium sont vérifiés.

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
| 3. Dev container | Créer `.devcontainer/Dockerfile`, `.devcontainer/devcontainer.json` et `compose.yaml` avec le seul service `dev` | VS Code s'attache ; Node 24, npm 11 et client PostgreSQL 17 répondent | [x] | [ ] |
| 4. Historique partagé | Repartir de `origin/develop` sur `feature/environnement-cours` après suppression de l'ancienne branche, conformément à l'ADR 0004 | Environnement enregistré sur une branche dédiée, puis publié pour revue | [x] | [ ] |
| 5. Base de données | Ajouter PostgreSQL 17, son healthcheck, `db/data/` et les scripts de `db/init/` | Deux questions de test accessibles par SQL ; données conservées après recréation du conteneur | [x] | [x] |
| 6. API et front de test | Créer les workspaces `api` et `web`, le lockfile unique et les scripts communs ; ajouter les routes et le proxy Vite | `/api/health` et `/api/questions` répondent ; le navigateur affiche les données ; `npm run build` passe | [x] | [x] |
| 7. Installation automatique | Configurer `postCreateCommand` pour `npm ci` et la copie du `.env.example` si nécessaire | Reconstruction réussie ; un `.env` existant est conservé | [x] | [ ] |
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
[journal des décisions (ADR)](ADR/README.md) pour les raisons des choix
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

### 9 novembre 2026 — Dev container vérifié et PostgreSQL préparé

- Session connectée dans `/workspace`, sous Debian 13 / x86_64, utilisateur `node`.
- Node `24.22.1`, npm `11.19.1`, psql `17.11`, Git et CLI GitHub disponibles.
- `/workspace` est déclaré comme dépôt de confiance Git ; étape 3 réalisée.
- Ajout du service `db` PostgreSQL 17, du healthcheck, de la dépendance de `dev`,
  du stockage `db/data/` et des deux scripts SQL du cours dans `db/init/`.
- Ajout du transfert VS Code `db:5432` et du guide `BASE-DE-DONNEES.md`.
- Correction des liens après le déplacement local de `docs/decisions/` vers `docs/ADR/`.
- Docker et son socket ne sont pas accessibles depuis cette session. La validation
  Compose, l'exécution SQL et la persistance restent à tester après reconstruction
  depuis VS Code. L'étape 5 reste donc non cochée.
- Aucun commit, push ou merge effectué ; modifications locales préexistantes conservées.

### 9 novembre 2026 — Persistance validée, API et front de test

- Les requêtes SQL depuis `/workspace` retrouvent les deux questions de démonstration.
  Christopher confirme la présence de sa question temporaire après reconstruction
  du conteneur. Le nettoyage est vérifié : seules les deux questions initiales restent.
  L'étape 5 est réalisée et validée par Christopher.
- Lecture de la page « Tester la stack » du cours. Création des workspaces npm
  `api` et `web`, d'un lockfile unique, des scripts communs `dev` et `build`.
  TypeScript reste en `~6.0.3`, les types Node en version 24 et Vite en version 8,
  conformément à l'exemple consulté.
- L'API Express lit `api/.env`, interroge PostgreSQL dans `/api/health` et renvoie
  les dix dernières questions dans `/api/questions`. Les erreurs de requête sont
  journalisées côté serveur avec une réponse JSON générique.
- Le front Vite écoute sur toutes les interfaces, port 5173, et transmet `/api`
  vers le port 3000. Les questions sont insérées comme texte dans la page ; un
  message visible signale une erreur de chargement.
- Vérifications réussies : `npm run build` pour les deux workspaces, requêtes HTTP
  directes et via le proxy Vite, puis affichage de la version PostgreSQL et des
  deux questions avec leurs réponses dans Chromium sans erreur JavaScript.
  Une réponse HTTP 500 simulée dans le navigateur affiche bien le message d'erreur.
- Playwright, Chromium et leurs bibliothèques de test ont été préparés uniquement
  dans `/tmp`, sans ajout aux dépendances du projet ni à l'image du conteneur.
- `api/.env`, `node_modules/` et les dossiers `dist/` sont bien ignorés par Git.
  L'étape 6 est réalisée ; sa validation par Christopher reste à faire dans son
  navigateur. L'installation automatique appartient toujours à l'étape 7.
- README et guides actualisés. Aucun commit, push ou merge effectué ;
  modifications locales préexistantes conservées.

### 9 novembre 2026 — Étape 6 validée et installation automatique préparée

- Christopher fournit une compilation réussie (`tsc` et `vite build`) et une
  capture du front sur `localhost:5173` affichant « API OK », PostgreSQL 17.11
  et les deux questions avec leurs réponses. L'étape 6 est validée par Christopher.
- `postCreateCommand` conserve la déclaration Git existante, exécute `npm ci`,
  puis crée `api/.env` depuis le modèle uniquement si ce fichier est absent.
  Le README décrit maintenant le démarrage avec cette installation automatique.
- Le contenu exact de `postCreateCommand` a été exécuté deux fois dans une copie
  temporaire du projet, avec une configuration Git globale temporaire :
  installation réussie, création du `.env` absent et conservation octet pour
  octet d'un `.env` personnalisé au second passage. La compilation des deux
  workspaces dans cette copie réussit. Le `.env` du projet reste intact.
- `git diff --check` réussit. Docker n'est pas disponible dans cette session :
  la reconstruction réelle reste à lancer par Christopher avec
  `Dev Containers: Rebuild Container`, puis `npm run dev` et contrôle du front.
  L'étape 7 est implémentée ; sa validation après reconstruction reste ouverte.
- L'étape 8 attend le choix du fournisseur IA avec l'équipe. Le test de clone
  par un coéquipier de l'étape 9 reste également à effectuer.
- Aucun commit, push ou merge effectué ; modifications préexistantes conservées.

### 9 novembre 2026 — Rattrapage des commits du cours

- Le cours prévoit « Base de données PostgreSQL », puis « API et front de test ».
  L’installation automatique fait partie du chapitre « Tester la stack » :
  les étapes locales 6 et 7 sont regroupées dans le second commit.
- Le commit PostgreSQL `e3b949e` contient la base,
  son transfert de port, les scripts SQL, le rangement des ADR et leur documentation.
- Le commit API/front regroupe les workspaces, le lockfile npm, les routes,
  le proxy Vite et l’installation automatique. `npm run build` a été relancé
  avec succès avant les commits. Le test de création/conservation du `.env`
  dans une copie temporaire avait également réussi.
- La reconstruction réelle depuis VS Code reste à valider par Christopher ;
  l’étape 7 n’est pas cochée dans sa colonne de validation. Le choix IA et
  le test du clone par un coéquipier restent en attente.
- La suppression préexistante de `README` et le passage local de Compose
  à `pgvector/pgvector:pg17` restent hors des deux commits et sont conservés.
  Les commits utilisent `postgres:17`, conformément à la configuration testée.
- Publication prévue sur `feature/environnement-cours`, pour revue vers `develop`.
  Aucun merge vers `develop` ou `main` n’est effectué.
