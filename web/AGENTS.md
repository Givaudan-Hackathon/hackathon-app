# Consignes de l’interface web

Portée : `web/`. Lire aussi les règles communes dans `../AGENTS.md` et les
décisions dans `../docs/adr/`. Ce fichier est maintenu par les Tech leads.

## Skills obligatoires

Pour tout travail sur l’interface, lire et appliquer les `SKILL.md` suivants
(version installée, sinon source liée), ainsi que leurs ressources pertinentes :

- [frontend-design](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md) : conception et direction visuelle.
- [vercel-react-best-practices](https://github.com/vercel-labs/agent-skills/blob/main/skills/react-best-practices/SKILL.md) : développement React ; appliquer les règles pertinentes pour Vite.
- [interface-design](https://github.com/Dammyjay93/interface-design/blob/2f9be3206855bcb2d1d0af262c8bae25cba6658d/.claude/skills/interface-design/SKILL.md) : conserver la direction Atelier validée, avec fiche sensorielle et brief.
- [web-design-guidelines](https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines/SKILL.md) : revue UX, accessibilité et interactions avant livraison.

Pour exploiter Figma, lire aussi `figma:figma-design-to-code` avant
`get_design_context`. Les maquettes cadrent le parcours ; les améliorations
visuelles et UX sont encouragées. Le prototype vise uniquement le petit client ;
le dépôt d’une demande reste distinct de son acceptation commerciale.

## Architecture du prototype

Lire [le cadrage web](../docs/ARCHITECTURE-WEB.md) avant le ticket #20 : état du
parcours, adaptateurs, contrat Data et images de démonstration. Le ticket #19
porte le cadrage ; le ticket #20 installe React/Tailwind ; #32 et #33 ajoutent le HTTP et l’atelier dans la même PR #28 à la demande de Christopher.
Le périmètre vise le petit client ; brouillon Data,
dépôt applicatif et acceptation commerciale restent des états distincts.

## Lancer et vérifier

- Depuis la racine : `npm run dev -w web` pour Vite sur 5173, puis `npm run build -w web` pour le bundle.
- La CI reste définie dans `../.github/workflows/ci.yml` ; lancer aussi les contrôles racine avant la PR.
- `npm run typecheck -w web` vérifie TypeScript ; le build Vite reste distinct. `npm test -w web` lance les tests métier avec Node 24 ; `npm run test:e2e -w web` vérifie le parcours avec Playwright, après installation de Chromium.
- `GIVAUDAN_TEST_PORT=5184 npm run test:e2e` utilise un serveur de test distinct, sans réutiliser le prototype déjà ouvert sur 5173.

## Code actuel et évolution

- `index.html` charge `src/main.tsx` ; `src/app/App.tsx` compose le parcours React/Tailwind. Les visuels et fontes sont locaux.
- `diagnostic.html` conserve le test API chargé par `src/main.ts`. Ne pas confondre cet écran technique avec le prototype client.
- `vite.config.ts` conserve le port 5173 et le proxy `/api` vers Nest (`API_PROXY_TARGET`, 3000 par défaut). Les routes réelles du socle restent décrites dans `../openapi.yaml`.
- Les composants utilisent les interfaces de `src/services/`. L’adaptateur HTTP appelle uniquement Nest (`/api/conversation`) par défaut ; `VITE_CONVERSATION_MODE=demo` est un choix explicite. Aucun repli fictif automatique sur erreur HTTP.
- Le contrat pur Zod `../api/src/contracts/conversation.ts` est partagé par Nest et React, via `src/services/conversation-service.ts`. Il préserve les champs Data additionnels ; afficher les réponses en texte, sans HTML injecté. Une correction invalide les résultats dépendants.
- Afficher les questions et choix fournis par Python (`guidage: true`), les profils, volumes, créations sur mesure et labels manquants. Un brouillon `echantillons` conservé ne déclenche le paiement que sur action explicite.
- Les images Data HTTP(S) sont acceptées ; à défaut, cinq ingrédients ont un visuel local et les autres un remplacement neutre.
- Conserver les mentions de démonstration, l’attribution reçue et la distinction brouillon/dépôt/commande ; le MVP ne transmet rien à un commercial et ne persiste pas les coordonnées.
