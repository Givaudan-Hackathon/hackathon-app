# Hackathon HETIC × Givaudan 2026 — Équipe 15

Nous développons une plateforme de commande IA pour les **petits clients qui
souhaitent décrire un projet d’arômes alimentaires avec leurs propres mots**,
clarifier leur besoin et déposer un brief structuré. Le parcours est à valider
avec les Product et les utilisateurs : les hypothèses et les preuves métier
restent dans le workbook d’équipe.

L’équipe comprend **deux Tech leads, deux Data et deux Product**. Le développement
sert au prototype commun. Le [Spike #13](https://github.com/Givaudan-Hackathon/hackathon-app/issues/13)
compare l’organisation des sources et conserve les essais. Les décisions durables
se trouvent dans le [journal des ADR](docs/adr/README.md).

## État du code et choix proposés

| Partie           | Code actuellement présent                        | Proposition pour le produit                      |
| ---------------- | ------------------------------------------------ | ------------------------------------------------ |
| Interface `web/` | React/TypeScript/Tailwind, parcours simulé       | Branchement à l’API applicative, ADR 0008        |
| API `api/`       | NestJS 12, PostgreSQL et appel IA                | Migration du socle réalisée, ADR 0009 acceptée   |
| Data             | Python/FastAPI dans `data-brique/`               | Relais Nest–Python à réaliser dans le ticket #31 |
| Organisation     | Workspaces npm `api/` et `web/`, base dans `db/` | Dépôt commun par composant, ADR 0007             |

Les deux Tech leads maîtrisent React et NestJS. Le choix React/Tailwind est
confirmé par Christopher pour le prototype et réalisé dans le ticket #20.
L’ADR 0009 est acceptée et la migration du socle API vers NestJS est fusionnée
(PR #27). Les ADR 0007 et 0010 restent proposés. La présence des sources Python
ne constitue pas encore un branchement du parcours React à leur conversation.

Le diagnostic API affiche l’état de PostgreSQL et les échanges enregistrés.
Son formulaire appelle `POST /api/questions`, interroge Ollama puis conserve la
réponse. Ce test technique ne démontre pas encore le parcours de brief client.
Ollama Windows avec `llama3.2:1b` est le choix d’atelier décrit dans l’ADR 0002 ;
le fournisseur et le modèle du produit restent à évaluer avec la Data.

## Prototype client React

Le [cadrage web](docs/ARCHITECTURE-WEB.md), livré dans le ticket #19 / PR #22,
fixe les fonctionnalités, l’état du parcours et les adaptateurs. Le
[ticket #20](https://github.com/Givaudan-Hackathon/hackathon-app/issues/20)
réalise le parcours invité : décrire un projet, préciser son besoin, comparer
jusqu’à trois pistes illustrées, relire et simuler une demande. Cinq ingrédients
sont couverts : citron vert, citron jaune, pamplemousse, vanille et fraise.

Le parcours affiche cinq étapes nommées et navigables : Votre idée, Affiner,
Choisir, Paiement et Votre demande. Les propositions précèdent la conversation
à l’étape Choisir. Revenir en arrière conserve la description, le message en
cours et les coordonnées ; modifier le brief invalide sa sélection et son
paiement fictif.

Une demande d’échantillon est précédée d’un **paiement fictif de 10 €**, montant
de démonstration choisi par Christopher. Aucune donnée bancaire n’est saisie,
aucun prestataire n’est appelé et aucun débit n’a lieu. Le panneau permet de
tester un paiement accepté ou refusé. Un paiement réussi débloque le formulaire,
puis le client confirme explicitement sa demande. Une demande de contact avec
un expert reste accessible sans paiement.

```bash
npm ci
npm run dev -w web
```

Ouvrir http://localhost:5173. Le prototype fonctionne sans backend : réponses,
références et dépôts sont simulés en mémoire. Recharger la page réinitialise
le projet. Les coordonnées ne sont ni transmises ni stockées ; aucun e-mail,
échantillon ou commande n’est envoyé. Les photos et les fontes sont locales ;
les [prompts des visuels](web/src/assets/README.md) sont conservés.

Le contrat V2 de la [PR Data #18](https://github.com/Givaudan-Hackathon/hackathon-app/pull/18)
a servi à construire le simulateur (source `09d22f3`). La brique Python est
maintenant présente dans le dépôt, mais le parcours reste simulé : le relais
Nest–Python est suivi dans #31 et le raccordement HTTP du front dans #32.
Les composants dépendent d’une interface de service indépendante des fixtures.
Le brouillon Data reste distinct du dépôt applicatif et de l’acceptation
commerciale d’une commande.

Le test technique historique est accessible à http://localhost:5173/diagnostic.html
et requiert l’API NestJS/PostgreSQL démarrée. Le build produit les deux pages.
La préparation Compose et le tag `m2` sont suivis dans le
[ticket #21](https://github.com/Givaudan-Hackathon/hackathon-app/issues/21) : ce
front simulé ne vaut pas intégration de la tranche jusqu’aux données.

```bash
npm run lint
npm run format:check
npm run typecheck
npm test
npm run build
```

`npm test` exécute les tests unitaires NestJS et les tests métier du front.

Pour les vérifications navigateur, installer le Chromium Playwright et ses
bibliothèques système dans l’environnement de test, puis lancer `npm run test:e2e`.
Les tests couvrent les formats 1440 et 360 px. Les captures et traces restent
sous `.scratch/qa/`. Les validations Product et la revue restent humaines.
Si le prototype est déjà ouvert sur 5173, utiliser
`GIVAUDAN_TEST_PORT=5184 npm run test:e2e` pour tester cette copie séparément.

## Organisation des composants

```text
web/                     Prototype React/Tailwind et dépendances npm du front
api/                     API NestJS et dépendances npm du back
  src/main.ts            Bootstrap NestJS et préfixe /api
  src/app.module.ts      Modules Database, Health et Questions
  src/database/          Pool PostgreSQL partagé
  src/health/            GET /api/health
  src/questions/         GET|POST /api/questions et fournisseur IA
  src/shared/            Filtre d’erreurs { error }
data-brique/             Service Python/FastAPI, relais Nest à réaliser
  api/                   API FastAPI
  src/                   Moteur Python
  notebooks/             Expérimentations
  scripts/               Préparation des données
  tests/                 Tests Python
  data/                  Échantillons utilisés par le moteur
db/                      PostgreSQL commun aux Data et aux Tech leads
  init/                  Schéma SQL et données initiales partagés
scripts/                 Vérifications transversales
docs/adr/                Décisions et alternatives
.github/                 CI, formulaires et responsabilités de revue
.devcontainer/           Environnement de référence
compose.yaml             Dev container et PostgreSQL actuels
openapi.yaml             Contrat des trois opérations de l’API actuelle
AGENTS.md                Instructions adaptées aux assistants de code
```

La base PostgreSQL définie par `db/` et `compose.yaml` est commune à l’API
applicative et au service Data. Les Data et les Tech leads coordonnent ses
évolutions de schéma et ses données initiales ; les responsabilités de revue
sont partagées. Chaque environnement de développement démarre son instance
locale via Compose. La connexion du service Data à cette base reste à intégrer
et à vérifier dans sa branche.

Chaque service conserve ses dépendances. Les workspaces npm ne remplacent pas
l’environnement virtuel Python. Les rôles servent à répartir les responsabilités
et les revues ; les dossiers correspondent aux composants.

Les consignes des assistants suivent la même organisation :

```text
AGENTS.md                  Règles communes au dépôt
web/AGENTS.md              Consignes de l’interface, maintenues par les Tech leads
api/AGENTS.md              Consignes de l’API, maintenues par les Tech leads
data-brique/AGENTS.md      À rédiger et maintenir par les Data dans leur branche
```

Le fichier racine donne le contexte et les règles partagées. Chaque fichier local
précise les chemins, commandes et contraintes de son composant, sans recopier le
README ni les ADR. Les modifications du fichier Data sont relues par l’équipe
`data` via CODEOWNERS ; cette règle de revue ne crée pas de droits d’accès séparés.

## Démarrer le socle existant

Prérequis : Git, Docker Desktop, VS Code et Dev Containers. Sous Windows,
utiliser le système de fichiers Linux de WSL. L’image de référence fournit
Node 24, npm 11 et le client PostgreSQL 17.

1. Cloner le dépôt, puis ouvrir son dossier dans VS Code.
2. Lancer **Dev Containers: Reopen in Container**. L’installation automatique
   exécute `npm ci` et crée `api/.env` depuis `api/.env.example` seulement si le
   fichier est absent. Après une modification du conteneur ou de Compose,
   utiliser **Dev Containers: Rebuild Container**.
3. Dans le terminal du conteneur, à la racine :

   ```bash
   npm run dev
   ```

Ouvrir [le diagnostic API](http://localhost:5173/diagnostic.html). Il doit afficher l’état de l’API,
la version PostgreSQL et les derniers échanges. Les ports 3000 et 5173 sont
transférés par VS Code ; vérifier l’onglet **Ports** si nécessaire. Ctrl+C arrête
les serveurs. `npm run dev -w api` et `npm run dev -w web` les lancent séparément.

Pour utiliser le formulaire IA, démarrer Ollama sur l’hôte et installer le modèle
indiqué dans `api/.env`. Le conteneur utilise `host.docker.internal` pour joindre
l’hôte. Consulter le [guide IA](docs/IA.md). Les secrets et la configuration locale
restent dans `api/.env`, ignoré par Git.

```bash
curl --fail http://localhost:3000/api/health
curl --fail http://localhost:3000/api/questions
npm run lint
npm run format:check
npm run build
```

Le [contrat OpenAPI](openapi.yaml), référencé par l’[ADR 0010](docs/adr/0010-contrat-openapi.md),
décrit les routes réellement implémentées. Une migration de framework doit
préserver ce contrat ou rendre ses changements explicites.

`db/init/` n’est exécuté qu’à l’initialisation de PostgreSQL : changer un script
ne modifie pas une base existante. Les données locales sont dans `db/data/`,
ignoré par Git. Voir le [guide PostgreSQL](docs/BASE-DE-DONNEES.md).

Le Compose actuel démarre `dev` et `db`, puis attend le lancement manuel des
serveurs. Le démarrage complet avec `docker compose up` seul reste à préparer
pour la tranche verticale m2.

## Travail avec la Data

Les sources Data sont fusionnées dans `data-brique/`. Le service expose
`/sante`, `/recommander` et `/conversation`, avec son propre environnement
Python. Son [contrat conversationnel](data-brique/docs/contrat_api.md) décrit
les snapshots, les étapes et les brouillons renvoyés au front.
Le script suivant vérifie un service Data déjà lancé :

```bash
node scripts/verifier-api-data.mjs http://127.0.0.1:8000
```

Les résultats de l’essai et la procédure de reproduction sont dans le ticket #13.
Le [ticket #31](https://github.com/Givaudan-Hackathon/hackathon-app/issues/31)
porte le relais Nest vers Python ; #32 porte son consommateur React. Le
[Spike #12](https://github.com/Givaudan-Hackathon/hackathon-app/issues/12)
conserve l’étude initiale. Les dépendances et tests Python restent séparés
des workspaces npm. Le démarrage commun relève de #21.

## Collaboration et jalon m1

Une branche par ticket part de `develop`, puis une PR relue vise `develop`.
Les protections de branche et le check `qualite` restent applicables. Le tableau
[Hackathon](https://github.com/orgs/Givaudan-Hackathon/projects/1), ses critères
Ready/Done et le cycle ticket → PR sont décrits dans le
[guide du tableau](docs/TABLEAU-HACKATHON.md).

Pour m1, vérifier au commit retenu : au moins deux ADR dont un sur un composant,
`AGENTS.md` à la racine d’au moins 400 octets, un fichier OpenAPI et un ADR qui le
cite. Le Project doit contenir au moins trois tickets, être lié au dépôt et
lisible par `evaluation`. Fusionner les livrables et vérifier la CI avant de
publier le tag sur le `develop` retenu. La date limite est le 10 novembre à 18 h,
heure de Paris ; cette PR ne crée pas le tag et ne vaut pas acceptation des ADR
proposés. [Consignes d’évaluation](https://learn.glassworks.tech/fullstack-setup/hackathon/evaluation).
