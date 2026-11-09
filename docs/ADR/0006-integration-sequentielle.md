# ADR 0006 — Intégrer les ateliers dans develop, une PR à la fois

- Date : 9 novembre 2026
- Statut : Accepté par Christopher
- Remplace la séquence de revue et le calendrier du check de l'ADR 0005

## Contexte

La PR #3 de l'atelier 2 ciblait `feature/environnement-cours`, qui porte la PR #2
de l'atelier 1. Cette organisation empilée ne suivait pas le parcours vers
`develop` attendu pour l'atelier. Le check `qualite` était aussi exigé sur la
PR #2 alors que le workflow n'existe pas encore dans sa branche.

Christopher demande une intégration PR par PR : chaque étape doit repartir du
résultat réellement fusionné de la précédente. La PR #2 possède déjà une
approbation sur le commit `d1e78f1` ; ses commits sont conservés pour garder cette
revue valide. Les modifications locales du poste ne sont pas incluses dans
cette correction, effectuée dans une copie isolée.

## Décision

1. Retirer temporairement l'exigence du seul check `qualite` du ruleset commun.
   Le ruleset reste actif sur `main` et `develop` : une PR et une approbation
   sont requises, les anciennes approbations sont révoquées après un nouveau
   commit, la revue CODEOWNERS est conservée, les suppressions et force-push
   restent interdits et la liste de bypass reste vide.
2. Terminer la revue de la PR #2, puis la fusionner dans `develop`.
3. Mettre `feature/collaboration` à jour depuis le `develop` obtenu, y compris
   si la PR #2 a été intégrée par squash. Vérifier et résoudre les éventuels
   conflits, puis vérifier que le diff de la PR #3 contient seulement l'atelier 2.
4. La PR #3 cible dès maintenant `develop`, mais reste en brouillon tant que
   cette mise à jour et la vérification de son diff ne sont pas réalisées.
5. Relancer les contrôles locaux et attendre la CI verte du nouveau commit de
   la PR #3. Rétablir alors `qualite`, lié à GitHub Actions, comme check exigé
   sur `main` et `develop`. Actualiser la copie versionnée du ruleset et vérifier
   la CI du dernier commit avant de demander la revue de la PR #3.
6. Après revue, fusionner la PR #3 dans `develop`. Une PR distincte de
   `develop` vers `main` préparera ensuite la version démontrable.

## État et conséquences

La suspension du check est une étape d'amorçage : les PR vers les branches
protégées ne sont temporairement plus bloquées par la CI. Le contrôle doit être
rétabli avant la fusion de la PR #3. Ce changement ne crée aucun acteur de bypass.

Les preuves des contrôles réalisées précédemment sont conservées comme
historique. Elles ne prouvent pas que la version modifiée de la PR #3 est verte :
il faudra contrôler son nouveau commit après récupération de `develop`.

Les fusions restent des étapes humaines explicites. Une approbation n'est pas
une fusion ; tant que la PR #2 n'est pas fusionnée, la PR #3 ne peut pas encore
hériter du `develop` final de l'atelier 1.

La configuration dans `.github/rulesets/main-develop.json` reflète l'état
actuellement appliqué, sans check pendant l'amorçage. Sa modification seule
n'applique pas les réglages distants. Lors du rétablissement, relire les règles
distantes et conserver les autres réglages existants.

Sources : [GitFlow du cours](https://learn.glassworks.tech/fullstack-setup/collaboration/gitflow),
[CI du cours](https://learn.glassworks.tech/fullstack-setup/collaboration/ci).
