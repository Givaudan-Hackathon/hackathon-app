# API Givaudan — backend NestJS

API du prototype Givaudan AI 2026. Socle NestJS 12 (ESM, Vitest), cf. [ADR 0009](../docs/adr/0009-api-nestjs.md).

## Démarrage (depuis la racine du monorepo)

```bash
npm install                  # une fois, à la racine
npm run start:dev -w api     # watch, port 3000
npm run build -w api         # → api/dist/main.js
npm run start:prod -w api    # depuis dist/
npm run test -w api
```
