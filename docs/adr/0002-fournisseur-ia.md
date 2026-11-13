# ADR 0002 — Choisir le fournisseur d'IA de l'application

- Date : 8 novembre 2026
- Statut : Accepté par Christopher le 9 novembre 2026

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

## Proposition initiale du 8 novembre

Pour tester la chaîne avant de figer le choix du produit, essayer Ollama sur
la machine hôte avec le petit modèle du cours si le matériel convient.
Cette proposition ne constitue pas une décision d'installation.
Le poste annonce 32 Go de RAM ; l'accélération GPU et la performance réelle
du modèle ne sont pas encore vérifiées.

## Décision du 9 novembre

Christopher choisit Ollama installé sur Windows, conformément à l'option
recommandée par le cours. Le modèle de test est `llama3.2:1b` : il permet de
vérifier la chaîne complète avec un téléchargement d'environ 1,3 Go et une
qualité de réponse modeste. Ce modèle reste à évaluer pour le produit final.

L'API utilise l'exemple compatible OpenAI du cours : appel HTTP avec `fetch`
vers `/v1/chat/completions`. `AI_BASE_URL`, `AI_MODEL` et `AI_API_KEY` viennent
de `api/.env`. Depuis le conteneur, l'hôte s'appelle `host.docker.internal`.

Ollama est le serveur qui exécute le modèle ; Llama 3.2 est le modèle qui génère
les réponses. L'application Windows permet de profiter du matériel de l'hôte
sans ajouter un service Ollama au Compose commun. La disponibilité et
l'utilisation réelle du GPU devront être vérifiées sur le poste.

## Conséquences

Il faut installer Ollama et télécharger le modèle sur chaque poste qui développe
avec cette configuration. Le service local et le modèle doivent être disponibles
pour répondre. Il n'y a pas de facturation par appel en local ; il reste un coût
en stockage, mémoire, calcul et électricité. Les requêtes de ce modèle local
restent traitées sur le poste.

Le serveur reçoit une question sans historique de conversation. La réponse
complète est attendue avant l'enregistrement en base et le retour au navigateur.
Le modèle n'utilise pas de recherche documentaire ni de recherche vectorielle
à cette étape. Le besoin éventuel de pgvector relève d'une décision distincte.

L'application lit sa configuration depuis les variables d'environnement.
Le choix du fournisseur ne doit pas imposer de réécrire le front ou la base.
Les clés éventuelles restent dans le `.env` local, hors de Git.

Sources : [barème](https://learn.glassworks.tech/fullstack-setup/planning),
[options IA du cours](https://learn.glassworks.tech/fullstack-setup/environnement/ia).
