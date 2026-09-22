# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python backend + frontend static server
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code and assets
COPY backend/ ./backend/
COPY sample_docs/ ./sample_docs/

# Copy built frontend from Stage 1 into the location expected by Flask
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ensure persistence and uploads directories exist
RUN mkdir -p /app/backend/uploads /app/backend/chroma_db

# Default environment variables
ENV PORT=8000 \
    HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Run with Gunicorn WSGI server in production
CMD exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4 --timeout 180 backend.main:app
