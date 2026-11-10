# ADR 0005 — Collaboration et dépôt public

- Date : 9 novembre 2026
- Statut : Accepté ; passage en public explicitement autorisé par Christopher
- Mise à jour : la séquence d'intégration et le calendrier d'exigence du check
  sont remplacés par l'[ADR 0006](0006-integration-sequentielle.md).

## Contexte et options

L'atelier 2 demande des équipes, des branches protégées, des revues et une CI.
L'organisation utilise GitHub Free. GitHub a refusé les rulesets sur le dépôt
privé avec une erreur 403. Les options étaient de garder le dépôt privé avec
une offre compatible, ou de rendre le dépôt public pour conserver le plan gratuit.

## Décisions

Avec l'accord explicite de Christopher, rendre le dépôt public sans achat.
Le code et l'historique versionnés deviennent visibles. Les `.env`, les données
PostgreSQL et les modèles locaux ne sont pas versionnés. Le contrôle des changements
de l'historique n'a détecté ni clé privée ni jeton reconnaissable avant publication.

Conserver les équipes et leurs membres déjà créés : tech-leads et data en Write,
product en Triage, evaluation en Admin. `glassworks` est déjà dans evaluation.
Les droits de base restent Read et la suppression des dépôts par les membres
reste désactivée. Le type d'issue Spike existe déjà.

Utiliser `develop` par défaut, squash pour intégrer une tâche, merge commit pour
intégrer `develop` à `main`, et supprimer automatiquement les branches fusionnées.
Le ruleset protège `main` et `develop` : suppression et force-push interdits,
PR obligatoire avec une approbation, approbations périmées révoquées après un
nouveau commit, revue CODEOWNERS et check `qualite`. La liste de bypass est vide.
Le check a été ajouté seulement après une première exécution verte réelle.

Recopier les exemples ESLint, Prettier, Husky/lint-staged et GitHub Actions du
professeur. Seule adaptation de règle : les paramètres préfixés par `_` peuvent
être inutilisés. Express exige quatre paramètres pour reconnaître son middleware
d'erreur, même quand `_next` n'est pas appelé. Les autres variables inutilisées
restent interdites. Prettier traite le style ; ESLint traite les erreurs probables.

La CI reprend `node:24-trixie`, `actions/checkout@v7` et le job `qualite` :
installation, lint, formatage et build. Elle ne démarre pas PostgreSQL ni Ollama,
conformément au chapitre CI ; la preuve de la chaîne applicative relève de l'atelier 1.

## Séquence initiale de revue — remplacée par l'ADR 0006

La PR #2 de l'atelier 1 attend la revue humaine. La branche `feature/collaboration`
part donc de `feature/environnement-cours`, dans une copie isolée, et reprend les
trois étapes du cours en trois commits. La PR #3 cible temporairement cette branche.

Fusionner la PR #3 d'abord ajoute le workflow à la PR #2, qui peut alors obtenir
le check exigé pour entrer dans `develop`. Cela évite d'exiger un workflow absent
de sa branche, sans bypass. Les fusions restent à la main des relecteurs.

## Conséquences

Le hook vérifie le commit ; la CI revérifie tout le projet, car un hook peut être
absent ou contourné. GitHub interdit l'approbation de sa propre PR : un autre
membre doit relire. L'équipe tech-leads compte actuellement Christopher seul ;
ajouter les autres tech leads lorsqu'ils seront connus permettra les revues
des futurs changements soumis à CODEOWNERS.

Les résultats réels et les étapes humaines restantes sont dans le
[suivi de l'atelier 2](../SUIVI-APRES-MIDI.md).

Sources : [atelier](https://learn.glassworks.tech/fullstack-setup/collaboration/atelier),
[GitFlow](https://learn.glassworks.tech/fullstack-setup/collaboration/gitflow),
[qualité](https://learn.glassworks.tech/fullstack-setup/collaboration/qualite),
[CI](https://learn.glassworks.tech/fullstack-setup/collaboration/ci),
[rulesets GitHub](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets).
