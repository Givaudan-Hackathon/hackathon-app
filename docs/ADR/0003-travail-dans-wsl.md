# ADR 0003 — Travailler dans le système de fichiers WSL

- Date : 8 novembre 2026
- Statut : Accepté par Christopher

## Contexte

Le dossier initial est sur le disque Windows. Le cours demande un projet dans
le système de fichiers Linux de WSL pour les performances et les permissions
de PostgreSQL. Ubuntu et Docker depuis Ubuntu fonctionnent déjà.

## Options envisagées

- Garder la copie de travail sous `C:\Users\Christopher\Desktop`.
- Préparer une copie dans le répertoire personnel Ubuntu.

## Décision

Utiliser `/home/hristopherswl/projets/hackathon-app` comme future copie de travail.
Conserver le dossier Windows initial et copier les fichiers, y compris Git et
les modifications locales. Ne pas écraser un dossier cible existant.

## Conséquences

Ouvrir la copie Ubuntu avec VS Code en mode WSL, puis s'attacher au dev container.
Les deux copies ne se synchronisent pas automatiquement : après la bascule,
travailler dans la copie WSL. Le suivi indique séparément si la copie et ses
vérifications ont effectivement été réalisés.
