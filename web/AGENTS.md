# Consignes de l’interface web

Portée : `web/`. Lire aussi les règles communes dans `../AGENTS.md` et les
décisions dans `../docs/adr/`. Ce fichier est maintenu par les Tech leads.

## Lancer et vérifier

- Depuis la racine : `npm run dev -w web` pour Vite sur 5173, puis `npm run build -w web` pour le bundle.
- La CI reste définie dans `../.github/workflows/ci.yml` ; lancer aussi les contrôles racine avant la PR.
- Le build Vite actuel ne lance pas de vérification TypeScript dédiée ; ne pas présenter un script de typecheck comme disponible tant qu’il n’existe pas dans `package.json`.

## Code actuel et évolution

- `index.html` charge `src/main.ts` ; cette page teste l’API et les échanges IA. Elle ne constitue pas encore le parcours de brief client.
- `vite.config.ts` transmet `/api` à l’API applicative sur 3000 ; les appels du socle suivent `../openapi.yaml`.
- `src/main.ts` insère actuellement les réponses avec `textContent` ; conserver un affichage textuel des réponses reçues.
- `../docs/adr/0008-interface-react.md` propose React avec Vite. Lors de sa migration validée, conserver les ports et le proxy, puis actualiser ce fichier et les commandes réellement ajoutées.
- Pour le parcours produit, prévoir les états chargement, erreur et récapitulatif du brief dans les composants concernés ; leur présence doit être vérifiée dans le code et avec le Product.

## Exploration du parcours — ticket #33

Pour `explorations/atelier/`, appliquer [Interface Design](https://github.com/Dammyjay93/interface-design/blob/2f9be3206855bcb2d1d0af262c8bae25cba6658d/.claude/skills/interface-design/SKILL.md),
en complément des skills frontend-design, vercel-react-best-practices et
web-design-guidelines requis pour le front. Lire la source liée si le skill
n’est pas installé. Les maquettes servent à choisir une direction ; elles ne
remplacent pas le parcours React/Tailwind. Lire leur README avant modification.
