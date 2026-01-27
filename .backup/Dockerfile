# ============================
# 1) BASE - Shared dependencies
# ============================
FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*


# ============================
# 2) BUILDER - Install dependencies
# ============================
FROM base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ============================
# 3) DEVELOPMENT - For local dev/devcontainer
# ============================
FROM base AS development

# Copy installed Python packages from builder
COPY --from=builder /usr/local /usr/local

# Install dev dependencies (if you have a separate requirements-dev.txt)
# COPY requirements-dev.txt .
# RUN pip install --no-cache-dir -r requirements-dev.txt

# Install useful dev tools
RUN pip install --no-cache-dir \
    ipython \
    ipdb

# Create directories
RUN mkdir -p /app/uploads

# Source code will be mounted via docker-compose volumes
# No COPY of src here - it comes from the mount

# Default command (can be overridden by docker-compose)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# ============================
# 4) PRODUCTION - For deployment
# ============================
FROM base AS production

# Copy installed Python packages from builder
COPY --from=builder /usr/local /usr/local

# Copy application code (baked into image for production)
COPY src ./src
COPY alembic.ini .

# Create uploads directory
RUN mkdir -p /app/uploads

# Run as non-root user in production
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
