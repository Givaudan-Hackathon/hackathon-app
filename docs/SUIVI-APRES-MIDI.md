# Atelier 2 — Collaboration : étapes et preuves

Source : [atelier de l'après-midi](https://learn.glassworks.tech/fullstack-setup/collaboration/atelier).
Les choix sont expliqués dans l'[ADR 0005](ADR/0005-collaboration-et-depot-public.md).
Une vérification technique ne vaut pas approbation humaine du code.

**La PR #2 est fusionnée dans `develop` au commit `92cc465`. La branche de la
PR #3 reprend ce résultat via `5ee4b68`, sans conflit. La CI de cette mise à jour
est verte et le check `qualite` est à nouveau obligatoire sur `main` et `develop`.
La revue de la PR #3 doit porter sur son dernier commit avec une CI verte.**
Voir l'[ADR 0006](ADR/0006-integration-sequentielle.md).

## Organisation et dépôt

L'organisation « Hetic Hackathon Givaudan 2026 | DP », ses équipes, les droits
ci-dessous et le type d'issue Spike étaient déjà préparés par Christopher.

| Équipe     | Droit sur hackathon-app | Membres vérifiés le 9 novembre   |
| ---------- | ----------------------- | -------------------------------- |
| tech-leads | Write                   | christopherDEPASQUAL             |
| data       | Write                   | christopherDEPASQUAL             |
| product    | Triage                  | christopherDEPASQUAL             |
| evaluation | Admin                   | glassworks, christopherDEPASQUAL |

Le dépôt est public après accord explicite de Christopher, sur GitHub Free,
sans achat. Les droits de base de l'organisation sont Read et la suppression
des dépôts par les membres est désactivée. Aucune invitation au professeur
n'était nécessaire : son accès Admin via evaluation est vérifié.

## Suivi des étapes

| Étape du cours                                | Réalisé | Preuve                                                                            |
| --------------------------------------------- | ------- | --------------------------------------------------------------------------------- |
| Organisation, équipes, rôles et choix du plan | [x]     | Audit API et accord pour le passage en public                                     |
| develop par défaut et réglages de fusion      | [x]     | API : squash/merge et suppression automatique activés ; rebase désactivé          |
| Ruleset main/develop sans check initial       | [x]     | Ruleset 26821516 actif, bypass vide                                               |
| CODEOWNERS et modèle de PR                    | [x]     | Exemples recopiés ; commit dédié et PR #3                                         |
| ESLint et Prettier sans erreur                | [x]     | lint et format:check réussis dans l'image du dev container                        |
| Husky et lint-staged                          | [x]     | Vrai commit invalide refusé ; commits valides acceptés                            |
| CI verte sur une PR                           | [x]     | Exécution 42543682683, job qualite réussi                                         |
| Check qualite exigé                           | [x]     | Rétabli après la CI verte de 5ee4b68, qui reprend develop après la PR #2          |
| Démonstration : push direct refusé            | [x]     | GH013 : Changes must be made through a pull request ; develop inchangée           |
| Démonstration : commit avec erreur refusé     | [x]     | no-unused-vars, Husky code 1 ; aucun commit de test créé                          |
| Démonstration : PR rouge bloquée              | [x]     | PR #4 hors brouillon, lint en échec, mergeable_state=blocked ; fermée sans fusion |
| Présentation à l'intervenant                  | [ ]     | À réaliser par l'équipe                                                           |

## À quoi servent les fichiers ?

- `.github/CODEOWNERS` désigne les responsables des fichiers sensibles ; les
  équipes doivent déjà avoir les droits. Le fichier ne leur donne pas accès.
- `.github/pull_request_template.md` rappelle quoi expliquer et comment tester.
- `eslint.config.mjs` détecte les erreurs probables ; `.prettierrc.json` fixe
  la présentation, dont les guillemets simples de l'exemple du cours.
- `.husky/pre-commit` lance lint-staged sur les fichiers indexés. `prepare`
  installe les hooks à chaque `npm ci`. Commiter depuis le conteneur assure Node 24.
- `.github/workflows/ci.yml` revérifie tout le projet sur GitHub.
- `.github/rulesets/main-develop.json` conserve les règles réellement appliquées.
  Modifier ce fichier seul ne change pas les réglages GitHub.

Dans le dev container sur la branche de l'atelier 2 :

```bash
npm ci
npm run lint
npm run format:check
npm run build
```

`npm run format` reformate volontairement les fichiers ; relire ensuite le diff.
Les scripts excluent `db/data`, qui appartient à PostgreSQL.

## Démonstrations et preuves distantes

Les preuves ci-dessous décrivent les tests effectués avant la correction de
l'ordre des PR. Le refus de fusion pour une CI rouge a été vérifié quand
`qualite` était exigé. Après sa suspension pour intégrer la PR #2, ce contrôle
est à nouveau actif : il a été rétabli après la CI verte de la branche mise à jour.

- [CI verte initiale](https://github.com/Givaudan-Hackathon/hackathon-app/actions/runs/42543682683) : npm ci, lint, format:check et build réussissent.
- [Ruleset actif](https://github.com/Givaudan-Hackathon/hackathon-app/rules/26821516) : main/develop, une approbation, revue CODEOWNERS et qualite exigé de GitHub Actions, sans bypass.
- Push direct : un commit vide non rattaché à une branche locale a été proposé
  à develop. GitHub l'a refusé avec GH013 ; le SHA distant est resté identique.
- Hook : un fichier temporaire avec une variable inutilisée a fait refuser un
  vrai git commit. Fichier, index et stash ont été restaurés sans nouveau commit.
- [PR #4 de test](https://github.com/Givaudan-Hackathon/hackathon-app/pull/4) : erreur ESLint volontaire, créée uniquement pour contrôler la CI serveur.
  Le hook a été contourné pour ce test négatif seulement. La CI
  [42543997672](https://github.com/Givaudan-Hackathon/hackathon-app/actions/runs/42543997672)
  échoue précisément sur lint. Après sortie du brouillon, GitHub indique
  `mergeable=true` (pas de conflit) et `mergeable_state=blocked` (règles non satisfaites).
  La PR est fermée sans fusion et sa branche temporaire est supprimée.

Un clone propre supplémentaire a exécuté la vraie commande `postCreateCommand`
deux fois dans un nouveau conteneur : le `.env` absent est créé, un `.env`
personnalisé est conservé octet pour octet, et `npm ci` installe automatiquement
le hook. Lint, format:check et build passent dans ce clone. Cela ne remplace pas
le test humain demandé à un coéquipier.

GitHub ne signale aucune erreur dans CODEOWNERS sur la branche de l'atelier 2.

## PR disponibles et ordre de revue

- [PR #1](https://github.com/Givaudan-Hackathon/hackathon-app/pull/1) : ancienne
  configuration, fermée sans fusion et remplacée par la reprise.
- [PR #2](https://github.com/Givaudan-Hackathon/hackathon-app/pull/2) : atelier 1
  complet avec Ollama, fusionné dans `develop` au commit `92cc465`.
- [PR #3](https://github.com/Givaudan-Hackathon/hackathon-app/pull/3) : atelier 2,
  trois commits du cours et documentation, mise à jour depuis `develop` après la PR #2.

1. La PR #2 a été approuvée puis fusionnée : son résultat est `develop` au
   commit `92cc465`. Sa branche n'a pas reçu de nouveau commit pendant la correction.
2. `feature/collaboration` a repris ce `develop` sans conflit au commit `5ee4b68`.
   Le diff porte sur l'atelier 2 ; les fichiers applicatifs existants sont
   uniquement reformatés par Prettier, sans changement fonctionnel.
3. La [CI de cette mise à jour](https://github.com/Givaudan-Hackathon/hackathon-app/actions/runs/42644201232)
   est verte. `qualite` est rétabli dans le ruleset. Attendre aussi la CI du
   dernier commit de documentation, puis obtenir une revue avant de fusionner
   la PR #3 vers `develop`.
4. Après la fusion de la PR #3, préparer une PR de `develop` vers `main` pour la
   version démontrable, avec ses contrôles et sa revue.

Chaque PR reprend ainsi le résultat réellement intégré de la précédente.
La copie de travail initiale reste conservée avec ses modifications locales.

La compréhension du code, la reconstruction dans VS Code et le test d'un clone par un
coéquipier restent des validations humaines de l'atelier 1. La capture de
Christopher confirme déjà la question, sa réponse et l'enregistrement en base.
Aucune PR fonctionnelle n'est fusionnée automatiquement pendant cette reprise.
