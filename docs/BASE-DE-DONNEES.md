# PostgreSQL de développement

Configuration reprise du [cours : la base de données](https://learn.glassworks.tech/fullstack-setup/environnement/base-de-donnees).

## Démarrer et vérifier

Après ajout du service `db`, lancer `Dev Containers: Rebuild Container` depuis
la palette de commandes VS Code. Le service `dev` attend le healthcheck PostgreSQL.

Dans le terminal du conteneur :

```bash
psql postgres://app:app@db:5432/app -v ON_ERROR_STOP=1 -c "SELECT id, question, answer, created_at FROM questions ORDER BY id"
```

Résultat attendu : deux lignes, avec les réponses `Paris.` et `Deux semaines.`.
Ces lignes sont des données de démonstration du cours.

Depuis un terminal WSL, dans le dépôt, les contrôles Docker sont :

```bash
docker compose config --quiet
docker compose ps
docker compose logs db
```

## Configuration

- Image : `postgres:17`.
- Depuis `dev` : hôte `db`, port `5432`, base `app`, utilisateur et mot de passe `app`.
- Ces identifiants sont réservés au développement local.
- VS Code transfère `db:5432` : un client SQL sur l'hôte utilise `127.0.0.1`
  et le port indiqué dans l'onglet **Ports**.
- `db/data/` conserve les données et est ignoré par Git.
- `db/init/001-schema.sql` crée la table ; `002-seed.sql` insère les exemples.
  Ces fichiers sont exécutés uniquement lorsque le dossier de données est vide.
  Modifier un script ne modifie donc pas une base déjà initialisée.

## Vérifier la persistance

1. Exécuter dans le terminal du conteneur :

   ```bash
   psql postgres://app:app@db:5432/app -v ON_ERROR_STOP=1 -c "INSERT INTO questions (question, answer) VALUES ('Test de persistance', 'À retrouver après reconstruction.');"
   ```

2. Lancer `Dev Containers: Rebuild Container` sans supprimer `db/data/`.
3. Vérifier puis nettoyer la ligne de test :

   ```bash
   psql postgres://app:app@db:5432/app -v ON_ERROR_STOP=1 -c "SELECT * FROM questions WHERE question = 'Test de persistance';"
   psql postgres://app:app@db:5432/app -v ON_ERROR_STOP=1 -c "DELETE FROM questions WHERE question = 'Test de persistance';"
   ```

La ligne doit être présente après reconstruction. Les données de test ne sont
pas réinsérées à chaque démarrage.

## État de validation

Le 9 novembre 2026, la connexion depuis le dev container et les deux questions
de démonstration ont été vérifiées directement par SQL. Christopher a confirmé
que la question temporaire reste présente après `Dev Containers: Rebuild Container` :
le test de persistance est réussi. La base contient de nouveau uniquement les
deux questions de démonstration après nettoyage.
