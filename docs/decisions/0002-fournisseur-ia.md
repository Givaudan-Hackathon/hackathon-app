# ADR 0002 — Choisir le fournisseur d'IA de l'application

- Date : 8 novembre 2026
- Statut : Proposé, décision à prendre avec l'équipe le lundi 9 novembre

## Contexte

Codex aide à développer depuis l'éditeur. Sa présence sur le poste ne connecte
pas l'application à un fournisseur d'IA. L'atelier demande qu'une requête parte
du front, passe par l'API, obtienne une réponse de l'IA et soit enregistrée dans
PostgreSQL.

Le barème prévoit 4 points pour la chaîne complète et 2 points pour justifier
les choix techniques, le fournisseur, le budget et les exclusions. Il ne prévoit
pas de bonus spécifique pour une IA locale.

## Options envisagées

- Ollama sur la machine hôte : modèle local, sans coût par appel, ressources
  matérielles et installation à prévoir.
- API commerciale : clé et budget à prévoir, sans exécuter le modèle localement.
- API de l'équipe Data/IA : contrat et disponibilité à convenir ensemble.
- Ollama dans un conteneur optionnel : variante du cours avec contraintes de
  performance à examiner.

## Proposition

Pour tester la chaîne avant de figer le choix du produit, essayer Ollama sur
la machine hôte avec le petit modèle du cours si le matériel convient.
Cette proposition ne constitue pas une décision d'installation.
Le poste annonce 32 Go de RAM ; l'accélération GPU et la performance réelle
du modèle ne sont pas encore vérifiées.

## Conséquences à examiner

L'application devra lire sa configuration depuis les variables d'environnement.
Le choix du fournisseur ne doit pas imposer de réécrire le front ou la base.
Les clés éventuelles restent dans le `.env` local, hors de Git.

Sources : [barème](https://learn.glassworks.tech/fullstack-setup/planning),
[options IA du cours](https://learn.glassworks.tech/fullstack-setup/environnement/ia).
