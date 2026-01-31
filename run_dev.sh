#!/usr/bin/env bash

# Development startup script
# Runs Uvicorn with auto-reload enabled
echo "Starting IP2A API in development mode..."

uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload
