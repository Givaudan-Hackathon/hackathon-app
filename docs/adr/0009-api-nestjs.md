# ADR 0009 — Structurer l’API applicative avec NestJS

- Date : 10 novembre 2026
- Statut : Proposée ; migration non réalisée dans cette PR
- Décideurs : les deux Tech leads, avec la Data pour la frontière entre services

## Contexte

`api/src/index.ts` contient actuellement trois routes Express, un accès PostgreSQL
via `pg` et un appel au fournisseur IA. Le prototype doit qualifier puis enregistrer
un brief et dialoguer avec la brique Python. Les deux Tech leads maîtrisent NestJS.
Le service FastAPI et le moteur Data existent dans `feature/data-brique` ; ils
restent sous la responsabilité Data et ne doivent pas être réécrits pour changer
le framework applicatif.

## Options

1. **Express organisé en modules internes.** Réutilise directement les routes,
   dépendances et scripts existants. L’équipe choisit elle-même les conventions
   de validation, de découpage, de configuration et de documentation.
2. **NestJS en TypeScript.** Contrôleurs, services et injection de dépendances
   donnent un cadre commun aux deux Tech leads ; validation et génération OpenAPI
   disposent d’intégrations officielles. Il faut migrer les routes, les erreurs,
   le chargement d’environnement et le build, avec davantage de conventions et
   de dépendances. Le gain de performance n’est pas un motif démontré du choix.

## Décision proposée

Retenir NestJS pour l’API applicative dans `api/`, compte tenu des compétences
confirmées et du travail partagé sur plusieurs responsabilités métier. Conserver
PostgreSQL et l’interface HTTP de la brique Data Python/FastAPI.

La migration doit préserver le contrat de test `openapi.yaml` ou en documenter
explicitement les changements. Elle vérifiera les routes, codes d’erreur,
configuration, scripts npm et CI. Cette PR de documentation ne déclare pas NestJS
installé ; le socle Express reste exécutable pour m1 tant que la migration n’est
pas intégrée. L’ADR 0001 reste l’historique de la stack d’atelier.

## Conséquences

- Conventions communes pour séparer traitement HTTP, logique et accès aux services.
- Coût accepté : migration et vérifications avant toute démonstration de NestJS.
- Une interface et deux services restent possibles dans un dépôt commun ; NestJS
  n’impose ni microservices supplémentaires, ni nouvel ORM, ni seconde base.
- À revoir si le coût de migration menace la tranche verticale ou si les besoins
  validés restent limités aux quelques routes actuelles.

Sources : [NestJS et son architecture](https://docs.nestjs.com/),
[validation](https://docs.nestjs.com/techniques/validation),
[génération OpenAPI](https://docs.nestjs.com/openapi/introduction).
