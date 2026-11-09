# ADR 0001 — Suivre la stack de test du cours

- Date : 8 novembre 2026
- Statut : Accepté par Christopher
- Mise à jour : le choix de prolonger l'ancienne branche est remplacé par
  l'[ADR 0004](0004-branche-environnement.md). Les choix de stack restent acceptés.

## Contexte

Il faut réaliser l'atelier du matin et pouvoir expliquer chaque étape.
Le produit et sa stack définitive seront discutés avec les équipes Data et
Product Owner le lundi 9 novembre.

## Options envisagées

- Reprendre la stack de test fournie par le cours.
- Choisir dès maintenant les frameworks du produit.

## Décision

Suivre l'exemple : Express et TypeScript pour l'API, Vite et TypeScript pour
le front, workspaces npm, Node 24 sur Debian trixie dans un dev container,
et PostgreSQL 17. Réutiliser la branche distante `develop` existante et examiner
le travail déjà présent dans `origin/feature/devcontainer` avant de le prolonger.

## Conséquences

Les choix sont faciles à comparer aux consignes. Ils valident l'environnement
sans engager l'équipe sur les frameworks du produit. Garder les scripts
`dev` et `build`, les ports et les routes prévus permettra de changer de
framework plus tard. Le fournisseur d'IA reste traité dans l'ADR 0002.
