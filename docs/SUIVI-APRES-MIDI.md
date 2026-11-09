# Atelier 2 — Collaboration : étapes et preuves

Source : [atelier de l'après-midi](https://learn.glassworks.tech/fullstack-setup/collaboration/atelier).
Les choix sont expliqués dans l'[ADR 0005](ADR/0005-collaboration-et-depot-public.md).
Une vérification technique ne vaut pas approbation humaine du code.

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
| Check qualite exigé                           | [x]     | Règle ajoutée après succès, liée à GitHub Actions                                 |
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

- [CI verte initiale](https://github.com/Givaudan-Hackathon/hackathon-app/actions/runs/42543682683) : npm ci, lint, format:check et build réussissent.
- [Ruleset actif](https://github.com/Givaudan-Hackathon/hackathon-app/rules/26821516) : main/develop, une approbation, CODEOWNERS, qualite, sans bypass.
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
  complet avec Ollama, prête à relire, cible develop.
- [PR #3](https://github.com/Givaudan-Hackathon/hackathon-app/pull/3) : atelier 2,
  trois commits du cours, cible temporaire feature/environnement-cours.

Relire puis fusionner d'abord la PR #3. La PR #2 récupère alors les scripts et le
workflow : attendre qualite vert et l'approbation d'un autre membre avant de la
fusionner dans develop. La copie de travail initiale reste sur la branche de
l'atelier 1 ; les changements de l'atelier 2 sont dans la PR et la copie isolée.

La compréhension du code, la reconstruction dans VS Code et le test d'un clone par un
coéquipier restent des validations humaines de l'atelier 1. La capture de
Christopher confirme déjà la question, sa réponse et l'enregistrement en base.
Aucune PR fonctionnelle n'est fusionnée automatiquement pendant cette reprise.
