# ADR 0004 — Reprendre l'environnement sur une branche dédiée

- Date : 8 novembre 2026
- Statut : Accepté à la suite de la demande de Christopher
- Remplace la consigne de prolonger `origin/feature/devcontainer` dans l'ADR 0001

## Contexte

Christopher demande de supprimer l'ancienne branche et de poursuivre en
reproduisant les exemples du professeur. `main` et `develop` existent déjà et
pointent sur le même commit lors de cette reprise.

## Options envisagées

- Continuer directement sur `main`.
- Travailler directement sur `develop`.
- Créer une branche dédiée depuis `develop`, puis proposer une pull request.

## Décision

Supprimer `feature/devcontainer` sur GitHub et repartir de `origin/develop`
sur `feature/environnement-cours`. Le cours décrit le parcours
`feature/*` → pull request vers `develop` → pull request vers `main` avant une démo.

Recopier les exemples du dev container depuis le cours. Garder les explications
et les résultats des vérifications dans la documentation du dépôt. Les
modifications locales existantes sont conservées pendant le changement de branche.

## Conséquences

`main` conserve les versions démontrables ; `develop` sert à l'intégration ;
notre branche isole cette tâche d'environnement pour la relire. Aucun merge
n'est effectué dans cette reprise. Les protections de branches et le changement
de branche par défaut appartiennent au chapitre de collaboration à venir.

Le commit `cf4b7e8` de l'ancienne branche a été sauvegardé avant sa suppression
dans `/tmp/hackathon-devcontainer-avant-suppression.bundle`. Cette sauvegarde
locale temporaire n'est pas un livrable du dépôt.

Le cours commence avec un dépôt vide. Ici, on conserve l'historique et le remote
existants : on ne répète pas `git init`, `git remote add origin` ni la création
de `develop`. Cette adaptation évite de refaire une étape déjà accomplie.

Source : [GitFlow et branches protégées — cours HETIC](https://learn.glassworks.tech/fullstack-setup/collaboration/gitflow).
