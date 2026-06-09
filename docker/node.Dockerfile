FROM node:22-slim AS base
WORKDIR /app
COPY services/edge-gateway/package.json services/edge-gateway/package-lock.json* /app/
RUN npm ci --production=false

FROM base AS builder
COPY services/edge-gateway/ /app/
RUN npm run build

FROM node:22-slim AS production
WORKDIR /app
COPY --from=builder /app/dist /app/dist
COPY --from=base /app/node_modules /app/node_modules
COPY services/edge-gateway/package.json /app/
EXPOSE 8787
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8787/health
CMD ["node", "dist/index.js"]
