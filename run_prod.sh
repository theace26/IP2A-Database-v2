#!/usr/bin/env bash

# Production startup script
# No reload, workers enabled, optimized

echo "Starting IP2A API in production mode..."

uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
