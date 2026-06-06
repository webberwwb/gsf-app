# Admin Frontend Dockerfile for Cloud Run
FROM node:20-alpine as build

WORKDIR /app

# Build argument for API base URL
ARG VITE_API_BASE_URL=https://backend.grainstoryfarm.ca/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Copy shared folder (needed for @shared imports)
COPY shared /shared

# Copy package files
COPY admin/package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY admin/ .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY admin/nginx.conf /etc/nginx/conf.d/default.conf

# Copy entrypoint script
COPY admin/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Cloud Run will provide PORT environment variable
EXPOSE 8080

# Use entrypoint script to substitute PORT
ENTRYPOINT ["/docker-entrypoint.sh"]

