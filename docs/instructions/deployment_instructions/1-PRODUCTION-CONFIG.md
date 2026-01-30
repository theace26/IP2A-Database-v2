# 1. Production Configuration

**Duration:** 1-2 hours
**Goal:** Prepare codebase for cloud deployment

---

## Step 0: Set Up Branch Strategy (Do This First!)

Before any production changes, separate your branches:

```bash
cd ~/Projects/IP2A-Database-v2

# Ensure main is current
git checkout main
git pull origin main

# Create develop branch for ongoing work
git checkout -b develop
git push -u origin develop

# Stay on develop for the production config work
# We'll merge to main at the end when everything is ready
```

**Branch purposes:**
- `main` → Stable demo (auto-deploys to Railway/Render)
- `develop` → Your working branch (Windows dev environment)

All the following steps should be done on `develop`. We'll merge to `main` at the end.

---

## Step 1: Create Production Dockerfile

Create `Dockerfile` in project root:

```dockerfile
# IP2A-Database-v2 Production Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    # WeasyPrint dependencies for PDF generation
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Create app user (non-root for security)
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy application code
COPY --chown=app:app . .

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "src.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

---

## Step 2: Create Health Check Endpoint

Add to `src/main.py` (after other routes):

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy", "version": "0.7.9"}
```

> **Note:** Update version string when tagging releases.

---

## Step 3: Create Production Settings

Create `src/config/settings.py`:

```python
"""Application settings with environment-based configuration."""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/ip2a"

    # Security
    secret_key: str = "change-me-in-production-min-32-characters"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # CORS
    allowed_hosts: str = "*"

    # S3 Storage
    s3_endpoint_url: Optional[str] = None
    s3_access_key_id: Optional[str] = None
    s3_secret_access_key: Optional[str] = None
    s3_bucket_name: str = "ip2a-documents"
    s3_region: str = "us-east-1"

    # Feature flags
    enable_docs: bool = True  # Swagger UI

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origins(self) -> list[str]:
        if self.allowed_hosts == "*":
            return ["*"]
        return [h.strip() for h in self.allowed_hosts.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
```

---

## Step 4: Update Database Configuration

Update `src/db/database.py` to use settings:

```python
"""Database configuration with production support."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Import settings
try:
    from src.config.settings import settings
    DATABASE_URL = settings.database_url
except ImportError:
    # Fallback for tests/development
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/ip2a"
    )

# Handle Railway's postgres:// vs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## Step 5: Update Main App for Production

Update `src/main.py` imports and configuration:

```python
"""Main FastAPI application with production configuration."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from jinja2 import Environment, FileSystemLoader

# Try to import settings, fallback for dev
try:
    from src.config.settings import settings
    ENVIRONMENT = settings.environment
    DEBUG = settings.debug
    CORS_ORIGINS = settings.cors_origins
except ImportError:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = ENVIRONMENT == "development"
    CORS_ORIGINS = ["*"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting IP2A-v2 in {ENVIRONMENT} mode")

    # Run migrations in production
    if ENVIRONMENT == "production":
        from alembic.config import Config
        from alembic import command
        try:
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            print("Database migrations applied")
        except Exception as e:
            print(f"Migration warning: {e}")

    yield

    # Shutdown
    print("Shutting down IP2A-v2")


# Create app with conditional docs
app = FastAPI(
    title="IP2A Database API",
    description="Union Operations & Training Management System",
    version="0.7.9",
    lifespan=lifespan,
    docs_url="/docs" if DEBUG or ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if DEBUG or ENVIRONMENT != "production" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... rest of your existing main.py code ...
```

---

## Step 6: Create .env.example

Create `.env.example` for reference:

```bash
# IP2A-Database-v2 Environment Variables
# Copy to .env and fill in values

# Environment (development, staging, production)
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database (PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ip2a

# Security (generate with: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=change-me-in-production-use-secrets-token-hex-32

# S3-Compatible Storage (MinIO for dev, Backblaze/AWS for prod)
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET_NAME=ip2a-documents
S3_REGION=us-east-1

# CORS (comma-separated list or * for all)
ALLOWED_HOSTS=*
```

---

## Step 7: Create railway.json (Railway Config)

Create `railway.json` in project root:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

---

## Step 8: Create render.yaml (Render Config)

Create `render.yaml` in project root:

```yaml
# Render Blueprint
# https://render.com/docs/blueprint-spec

services:
  - type: web
    name: ip2a-api
    env: docker
    dockerfilePath: ./Dockerfile
    healthCheckPath: /health
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: ip2a-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: S3_ENDPOINT_URL
        sync: false
      - key: S3_ACCESS_KEY_ID
        sync: false
      - key: S3_SECRET_ACCESS_KEY
        sync: false
      - key: S3_BUCKET_NAME
        value: ip2a-documents

databases:
  - name: ip2a-db
    databaseName: ip2a
    plan: starter
```

---

## Step 9: Update .gitignore

Ensure `.gitignore` includes:

```gitignore
# Environment
.env
.env.local
.env.production

# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Docker
.docker/

# Logs
*.log
logs/

# Local uploads (production uses S3)
uploads/
*.tmp

# OS
.DS_Store
Thumbs.db
```

---

## Step 10: Create requirements.txt Update

Ensure `requirements.txt` includes production dependencies:

```txt
# Add if not present
gunicorn==21.2.0
pydantic-settings==2.1.0
```

Run:
```bash
pip install gunicorn pydantic-settings --break-system-packages
pip freeze | grep -E "gunicorn|pydantic-settings" >> requirements.txt
```

---

## Step 11: Commit and Merge to Main

```bash
# Ensure you're on develop
git checkout develop

# Add all production files
git add -A

# Commit
git commit -m "chore: add production deployment configuration

- Add production Dockerfile with gunicorn
- Add health check endpoint
- Add settings module with env configuration
- Add railway.json for Railway deployment
- Add render.yaml for Render blueprint
- Add .env.example for reference
- Update database.py for production URLs
- Update main.py with lifespan events and migrations

Ready for cloud deployment"

# Push develop
git push origin develop

# Now merge to main for deployment
git checkout main
git pull origin main
git merge develop
git push origin main

# Tag the production-ready release
git tag -a v0.8.0-rc1 -m "Release candidate: production config ready"
git push origin v0.8.0-rc1

# Return to develop for future work
git checkout develop
```

---

## Verification

Before proceeding to deployment:

1. ✅ On `main` branch with production config merged
2. ✅ `Dockerfile` exists in project root
3. ✅ `railway.json` exists
4. ✅ `render.yaml` exists
5. ✅ `.env.example` exists
6. ✅ `src/config/settings.py` exists
7. ✅ Health endpoint responds: `curl http://localhost:8000/health`
8. ✅ All tests still pass: `pytest -v`

---

**Next:** `2-RAILWAY-DEPLOY.md` →
