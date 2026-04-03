# Backend Dockerfile for Cloud Run
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Note: APP_VERSION should be set as environment variable during deployment
# This ensures API version matches frontend version (from sw.js)

# Cloud Run will provide PORT environment variable
EXPOSE 8080

# Use gunicorn with gevent-websocket worker for SocketIO support
CMD exec gunicorn --bind 0.0.0.0:${PORT:-8080} --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 1 --timeout 0 wsgi:app

