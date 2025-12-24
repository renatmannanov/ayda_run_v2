#!/bin/bash
set -e

echo "=== Building frontend ==="
cd webapp
npm install
npm run build
cd ..

echo "=== Running database migrations ==="
alembic upgrade head

echo "=== Starting API server ==="
uvicorn api_server:app --host 0.0.0.0 --port ${PORT:-8000}
