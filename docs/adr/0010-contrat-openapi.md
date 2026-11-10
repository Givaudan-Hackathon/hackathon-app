# ADR 0010 — Versionner le contrat HTTP en OpenAPI

- Date : 10 novembre 2026
- Statut : Proposée ; contrat du socle existant fourni pour revue
- Décideurs : Tech leads, avec la Data lors des évolutions du contrat partagé

## Contexte

Le socle exposé par `api/src/index.ts` possède GET `/api/health`, GET
`/api/questions` et POST `/api/questions`. Le front les appelle via le proxy Vite.
Les migrations de framework doivent rendre visibles les changements de ces
interfaces. Le jalon m1 demande un fichier OpenAPI dans le dépôt et un ADR qui
le cite ; une page Swagger seule ne suffit pas.

## Options

1. **Documentation Markdown uniquement.** Simple à lire, mais sans schéma
   exploitable par les outils et avec un risque de divergence avec le code.
2. **Fichier OpenAPI versionné.** Schémas, exemples et codes HTTP relus dans la
   même PR que les routes ; validation automatique du document possible. Il faut
   maintenir le fichier et vérifier qu’il décrit réellement l’implémentation.

## Décision proposée

Versionner [`openapi.yaml`](../../openapi.yaml) à la racine, au format OpenAPI
3.1.1. Son périmètre initial correspond aux trois opérations du socle applicatif
actuel, avec leurs réponses et erreurs. Il ne prétend pas décrire des routes de
brief ou de commande qui ne sont pas encore implémentées.

Après migration NestJS, une génération depuis l’application pourra alimenter le
fichier versionné ; le diff restera relu. Le service Data conserve son propre
contrat : ses routes `/sante` et `/recommander` ne sont pas présentées comme des
routes Express. Son OpenAPI sera versionné lors de son intégration, en coordination
avec la Data et le Spike #12.

## Conséquences

- Le front et les relecteurs disposent d’une référence précise pour le socle.
- Coût accepté : mise à jour conjointe du code, du contrat et des exemples.
- La validité du YAML ne prouve pas l’intégration, la performance ou la pertinence
  métier ; ces éléments restent à vérifier par des essais dédiés.
- À revoir lors de l’ajout du parcours métier, d’une rupture de contrat ou du
  remplacement de l’API par une autre implémentation.

Sources : [OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html),
[critères m1](https://learn.glassworks.tech/fullstack-setup/hackathon/evaluation).
