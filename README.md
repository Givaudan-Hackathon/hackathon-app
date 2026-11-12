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
| API `api/`       | NestJS 12 (ESM, Vitest), PostgreSQL et appel IA            | NestJS/TypeScript, ADR 0009 (Acceptée)                      |
| Data             | Python/FastAPI, moteur et tests dans `feature/data-brique` | Service Python conservé ; intégration à relire avec la Data |
| Organisation     | Workspaces npm `api/` et `web/`, base dans `db/`           | Dépôt commun par composant, ADR 0007                        |

Les deux Tech leads maîtrisent React et NestJS. L’ADR 0009 (NestJS) est
**Acceptée** et la migration de l’API applicative est réalisée ; les ADR 0007,
0008 et 0010 restent au statut **Proposée**. La migration de l’interface React
(ADR 0008) et l’intégration de la branche Data ne sont pas encore réalisées.

Le socle actuel affiche l’état de PostgreSQL et les échanges enregistrés.
Son formulaire appelle `POST /api/questions`, interroge Ollama puis conserve la
réponse. Ce test technique ne démontre pas encore le parcours de brief client.
Ollama Windows avec `llama3.2:1b` est le choix d’atelier décrit dans l’ADR 0002 ;
le fournisseur et le modèle du produit restent à évaluer avec la Data.

## Prototype client : architecture puis réalisation

Le parcours retenu accompagne uniquement le petit client dans son projet d’arômes
alimentaires. La [référence d’architecture web](docs/ARCHITECTURE-WEB.md) décrit
la cible React/TypeScript/Tailwind, le simulateur et la frontière avec le service
Data. Elle ne change pas les dépendances actuellement installées.

- [#19 — Architecture web](https://github.com/Givaudan-Hackathon/hackathon-app/issues/19) : découpage, état et contrat.
- [#20 — Prototype client](https://github.com/Givaudan-Hackathon/hackathon-app/issues/20) : installation et parcours responsive illustré.
- [#21 — Préparation m2](https://github.com/Givaudan-Hackathon/hackathon-app/issues/21) : démarrage complet, démo et tag du commit montré.

Le contrat conversationnel V2 de la PR Data #18 a été consulté au commit
`0cec17f` ; la PR reste à relire et à intégrer séparément. Les pistes possèdent
un identifiant stable ; leurs images sont encore à `null`. Le premier lot web
prévoit donc cinq visuels locaux de démonstration et une image de remplacement.
La demande d’échantillons Data est un brouillon non envoyé, distinct d’un dépôt
applicatif et d’une commande acceptée par un commercial.

## Organisation des composants

```text
web/                     Interface et dépendances npm du front
api/                     API NestJS et dépendances npm du back
  src/main.ts            Bootstrap NestJS (préfixe /api, filtre d'erreurs)
  src/app.module.ts      Module racine (Database, Health, Questions)
  src/database/          Pool PostgreSQL partagé (PG_POOL)
  src/health/            GET /api/health
  src/questions/         GET|POST /api/questions (pg + IA)
  src/shared/            Filtre d'exception global { error }
data-brique/             Source Data dans feature/data-brique, à intégrer
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
