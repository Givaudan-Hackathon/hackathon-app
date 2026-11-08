# Hackathon HETIC × Givaudan 2026

Dépôt collaboratif de l'application développée dans le cadre du hackathon HETIC × Givaudan 2026.

Pour l'atelier, nous suivons la stack de test du cours :

- API : Express et TypeScript, avec PostgreSQL 17 et Node 24.
- Front : Vite et TypeScript.
- IA : fournisseur à décider avec l'équipe ; essai local avec Ollama proposé.

L'installation est en cours. Les fichiers du dev container reprennent les exemples
du cours ; leur construction reste bloquée par un téléchargement Docker (`EOF`).
Consulter le [plan et les vérifications](docs/SUIVI-MATIN.md), le
[guide WSL](docs/WSL.md), les [explications du dev container](docs/DEVCONTAINER.md)
et le [journal des décisions (ADR)](docs/decisions/README.md).

Le travail en cours se fait sur `feature/environnement-cours`, créée depuis
`develop`. Les changements seront relus via une pull request vers `develop`,
puis intégrés à `main` pour une version démontrable, selon le
[GitFlow du cours](https://learn.glassworks.tech/fullstack-setup/collaboration/gitflow).
