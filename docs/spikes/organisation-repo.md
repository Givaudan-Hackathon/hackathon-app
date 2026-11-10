# Spike 13 — Un dépôt commun ou plusieurs dépôts ?

[Ticket #13](https://github.com/Givaudan-Hackathon/hackathon-app/issues/13).
Date : 10 novembre 2026. Durée maximale : une demi-journée.

**Conclusion technique : nous recommandons un dépôt commun, avec des services et dépendances séparés. La décision est à relire ensemble. Les essais par une personne Tech et une personne Data restent à renseigner avant de déclarer tous les critères du ticket satisfaits.**

## Contexte vérifié

L’équipe comprend deux Tech leads, deux Data et deux Product. Christopher confirme
que le développement sert uniquement au prototype commun. Le parcours retenu vise
les petits clients qui décrivent un projet d’arômes alimentaires avec leurs mots
et déposent un brief structuré. Aucun autre projet consommateur ni besoin d’accès
séparé n’a été exprimé.

Le socle Tech contient Express/TypeScript, Vite et PostgreSQL. La branche Data
contient une API FastAPI, un moteur TF-IDF, des données d’exemple, des scripts,
des notebooks et des tests. Le choix du dépôt concerne la collaboration et la
livraison ; les services conservent chacun leur langage et leurs dépendances.

Sources techniques examinées :

- `develop` : `a49dd80a0f9e3c373d06df1e64d7d334418c43e4`.
- `feature/data-brique` : `148f6e457c8c82270f9c901c4ef3ee2819cc47ed`.
- [Contrat Data](https://github.com/Givaudan-Hackathon/hackathon-app/blob/148f6e457c8c82270f9c901c4ef3ee2819cc47ed/data-brique/docs/contrat_api.md).
- `compose.yaml`, `.devcontainer/`, `.github/workflows/ci.yml`,
  `.github/CODEOWNERS` et les `package.json` du socle Tech.

## Comparaison pour notre équipe

| Critère                                            | Dépôt commun                                                          | Dépôts Tech et Data séparés                                               |
| -------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Changement du contrat Data et de ses consommateurs | Une PR peut réunir les changements et les revues                      | PR coordonnées et versions compatibles à identifier dans deux historiques |
| Installation et démonstration                      | Une arborescence à récupérer ; les services restent distincts         | Deux sources à récupérer et leurs versions à associer                     |
| Dépendances Python et Node                         | `data-brique/.venv` et `requirements.txt` séparés des workspaces npm  | Isolation naturelle par dépôt, avec deux préparations à maintenir         |
| Qualité                                            | Un point de contrôle commun, avec commandes adaptées à chaque langage | Deux CI, plus une vérification d’intégration entre les versions           |
| Responsabilités                                    | Dossiers et revues définis par CODEOWNERS                             | Responsables et permissions gérés par dépôt                               |
| Livraison indépendante pour d’autres produits      | Possible, sans nécessité actuelle                                     | Intérêt plus fort si la brique doit être réutilisée indépendamment        |
| Coût accepté                                       | Coordination sur les fichiers partagés et CI à étendre                | Coordination des versions, contrats, accès et démarrage de deux dépôts    |

CODEOWNERS demande des revues ; il ne limite pas les droits d’accès à certains
dossiers. Les droits actuels de l’organisation restent inchangés par ce Spike.

## Essais réalisés

Les deux sources ont été réunies dans une copie jetable sous `/tmp`. Aucun code
Data n’a été fusionné dans `develop` et aucune modification locale préexistante
n’a été incluse. Environnement des essais : Linux/WSL, Node `24.15.0`, npm
`11.12.1`, Python `3.13.9`.

| Vérification                                                             | Résultat observé                                                                    |
| ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| `npm run lint` sur la copie réunie                                       | Réussi                                                                              |
| `npm run format:check` sur la copie réunie                               | Réussi                                                                              |
| `npm run build` : Express et Vite                                        | Réussi                                                                              |
| Installation de tout `data-brique/requirements.txt` dans un venv jetable | Réussie                                                                             |
| `python -m pip check`                                                    | Aucun conflit de dépendances déclaré                                                |
| `GET /sante` depuis Node vers FastAPI                                    | HTTP 200, 32 ms                                                                     |
| Trois `POST /recommander`, `k = 2`                                       | HTTP 200, 9 ms, 4 ms et 5 ms                                                        |
| Contrôle des trois réponses                                              | Deux produits, champs et types attendus, score entre 0 et 1 et attribution présente |
| Démarrage reproduit par un membre Tech                                   | À renseigner                                                                        |
| Démarrage reproduit par un membre Data                                   | À renseigner                                                                        |

Les dépendances Node déjà installées depuis le lockfile ont été réutilisées pour
ces contrôles ; il ne s’agit pas d’un `npm ci` dans un nouveau clone. Les durées
HTTP sont des observations locales et non une garantie de performance.

Les trois tests existants de l’API Data ont également réussi en 1,84 seconde
avec `python -m pytest -q` exécuté depuis `data-brique/`.

L’API Data a été démarrée sur une adresse locale et arrêtée après les essais.
Le script de preuve est `scripts/verifier-api-data.mjs`. Il effectue un contrôle
de santé et trois appels avec des briefs d’arômes alimentaires, sans dépendance
npm supplémentaire.

## Ce que ces preuves permettent de conclure

Les dépendances et les sources Python et TypeScript peuvent cohabiter dans cette
arborescence. Un client Node peut appeler le service Data sans déplacer son moteur
ni ses données dans l’API Express. Aucun blocage technique imposant deux dépôts
n’a été trouvé dans ces essais.

Ces preuves ne valident pas encore le lancement de toute l’application avec
`docker compose up`, la reproduction sur deux postes, les notebooks, la
pertinence métier des recommandations ni l’intégration Express → Data. Cette
intégration complète reste dans le [Spike #12](https://github.com/Givaudan-Hackathon/hackathon-app/issues/12).
La vérification de l’image du dev container n’a pas abouti : le contrôle
automatique des permissions a expiré. Sa disponibilité Python reste à contrôler.

## Organisation recommandée

Conserver `web/`, `api/`, `data-brique/`, `db/`, les ADR et le Compose commun dans
`hackathon-app`. Les dépendances restent dans leurs manifests respectifs :
workspaces npm côté Tech, environnement virtuel et `requirements.txt` côté Data.

Pour travailler à quatre sur le code :

1. Une branche `feature/nom-du-ticket` depuis `develop` par travail délimité.
2. Une PR vers `develop`, avec `Closes #N` lorsque ses critères sont satisfaits.
3. Data relit les changements de `data-brique/`, Tech ceux de `api/` et `web/`.
   Un changement du contrat partagé est relu par Tech et Data.
4. Le Product vérifie les critères métier ; le tableau GitHub Projects reste commun.
5. La branche Data actuelle entre par une PR relue. Elle ne devient pas une
   branche d’intégration permanente parallèle à `develop`.

Adaptations à planifier après le choix :

- Étendre CODEOWNERS aux dossiers Data, Tech et au contrat partagé.
- Ajouter un contrôle Python dans la CI, exécuté depuis `data-brique/`, en
  complément du job `qualite` existant.
- Versionner le contrat OpenAPI réel et documenter les changements compatibles.
- Décrire le démarrage de chaque service ; préparer ensuite le démarrage commun
  par Compose pour la tranche verticale. Un dépôt commun n’exige pas de lancer
  Node et Python dans le même processus.

## Reproduire les contrôles côté Data et Tech

Procédure pour Linux/WSL avec Node 24, Python 3.13 et Git, dans un **nouveau clone
jetable**. La branche du Spike contient le script ; la source Data est récupérée
sur le commit précis examiné, sans fusion de sa branche.

```bash
git clone --branch feature/spike-organisation-repo https://github.com/Givaudan-Hackathon/hackathon-app.git hackathon-essai-organisation
cd hackathon-essai-organisation
git fetch origin 148f6e457c8c82270f9c901c4ef3ee2819cc47ed
git restore --source=148f6e457c8c82270f9c901c4ef3ee2819cc47ed --worktree -- data-brique
npm ci
npm run lint
npm run format:check
npm run build
python3 -m venv data-brique/.venv
data-brique/.venv/bin/python -m pip install -r data-brique/requirements.txt
data-brique/.venv/bin/python -m pip check
cd data-brique
.venv/bin/python -m pytest -q
.venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Dans un second terminal, depuis la racine du clone :

```bash
node scripts/verifier-api-data.mjs http://127.0.0.1:8000
```

Arrêter Uvicorn avec Ctrl+C. Le guide de démarrage Tech existant dans `README.md`
reste à reproduire pour valider aussi Express, Vite et PostgreSQL.

Chaque personne renseigne dans le ticket : rôle, OS, commit, commandes, résultat
et blocages éventuels. Les validations automatiques ci-dessus ne doivent pas être
présentées comme deux validations humaines.

## Suite et condition de révision

Faire relire ce compte rendu par Tech et Data. Après accord, consigner le choix
dans un nouvel ADR, avec les deux options et leurs coûts. Réexaminer deux dépôts
si un autre produit doit consommer la brique Data, si les droits doivent diverger
ou si les livraisons deviennent réellement indépendantes.

Le Spike reste ouvert tant que la reproduction et la décision commune prévues
par son seuil ne sont pas renseignées. Les éléments de `m1` feront l’objet de la
suite du travail après ce point de validation.
