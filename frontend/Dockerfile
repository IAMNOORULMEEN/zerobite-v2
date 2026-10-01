FROM node:20-alpine

WORKDIR /app

# Copy manifests first for better layer caching.
COPY package.json package-lock.json* ./

RUN --mount=type=cache,target=/root/.npm NODE_OPTIONS=--dns-result-order=ipv4first npm install --no-audit --no-fund --fetch-retries=5 --fetch-retry-mintimeout=2000 --fetch-timeout=60000 --loglevel=http

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
