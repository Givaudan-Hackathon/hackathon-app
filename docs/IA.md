# Étape 8 — Ollama sur Windows

Source : [L'IA — cours HETIC](https://learn.glassworks.tech/fullstack-setup/environnement/ia).
Décision : [ADR 0002](ADR/0002-fournisseur-ia.md).

## La chaîne à comprendre

Le navigateur envoie `{ "question": "..." }` à `POST /api/questions`.
Vite transmet `/api` à Express pendant le développement. Express vérifie la
question, appelle Ollama, puis insère la question et la réponse dans PostgreSQL.
Il renvoie la ligne créée avec un statut HTTP 201. Le front recharge la liste.

Ollama est un serveur d'inférence : il charge et exécute le modèle
`llama3.2:1b` sur le poste Windows. Le modèle et le serveur ne sont pas le même
élément. La base conserve les échanges ; elle n'exécute pas le modèle.

## Ce qui reprend le cours

- Même modèle `llama3.2:1b` et mêmes variables `AI_BASE_URL`, `AI_MODEL`, `AI_API_KEY`.
- Même endpoint compatible OpenAI : `/v1/chat/completions`, appelé avec `fetch`.
- Même route `POST /api/questions` et insertion SQL paramétrée avec `$1`, `$2`.
- Même formulaire et rechargement de la liste après enregistrement.
- Bloc `extra_hosts` du cours dans le service `dev`, pour le nom de l'hôte.

Adaptations expliquées : on conserve les erreurs JSON de l'API et les messages
du front existants. Le serveur exige une question textuelle non vide, vérifie
la présence d'une réponse textuelle de l'IA et limite l'appel à 60 secondes.
Le bouton est désactivé pendant l'envoi pour éviter les doubles clics ; en cas
d'erreur, la question reste dans le champ. `stream: false` demande une seule
réponse JSON complète, au lieu de morceaux de texte à traiter progressivement.
Aucune bibliothèque d'IA supplémentaire n'est installée.

## Installer et vérifier Ollama

L'application Windows officielle est disponible sur
[ollama.com/download/windows](https://ollama.com/download/windows).
Elle installe le serveur et la commande `ollama` dans le compte Windows.

Dans un nouveau terminal **PowerShell Windows**, hors du conteneur, reprendre
les commandes du professeur :

```powershell
ollama --version
ollama pull llama3.2:1b
ollama run llama3.2:1b "Réponds en une phrase : qui es-tu ?"
```

Le téléchargement du modèle fait environ 1,3 Go. Le premier appel peut être
plus lent car il faut charger le modèle en mémoire. `ollama ps` indique si le
modèle utilise le processeur ou le GPU.

## Configurer l'API

Dans `api/.env`, conserver la connexion PostgreSQL et ajouter ces lignes :

```dotenv
AI_BASE_URL=http://host.docker.internal:11434/v1
AI_MODEL=llama3.2:1b
AI_API_KEY=
```

`host.docker.internal` désigne le poste Windows depuis le conteneur ; `localhost`
depuis le conteneur désignerait le conteneur lui-même. `/v1` sélectionne l'API
compatible OpenAI d'Ollama. Ce protocole commun ne signifie pas que les requêtes
sont envoyées à OpenAI. Ollama local n'exige pas de clé pour cet appel.

Le modèle de configuration versionné est `api/.env.example`. Un `.env` existant
n'est pas remplacé par `postCreateCommand` : les variables IA doivent donc être
ajoutées au fichier existant. Ne pas commiter ce fichier local.

## Vérifier depuis le dev container

Après l'ajout d'`extra_hosts`, reconstruire le conteneur avec
`Dev Containers: Rebuild Container`. Puis vérifier :

```bash
curl --fail http://host.docker.internal:11434/v1/models
```

La réponse doit lister `llama3.2:1b`. Si la connexion est refusée, vérifier
d'abord qu'Ollama fonctionne depuis PowerShell Windows. Examiner ensuite son
adresse d'écoute et la connexion entre Docker Desktop et l'hôte. Ne pas ouvrir
le service sur toutes les interfaces sans examiner le pare-feu et le réseau.

Relancer `npm run dev` après modification de `api/.env`, puis reprendre le test
du professeur dans un second terminal du conteneur :

```bash
curl --fail-with-body -X POST localhost:3000/api/questions \
  -H 'Content-Type: application/json' \
  -d '{"question": "Quelle est la capitale du Japon ?"}'
```

Ouvrir `http://localhost:5173`, poser une question et vérifier son apparition.
La preuve SQL est :

```bash
psql postgres://app:app@db:5432/app -c "SELECT id, question, answer FROM questions ORDER BY id DESC LIMIT 10"
```

## Comprendre un échec

| Statut | Signification |
| --- | --- |
| 400 | Question absente/non textuelle, ou corps JSON invalide |
| 502 | Erreur HTTP d'Ollama ou réponse inexploitable |
| 503 | Configuration IA absente ou serveur injoignable |
| 504 | L'appel IA a dépassé 60 secondes |

Une erreur IA n'insère aucune ligne en base. Une erreur PostgreSQL après la
génération échoue aussi côté navigateur : l'enregistrement fait partie de la
réussite de la demande.

Références : [compatibilité OpenAI](https://docs.ollama.com/api/openai-compatibility),
[Ollama sous Windows](https://docs.ollama.com/windows).

## Vérifications du 9 novembre 2026

- Ollama Windows `0.40.15` est disponible. Une installation existante a été
  détectée avant l'installation automatique et conservée. Le serveur natif a été
  démarré avec `ollama serve` ; il écoute sur `127.0.0.1:11434` et répond depuis
  le dev container via `host.docker.internal`, sans modification de son écoute.
- Le modèle `llama3.2:1b` a été téléchargé et apparaît dans `/v1/models`.
- La requête du professeur, envoyée via le proxy Vite, reçoit HTTP 201 en
  34 secondes au premier appel : « La capitale du Japon est Tokyo. ».
  L'échange est conservé sous l'identifiant 3 et relu dans PostgreSQL et par l'API.
- `ollama ps` indique `100% GPU`, environ 1,5 Go chargés et un contexte de
  4096 jetons sur ce poste. Ce constat ne garantit pas les performances d'un
  autre modèle ou d'une autre machine.
- Une instance Edge avec un profil temporaire affiche « API OK », le formulaire
  et la vraie réponse. Le profil temporaire est supprimé après ce contrôle.
- La compilation API/front et la validation Compose réussissent. Les erreurs
  400, 502, 503 et le délai réel de 60 secondes (504) ont été contrôlés avec un
  fournisseur simulé et des schémas SQL temporaires supprimés ensuite.
- La validation manuelle de Christopher et le test sur un clone neuf restent
  à effectuer. L'alias ajouté dans Compose sera pris en compte lors de la
  prochaine reconstruction ; Docker Desktop fournit déjà ce nom sur ce poste.
