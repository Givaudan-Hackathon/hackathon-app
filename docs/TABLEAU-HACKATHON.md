# Tableau GitHub Projects du hackathon

Référence : [Le tableau GitHub Projects](https://learn.glassworks.tech/fullstack-setup/hackathon/tableau).

Ouvrir le [tableau Hackathon](https://github.com/orgs/Givaudan-Hackathon/projects/1).

Le projet d’organisation s’appelle **Hackathon**. Il suit les issues du dépôt
`Givaudan-Hackathon/hackathon-app`. Une carte représente un ticket ; les pull
requests restent liées aux tickets et ne créent pas de seconde carte.

## Colonnes et estimation

| Status      | Sens                          |
| ----------- | ----------------------------- |
| Backlog     | À trier ou encore bloqué      |
| Ready       | Prêt à commencer              |
| In progress | Quelqu’un travaille au ticket |
| In review   | Pull request ouverte          |
| Done        | Fusionné et critères vérifiés |

Le champ **Size** est un choix unique : **S : ½ jour**, **M : 1 jour**,
**L : 2 jours**. Au-delà, découper le ticket. Un spike dure au plus une journée.
L’ordre des cartes dans Ready donne la priorité ; aucun champ Priorité n’est
nécessaire. Chaque personne garde au plus deux tickets In progress.

## Accès

Le tableau reste privé, avec un rôle de base **No access**. Ses droits sont
distincts de ceux du dépôt :

| Équipe     | Rôle du tableau |
| ---------- | --------------- |
| tech-leads | Admin           |
| data       | Write           |
| product    | Write           |
| evaluation | Read            |

Le dépôt lié et le dépôt par défaut sont `hackathon-app`. Le type d’issue
**Spike** doit exister dans l’organisation. La fusion squash utilise le titre
de la pull request comme message de commit.

## Quand déplacer une carte

Ces listes reprennent les critères du cours ; l’équipe doit en convenir lors
du cadrage suivi dans le [ticket #7](https://github.com/Givaudan-Hackathon/hackathon-app/issues/7).

**Ready :**

- Le titre dit ce qui change.
- Les critères d’acceptation sont vérifiables.
- Size vaut S, M ou L.
- Rien ne bloque le travail.

**Done :**

- La pull request est fusionnée dans `develop`.
- La CI est verte et le code a été relu.
- Le Product a vérifié les critères avant fusion.
- Le résultat est démontrable.

Le Product écrit les stories, ordonne Ready et vérifie le besoin. Le tech-lead
découpe et estime les tâches techniques. La Data/IA écrit les spikes et vérifie
les métriques. Un notebook suit le même cycle qu’un autre fichier de code.

## Du ticket à la démonstration

1. Créer une issue avec le formulaire Story, Tâche, Spike ou Bug. La carte
   arrive en Backlog lorsque les workflows du projet sont actifs.
2. Le Product relit les critères, l’équipe estime Size, puis le Product place
   le ticket dans Ready selon sa priorité.
3. La personne qui prend le ticket se l’assigne, crée une branche
   `feature/nom-court` depuis `develop` et déplace la carte en In progress.
4. Elle ouvre une PR vers `develop`, avec le titre du ticket et `Closes #N`
   dans la description. La carte passe en In review lorsque le workflow de
   liaison est disponible et activé ; sinon l’auteur la déplace manuellement.
5. Le Product vérifie les critères, un relecteur approuve et la CI passe.
   La fusion ferme le ticket ; le workflow Item closed place la carte en Done.

Exemple pour le premier ticket : branche `feature/modeles-tickets`, PR
« Ajouter les modèles de tickets », description contenant `Closes #5`.

Les modèles de `.github/ISSUE_TEMPLATE/` ne sont proposés par GitHub qu’après
fusion dans la branche par défaut, `develop`. Les tickets vierges sont désactivés.

Les noms de branches utilisent des minuscules, des tirets et aucun accent.
Une correction urgente part de `main`, sur une branche `hotfix/nom-court`.
Les mots-clés de fermeture ne fonctionnant que vers la branche par défaut,
un ticket de hotfix fusionné dans `main` est fermé manuellement après validation.

## Workflows natifs du projet

Dans **Projects → Hackathon → … → Workflows**, les réglages attendus sont :

| Workflow                     | Réglage                                       |
| ---------------------------- | --------------------------------------------- |
| Auto-add to project          | Dépôt `hackathon-app`, filtre `is:issue`      |
| Item added to project        | Status : Backlog                              |
| Pull request linked to issue | Status : In review, si ce workflow est offert |
| Item closed                  | Status : Done                                 |

Un seul Auto-add est disponible sur le plan gratuit. Il récupère les issues
créées ou modifiées après son activation ; les tickets antérieurs sont ajoutés
explicitement. Ne pas inclure les pull requests dans son filtre.

Une carte déplacée manuellement vers Done ou In review mérite un contrôle :
liaison `Closes #N` absente, workflow inactif ou fonctionnalité indisponible.
Ces workflows sont ceux de Projects, pas des GitHub Actions.

## Vues et rythme

- **Board** : toutes les cartes, groupées par Status dans l’ordre du tableau.
- **Table** : renseigner les champs, notamment Size et Assignees.
- **Daily** : filtre `-status:Backlog -status:Done`.
- **Mon travail** : filtre `assignee:@me -status:Done`.

Chaque matin, le tech-lead anime un daily de dix minutes, en lisant de droite
à gauche. Un ticket In progress depuis deux jours sans PR doit être débloqué
ou découpé ; une PR en revue depuis un jour appelle une relecture. Une CI rouge
est traitée par l’auteur. Si tout est en cours, finir avant de commencer autre chose.

Avant une démo, préparer une PR de `develop` vers `main`, avec CI et revue.
La démonstration au Product se fait sur `main`, à partir des critères d’acceptation.
Après la démo, prévoir quinze minutes de rétro : garder, arrêter, essayer.
