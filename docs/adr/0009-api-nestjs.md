# ADR 0009 — Structurer l’API applicative avec NestJS

- Date : 10 novembre 2026
- Statut : Acceptée
- Décideurs : les deux Tech leads, avec la Data pour la frontière entre services

## Contexte

`api/src/index.ts` contenait trois routes Express, un accès PostgreSQL via `pg`
et un appel au fournisseur IA. Le prototype doit qualifier puis enregistrer un
brief et dialoguer avec la brique Python. Les deux Tech leads maîtrisent NestJS.
Le service FastAPI et le moteur Data existent dans `feature/data-brique` ; ils
restent sous la responsabilité Data et ne sont pas réécrits pour changer le
framework applicatif.

## Options

1. **Express organisé en modules internes.** Réutilise directement les routes,
   dépendances et scripts existants. L’équipe choisit elle-même les conventions
   de validation, de découpage, de configuration et de documentation.
2. **NestJS en TypeScript.** Contrôleurs, services et injection de dépendances
   donnent un cadre commun aux deux Tech leads ; validation et génération OpenAPI
   disposent d’intégrations officielles. Il faut migrer les routes, les erreurs,
   le chargement d’environnement et le build, avec davantage de conventions et
   de dépendances. Le gain de performance n’est pas un motif démontré du choix.

## Décision

Retenir NestJS pour l’API applicative dans `api/`, compte tenu des compétences
confirmées et du travail partagé sur plusieurs responsabilités métier. Conserver
la base PostgreSQL commune aux Data et aux Tech leads et l’interface HTTP de la
brique Data Python/FastAPI. La connexion Data à PostgreSQL reste à intégrer et
à vérifier dans sa branche.

La migration est réalisée : NestJS 12 (ESM, Vitest) fournit le socle de `api/`,
l’ancien `src/index.ts` Express est supprimé. Le préfixe global `/api` est défini
dans `main.ts` afin de préserver le contrat `openapi.yaml`. Les routes
`GET /api/health` et `GET|POST /api/questions` sont portées dans
`HealthController` et `QuestionsController`, avec un filtre d’exception global
qui préserve le format `{ error }`. `pg` est conservé comme dépendance
d’exécution ; `@types/pg` comme dépendance de développement.

La migration doit préserver le contrat de test `openapi.yaml` ou en documenter
explicitement les changements. Elle vérifie les routes, codes d’erreur,
configuration, scripts npm et CI. L’ADR 0001 reste l’historique de la stack
d’atelier.

Le relais `POST /api/conversation` utilise HTTP/JSON vers Python : il renvoie
200 et valide le snapshot avec un contrat Zod pur partagé avec React. Les champs
Data additionnels sont conservés. Le refus d’une entrée (400/422 Data → 422)
reste distinct d’une panne (5xx/429 Data → 503), d’un corps inexploitable (502)
et d’un délai dépassé, corps inclus (504). Le délai serveur configurable reste
borné à 120 secondes, avec 30 secondes par défaut. Ce raccordement ajoute un
relais au socle, sans persister la conversation ni créer de commande.

## Conséquences

- Conventions communes pour séparer traitement HTTP, logique et accès aux services.
- Coût engagé : scaffold NestJS, migration du point d’entrée, suppression du socle
  Express, portage des routes `health` et `questions`, tests unitaires et e2e.
- Une interface et deux services restent possibles dans un dépôt commun ; NestJS
  n’impose ni microservices supplémentaires, ni nouvel ORM, ni seconde base.
- À revoir si le coût de migration menace la tranche verticale ou si les besoins
  validés restent limités aux quelques routes actuelles.

Sources : [NestJS et son architecture](https://docs.nestjs.com/),
[validation](https://docs.nestjs.com/techniques/validation),
[génération OpenAPI](https://docs.nestjs.com/openapi/introduction).
