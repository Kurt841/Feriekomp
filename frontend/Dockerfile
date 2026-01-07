# Frontend Dockerfile for Next.js
FROM node:20-slim AS base

# Installer avhengigheter kun når nødvendig
FROM base AS deps
WORKDIR /app

# Offentlige envs for build (kan overstyres ved build-tid)
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_ENABLE_AI_EXPLANATION

# Kopier package-filer
COPY package.json package-lock.json* ./

# Installer avhengigheter
RUN npm ci

# Bygg kildekoden på nytt kun når nødvendig
FROM base AS builder
WORKDIR /app

ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_ENABLE_AI_EXPLANATION
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
ENV NEXT_PUBLIC_ENABLE_AI_EXPLANATION=${NEXT_PUBLIC_ENABLE_AI_EXPLANATION}

# Kopier avhengigheter fra deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Sett miljøvariabler for build
ENV NEXT_TELEMETRY_DISABLED=1

# Bygg applikasjonen
RUN npm run build

# Produksjonsimage, kopier alle filer og kjør next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_ENABLE_AI_EXPLANATION
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
ENV NEXT_PUBLIC_ENABLE_AI_EXPLANATION=${NEXT_PUBLIC_ENABLE_AI_EXPLANATION}

# Opprett ikke-root bruker
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Kopier bygget applikasjon (standalone output)
WORKDIR /app
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./app/.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./app/public

WORKDIR /app/app

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Healtcheck for å sikre at applikasjonen kjører
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Kjør applikasjonen
CMD ["node", "server.js"]
