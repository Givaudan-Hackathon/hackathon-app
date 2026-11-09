# Étape 3 — Comprendre le dev container

Source : [Le dev container — cours HETIC](https://learn.glassworks.tech/fullstack-setup/environnement/devcontainer).

Les fichiers `.devcontainer/Dockerfile`, `.devcontainer/devcontainer.json`,
`compose.yaml` et `.gitattributes` sont recopiés depuis les blocs du cours,
commentaires compris. Ils ont été comparés aux exemples consultés le
8 novembre 2026. La configuration initiale contenait uniquement le service `dev`. Le service
`db` est maintenant ajouté : voir [le guide PostgreSQL](BASE-DE-DONNEES.md).

## Le problème résolu

Chaque membre doit retrouver les mêmes outils, même s'il utilise un autre OS.
Le dépôt décrit donc le poste de développement. Docker construit son image,
puis lance un conteneur à partir de cette image. VS Code s'y connecte pour
exécuter les outils dans ce même environnement.

Sur ce poste : Windows héberge l'interface VS Code et Docker Desktop ; Ubuntu
dans WSL héberge les fichiers du projet ; le conteneur fournit Node et les
outils de développement.

## Le Dockerfile : quels outils installer ?

- `FROM ...:24-trixie` choisit l'image Microsoft Dev Containers avec Node 24
  sur Debian trixie. Une image est le modèle utilisé pour créer un conteneur.
- `sed ...` remplace le miroir Debian par le miroir français prévu par le cours
  pour le réseau HETIC. Le commentaire du cours parle d'Ubuntu ; l'image
  utilisée est bien Debian.
- `apt-get install ... postgresql-client` installe `psql`, le client SQL.
  Cela n'installe pas le serveur PostgreSQL : celui-ci aura son propre service.
- La suppression de `/var/lib/apt/lists/*` retire les index de paquets après
  l'installation pour réduire la taille de cette couche de l'image.

Le tag fixe une version majeure de Node et une distribution. Il ne fige pas
chaque correctif : ce n'est pas une image verrouillée par son empreinte.

## Compose : comment lancer le poste de travail ?

- `name: hackathon` donne un nom commun aux ressources Docker de ce projet.
- Le service `dev` est construit depuis `.devcontainer/Dockerfile`.
- `command: sleep infinity` garde le conteneur démarré pour que VS Code puisse
  s'y connecter. Cela ne lance pas encore d'application.
- `.:/workspace:cached` monte le dossier du dépôt dans `/workspace` : les
  changements faits depuis le conteneur sont conservés dans la copie WSL.

## devcontainer.json : comment VS Code s'y connecte ?

- `dockerComposeFile` désigne Compose ; `service: dev` choisit le conteneur.
- `workspaceFolder` indique où ouvrir les fichiers montés.
- `remoteUser: node` fait travailler VS Code avec l'utilisateur `node`.
- `shutdownAction: stopCompose` arrête les services quand la session est fermée.
- La feature `github-cli` ajoute `gh` lors de la création par Dev Containers.
- `customizations` fournit les mêmes extensions et réglages à l'équipe.
  ESLint et Prettier devront aussi être configurés dans l'application ensuite.
- `forwardPorts` prépare l'accès aux futurs serveurs sur 3000 et 5173.
  Il ne démarre aucun serveur à lui seul.
- `postCreateCommand` déclare `/workspace` comme dépôt de confiance pour Git.
  L’installation npm sera ajoutée quand les workspaces et le lockfile existeront.

Les commentaires `//` sont acceptés dans ce fichier par Dev Containers : c'est
du JSON avec commentaires.

## Vérifier l'étape

Depuis le dossier WSL, `docker compose config --quiet` valide la configuration.
`docker compose build dev` vérifie la construction de l'image de base de travail.
Ces commandes seules ne valident pas les features et extensions de VS Code.

Dans VS Code ouvert sur WSL : `F1` puis
`Dev Containers: Reopen in Container`. Une fois connecté, lancer dans son terminal
les commandes de l'exemple du cours :

```bash
node -v          # v24…
npm -v           # 11…
psql --version   # 17… : le client seulement, la base arrive à l'étape suivante
uname -m         # aarch64 sur Mac Apple Silicon, x86_64 sur PC : même environnement
```

Après modification de la configuration, utiliser `Dev Containers: Rebuild Container`.

## Résultats du 8 novembre 2026

- Docker Engine `28.5.1` et Compose `v2.40.3-desktop.1` répondent depuis WSL.
- L'authentification SSH GitHub réussit pour `christopherDEPASQUAL`.
- La configuration Compose est valide ; les quatre fichiers correspondent
  aux exemples du cours.
- La construction échoue au téléchargement de l'image avec une erreur `EOF`
  de Docker Desktop vers `mcr.microsoft.com`. Un téléchargement direct par
  `docker pull` échoue également. Le registre répond depuis WSL et confirme
  que le tag `24-trixie` existe.
- Aucun conteneur de ce projet n'a donc démarré. Les versions des outils et
  l'ouverture dans Dev Containers restent à vérifier.

Pour reprendre : rétablir l'accès de Docker Desktop au registre Microsoft,
puis relancer `docker compose build dev`. Si l'erreur persiste, examiner la
connexion et les réglages proxy de Docker Desktop, puis son journal. Les
constats actuels ne permettent pas d'attribuer la panne à une cause précise.

## Vérification du 9 novembre 2026

Le blocage de construction décrit ci-dessus est résolu : la session s'exécute
bien dans le dev container sous Debian 13, utilisateur `node`, avec Node
`24.22.1`, npm `11.19.1` et psql `17.11`. Git et la CLI GitHub répondent.
Le service PostgreSQL est accessible depuis ce conteneur ; les deux questions
de démonstration sont présentes. Christopher a également confirmé leur
persistance avec une ligne temporaire après reconstruction depuis VS Code.
