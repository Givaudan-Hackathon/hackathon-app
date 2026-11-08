# Journal des décisions (ADR)

Un ADR (*Architecture Decision Record*) conserve le contexte, les options,
la décision et ses conséquences. Il explique pourquoi le projet évolue ainsi.
Git conserve les modifications des fichiers ; la checklist de la matinée suit
les tâches et les vérifications. Ces trois outils sont complémentaires.

| ADR | Sujet | Statut |
| --- | --- | --- |
| [0001](0001-environnement-du-cours.md) | Suivre la stack de test du cours | Accepté |
| [0002](0002-fournisseur-ia.md) | Choisir le fournisseur d'IA de l'application | Proposé, à décider avec l'équipe |
| [0003](0003-travail-dans-wsl.md) | Travailler dans le système de fichiers WSL | Accepté |
| [0004](0004-branche-environnement.md) | Reprendre l'environnement sur une branche dédiée | Accepté ; remplace le choix de branche de l'ADR 0001 |

Créer un fichier numéroté pour chaque décision technique significative avec :
date, statut, contexte, options envisagées, décision et conséquences.
Un statut « Accepté » indique un choix, pas une installation terminée.
Si une décision acceptée change, ajouter un nouvel ADR et indiquer dans l'ancien
qu'il est remplacé, avec un lien. Conserver les raisons du choix initial.

Référence : [Michael Nygard, Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).
