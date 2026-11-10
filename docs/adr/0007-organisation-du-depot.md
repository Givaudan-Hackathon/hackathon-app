# ADR 0007 — Regrouper les composants du prototype dans un dépôt commun

- Date : 10 novembre 2026
- Statut : Proposée ; validation Tech et Data en attente
- Décideurs : Tech leads et Data, avec le Product pour le périmètre
- Exploration : [Spike #13](https://github.com/Givaudan-Hackathon/hackathon-app/issues/13)

## Contexte

L’équipe compte deux Tech leads, deux Data et deux Product. Christopher confirme
que les développements servent au même prototype, sans réutilisation indépendante
prévue. Le parcours vise les petits clients qui décrivent leur projet d’arômes
alimentaires et déposent un brief structuré.

Le socle existant utilise TypeScript pour Express et Vite. La brique Data utilise
Python, FastAPI et scikit-learn. Les essais du Spike montrent la coexistence des
dépendances et trois appels Node vers Data réussis. La reproduction sur deux postes
reste à consigner dans le ticket.

## Options

1. **Un dépôt commun, organisé par composant.** Une modification du contrat et
   de ses consommateurs peut être relue dans une PR. Le démarrage et les versions
   se documentent ensemble. Il faut coordonner les fichiers partagés et adapter
   la CI aux deux langages.
2. **Deux dépôts Tech et Data.** Les accès et livraisons sont indépendants. Il
   faut associer deux versions pour reproduire la démo et coordonner les PR de
   contrat. Ce coût n’est pas justifié par un autre produit consommateur identifié.

## Décision proposée

Conserver un dépôt `hackathon-app`, avec les composants regroupés ainsi :

```text
web/          Interface Vite/TypeScript
api/          API applicative Express/TypeScript
data-brique/  API FastAPI, moteur, notebooks, scripts et tests Python
db/           PostgreSQL commun aux Data et aux Tech leads
docs/adr/     Décisions communes
```

Chaque composant conserve son code, ses tests, sa configuration et ses dépendances.
Les workspaces npm couvrent `web/` et `api/` ; `data-brique/requirements.txt` et son
environnement virtuel couvrent Python. Compose, la CI et les instructions communes
restent à la racine ou dans leurs dossiers existants.

La base PostgreSQL définie par `db/` et Compose est commune à l’API applicative
et au service Data. Les deux équipes coordonnent les modifications du schéma,
les données initiales et la mise à jour des bases existantes. La connexion du
service Data à PostgreSQL reste à intégrer et à vérifier dans sa branche.

Les rôles se traduisent par les responsabilités de revue : Tech pour `web/` et
`api/`, Data pour `data-brique/`, revue commune pour `db/` et le contrat. CODEOWNERS ne
constitue pas une restriction d’accès aux dossiers. Une branche par ticket vise
`develop` via PR.

Cet ADR propose l’organisation des sources. Le contrat entre services et les
choix de langage pour le produit seront justifiés séparément à partir de l’existant.

## Conséquences

- Une source commune à récupérer et une version du prototype à identifier.
- Coût accepté : coordination sur le contrat et Compose ; contrôles Python à
  ajouter à la CI ; revue croisée des modifications communes.
- La recommandation n’atteste pas encore le démarrage Compose complet ni
  l’intégration Express vers Data. Les essais détaillés restent dans le Spike.
- À revoir si un autre produit réutilise la brique Data, si les accès doivent
  diverger ou si les livraisons deviennent indépendantes.
