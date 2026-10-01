FROM node:20-alpine

WORKDIR /app

# Copy manifests first for better layer caching.
COPY package.json package-lock.json* ./

RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
