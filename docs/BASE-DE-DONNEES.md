# PostgreSQL commun aux Data et aux Tech leads

Configuration reprise du [cours : la base de données](https://learn.glassworks.tech/fullstack-setup/environnement/base-de-donnees).

## Responsabilité commune

La base définie par `db/` et le service `db` de `compose.yaml` est destinée à
l’API applicative et au service Data du même prototype. Les Data et les Tech
leads maintiennent ensemble le schéma SQL et les données initiales. Les deux
équipes sont identifiées dans CODEOWNERS pour `db/` et ce guide.

Une évolution du schéma se coordonne entre les deux équipes et précise comment
mettre à jour une base déjà initialisée. Les scripts `db/init/` ne constituent
pas un mécanisme de migration pour une base existante.

Chaque environnement de développement utilise son instance locale PostgreSQL
lancée par Compose. L’API applicative s’y connecte déjà ; la connexion du service
Data reste à intégrer et à vérifier dans sa branche. Les fichiers d’échantillons
de `data-brique/data/` restent distincts du stockage PostgreSQL `db/data/`.

## Démarrer et vérifier

Ouvrir le projet avec `Dev Containers: Reopen in Container` depuis la palette
de commandes VS Code. Après une modification de Compose, utiliser
`Dev Containers: Rebuild Container`. Le service `dev` attend le healthcheck PostgreSQL.

Dans le terminal du conteneur :

```bash
psql postgres://app:app@db:5432/app -v ON_ERROR_STOP=1 -c "SELECT id, question, answer, created_at FROM questions ORDER BY id"
```

Sur une base nouvellement initialisée, les exemples incluent les réponses
`Paris.` et `Deux semaines.`. Les échanges créés ensuite apparaissent également
dans cette liste ; les exemples sont des données de démonstration du cours.

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
