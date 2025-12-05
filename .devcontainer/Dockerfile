# Devcontainer build for FastAPI + Alembic + Postgres
FROM mcr.microsoft.com/devcontainers/python:3.12

# Install system-level deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        git \
        postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy dependencies first for caching
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Preinstall Alembic + Uvicorn globally for dev
RUN pip install alembic uvicorn[standard]

# Default command – VS Code overrides with "overrideCommand": false
CMD [ "sleep", "infinity" ]
