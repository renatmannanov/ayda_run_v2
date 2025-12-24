# Build stage for frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/webapp
COPY webapp/package*.json ./
RUN npm install
COPY webapp/ ./
RUN npm run build

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/webapp/dist ./webapp/dist

# Expose port
EXPOSE 8000

# Start command
CMD alembic upgrade head && uvicorn api_server:app --host 0.0.0.0 --port ${PORT:-8000}
