FROM node:24-alpine AS frontend-builder

WORKDIR /src

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend ./
RUN npm run build

FROM caddy:2-alpine

COPY caddy/Caddyfile /etc/caddy/Caddyfile
COPY caddy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY --from=frontend-builder /src/dist /srv/webui
