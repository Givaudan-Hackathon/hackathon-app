# Journal des décisions (ADR)

Un ADR (_Architecture Decision Record_) conserve le contexte, les options,
la décision et ses conséquences. Il explique pourquoi le projet évolue ainsi.
Git conserve les modifications des fichiers ; la checklist de la matinée suit
les tâches et les vérifications. Ces trois outils sont complémentaires.

| ADR                                           | Sujet                                              | Statut                                               |
| --------------------------------------------- | -------------------------------------------------- | ---------------------------------------------------- |
| [0001](0001-environnement-du-cours.md)        | Suivre la stack de test du cours                   | Accepté                                              |
| [0002](0002-fournisseur-ia.md)                | Ollama sur Windows avec llama3.2:1b pour l'atelier | Accepté le 9 novembre par Christopher                |
| [0003](0003-travail-dans-wsl.md)              | Travailler dans le système de fichiers WSL         | Accepté                                              |
| [0004](0004-branche-environnement.md)         | Reprendre l'environnement sur une branche dédiée   | Accepté ; remplace le choix de branche de l'ADR 0001 |
| [0005](0005-collaboration-et-depot-public.md) | Collaboration, qualité et dépôt public             | Accepté ; visibilité autorisée par Christopher       |
| [0006](0006-integration-sequentielle.md)      | Intégration séquentielle des ateliers dans develop | Accepté ; remplace l’ordre de revue de l’ADR 0005    |

Propositions à relire pour le produit et m1 :

- [0007 — Organisation du dépôt](0007-organisation-du-depot.md) : proposée.
- [0008 — Interface React avec Vite](0008-interface-react.md) : proposée, [architecture du prototype précisée](../ARCHITECTURE-WEB.md), migration dans le ticket #20.
- [0009 — API applicative NestJS](0009-api-nestjs.md) : proposée, migration à réaliser.
- [0010 — Contrat OpenAPI versionné](0010-contrat-openapi.md) : proposée ; référence `openapi.yaml`.

Les preuves et la procédure du choix de dépôt restent dans le
[Spike #13](https://github.com/Givaudan-Hackathon/hackathon-app/issues/13).
Les propositions ne remplacent pas les ADR acceptés tant que la décision n’est pas validée.

Créer un fichier numéroté pour chaque décision technique significative avec :
date, statut, contexte, options envisagées, décision et conséquences.
Un statut « Accepté » indique un choix, pas une installation terminée.
Si une décision acceptée change, ajouter un nouvel ADR et indiquer dans l'ancien
qu'il est remplacé, avec un lien. Conserver les raisons du choix initial.

Référence : [Michael Nygard, Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).
