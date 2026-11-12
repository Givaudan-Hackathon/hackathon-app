# ADR 0008 — Construire l’interface produit avec React et Vite

- Date : 10 novembre 2026
- Statut : Choix React/Tailwind confirmé par Christopher le 12 novembre ; implémentation proposée à la revue dans le ticket #20
- Décideurs : les deux Tech leads, avec le Product pour le parcours

## Contexte

Le front actuel est une page Vite/TypeScript de test dans `web/src/main.ts`.
Le produit vise la qualification progressive d’un brief d’arômes alimentaires :
questions, réponses, informations manquantes, relecture et dépôt. Christopher
confirme que les deux Tech leads maîtrisent React et NestJS. Le jalon m1 est fixé
au 10 novembre à 18 h ; il exige des livrables cohérents avec le code au tag.

## Options

1. **Conserver le DOM et TypeScript actuels.** Continuité immédiate et peu de
   dépendances. L’état d’un dialogue et les écrans suivants doivent être organisés
   manuellement ; le code actuel ne comporte qu’un formulaire de démonstration.
2. **React avec TypeScript et Vite.** Composants et état explicites pour le dialogue,
   le récapitulatif et les résultats ; connaissances déjà présentes dans l’équipe.
   Il faut migrer la page, ajouter JSX et le contrôle TypeScript, adapter la
   configuration et vérifier le formulaire et les erreurs.

## Décision proposée

Adopter React pour le front produit dans `web/`, en conservant Vite, TypeScript,
le port 5173 et le proxy `/api`. La migration fera l’objet d’un changement de code
revu et testé. Jusqu’à cette migration, le README et AGENTS.md décrivent le front
Vite/TypeScript réellement présent. La réalisation du ticket #20 installe ensuite
React, Tailwind et un contrôle TypeScript dédié ; Nest et Data restent séparés.

Ce choix répond au parcours interactif du prototype. Aucun besoin de rendu côté
serveur n’a été validé ; ajouter un autre framework de rendu n’est pas proposé ici.

## Conséquences

- Organisation du travail par composants et état du brief explicite.
- Coût accepté : migration du formulaire, dépendances React, vérification des
  chargements et erreurs, et maintien du build et de la CI.
- React ne constitue pas une preuve que le chatbot qualifie correctement un brief.
- À revoir si le parcours validé reste une page statique, si l’équipe change ou
  si des exigences de rendu côté serveur apparaissent.

Source : [React avec un outil de build, dont Vite](https://react.dev/learn/build-a-react-app-from-scratch).

## Précision pour le prototype du 12 novembre

Christopher confirme le passage à la réalisation après le cadrage #19/PR #22.
React/TypeScript et Tailwind sont installés dans le workspace web ; l’API Express
et ses routes sont conservées. Le parcours client consomme un service simulé au
contrat V2 de la PR Data #18, via une interface indépendante des composants.
Les vérifications de réalisation et les limites restent dans le ticket #20.

Pour les styles, CSS par composant et Tailwind ont été examinés dans le cadrage.
Tailwind est retenu selon la demande de Christopher pour les tokens, utilitaires
et composants partagés. Le coût est une dépendance et une convention de classes
à maintenir. Les effets du MVP utilisent CSS ; aucune dépendance de moteur 3D,
de routage ou de store global n’est ajoutée. Zod valide les objets reçus à
l’exécution et les coordonnées, TypeScript vérifiant leurs usages dans le code.
