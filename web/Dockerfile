FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# NEXT_PUBLIC_API_URL must be baked in at build time (Next.js inlines it).
# Render passes this as a build environment variable.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Render injects PORT at runtime (default 10000). Next.js standalone server.js
# reads process.env.PORT automatically — no hardcoded port needed.
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
