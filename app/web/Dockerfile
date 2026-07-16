# syntax=docker/dockerfile:1

# ------------------------------------------------------------
# Build stage
# ------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first to maximize layer caching
COPY package*.json ./
RUN npm ci

# Copy the rest of the frontend source
COPY . .

# Build-time API base URL for Vite
# In production, set this to "/api"
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Produce the static production bundle
RUN npm run build

# ------------------------------------------------------------
# Runtime stage
# ------------------------------------------------------------
FROM nginx:1.27-alpine

# Nginx config for SPA + reverse proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built static assets
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]