#!/bin/bash
set -e

echo "=== IP2A Database Startup ==="

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head

# Check if we should run one-time production seed
if [ "$RUN_PRODUCTION_SEED" = "true" ]; then
    echo "Checking if production seed is needed..."
    python -m src.seed.production_seed
fi

# Start the application
echo "Starting application server..."
exec gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-8000}
