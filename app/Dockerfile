# App Frontend Dockerfile for Cloud Run
FROM node:20-alpine as build

WORKDIR /app

# Build arguments for Vite environment variables
ARG VITE_API_BASE_URL=https://backend.grainstoryfarm.ca/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

ARG VITE_APP_PUBLIC_URL=https://app.grainstoryfarm.ca
ENV VITE_APP_PUBLIC_URL=$VITE_APP_PUBLIC_URL

ARG VITE_GOOGLE_MAPS_API_KEY
ENV VITE_GOOGLE_MAPS_API_KEY=$VITE_GOOGLE_MAPS_API_KEY

# Copy shared folder (needed for @shared imports)
COPY shared /shared

# Copy package files
COPY app/package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY app/ .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY app/nginx.conf /etc/nginx/conf.d/default.conf

# Copy entrypoint script
COPY app/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Cloud Run will provide PORT environment variable
EXPOSE 8080

# Use entrypoint script to substitute PORT
ENTRYPOINT ["/docker-entrypoint.sh"]

