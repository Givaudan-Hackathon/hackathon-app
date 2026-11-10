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

| Partie           | Code actuellement présent                                  | Proposition pour le produit                                 |
| ---------------- | ---------------------------------------------------------- | ----------------------------------------------------------- |
| Interface `web/` | Vite et TypeScript, formulaire de test                     | React avec Vite et TypeScript, ADR 0008                     |
| API `api/`       | Express/TypeScript, PostgreSQL et appel IA                 | NestJS/TypeScript, ADR 0009                                 |
| Data             | Python/FastAPI, moteur et tests dans `feature/data-brique` | Service Python conservé ; intégration à relire avec la Data |
| Organisation     | Workspaces npm `api/` et `web/`, base dans `db/`           | Dépôt commun par composant, ADR 0007                        |

Les deux Tech leads maîtrisent React et NestJS. Les ADR 0007 à 0010 restent au
statut **Proposée**. Cette branche prépare la documentation et le contrat de m1 ;
les migrations React/NestJS et l’intégration de la branche Data ne sont pas
réalisées par la présence de ces documents.

Le socle de test actuel affiche l’état de PostgreSQL et les échanges enregistrés.
Son formulaire appelle `POST /api/questions`, interroge Ollama puis conserve la
réponse. Ce test technique ne démontre pas encore le parcours de brief client.
Ollama Windows avec `llama3.2:1b` est le choix d’atelier décrit dans l’ADR 0002 ;
le fournisseur et le modèle du produit restent à évaluer avec la Data.

## Organisation des composants

```text
web/                     Interface et dépendances npm du front
api/                     API applicative et dépendances npm du back
  src/index.ts           Routes du socle Express actuel
data-brique/             Source Data dans feature/data-brique, à intégrer
  api/                   API FastAPI
  src/                   Moteur Python
  notebooks/             Expérimentations
  scripts/               Préparation des données
  tests/                 Tests Python
  data/                  Échantillons utilisés par le moteur
db/init/                 Schéma SQL et données initiales du socle
scripts/                 Vérifications transversales
docs/adr/                Décisions et alternatives
.github/                 CI, formulaires et responsabilités de revue
.devcontainer/           Environnement de référence
compose.yaml             Dev container et PostgreSQL actuels
openapi.yaml             Contrat des trois opérations de l’API actuelle
AGENTS.md                Instructions adaptées aux assistants de code
```

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

Ouvrir [le front Vite](http://localhost:5173). Il doit afficher l’état de l’API,
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

La source Data examinée est `feature/data-brique` au commit `148f6e4`. Elle
expose `/sante` et `/recommander`, avec son propre contrat et ses dépendances.
Le script suivant vérifie un service Data déjà lancé :

```bash
node scripts/verifier-api-data.mjs http://127.0.0.1:8000
```

Les résultats de l’essai et la procédure de reproduction sont dans le ticket #13.
L’intégration de l’API applicative vers Data relève du
[Spike #12](https://github.com/Givaudan-Hackathon/hackathon-app/issues/12).
Les contrôles Python et le démarrage commun seront ajoutés avec l’intégration
Data ; la CI actuelle vérifie les workspaces TypeScript.

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
