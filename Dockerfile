# Node 24, comme le dev container ; dépendances des deux workspaces.
FROM mcr.microsoft.com/devcontainers/typescript-node:24-trixie AS node-app
WORKDIR /app
COPY package.json package-lock.json ./
COPY api/package.json ./api/package.json
COPY web/package.json ./web/package.json
RUN npm ci
COPY api ./api
COPY web ./web
RUN npm run build --workspaces

FROM node-app AS api
WORKDIR /app/api
CMD ["node", "dist/main.js"]

FROM node-app AS web
WORKDIR /app/web
CMD ["node", "../node_modules/vite/bin/vite.js", "--host", "0.0.0.0", "--port", "5173"]
