# UnionCore — Demo Environment Deployment
**Spoke:** Spoke 3: Infrastructure (routed directly from Hub)
**Target:** MacBook Pro M4 Pro — local demo for stakeholder presentations
**Estimated Effort:** 3-5 hours
**Prerequisites:** Docker Desktop installed and running, repo cloned

---

> **⚠️ EXECUTION CONTEXT: HOST MACHINE — NOT A DEV CONTAINER**
>
> This document is executed from the **host MacBook's terminal** in the project root directory (e.g., `~/Projects/IP2A-Database-v2`). It is NOT meant to run inside a dev container. The commands here create and manage Docker containers — you cannot do that from inside a container that doesn't exist yet.
>
> - **Phases 1-4:** Host terminal, project root. Docker builds, compose commands, file creation, `/etc/hosts` edits (requires `sudo`).
> - **Phase 5 only:** You `docker exec` into the running API container for Alembic migrations and seed data. Then `exit` back to the host.
> - **Phases 6-7:** Back on the host — browser verification and README creation.
>
> If Claude Code normally operates inside a dev container, this task requires **host-level access** for `docker compose` commands and the macOS `/etc/hosts` edit.

---

## MISSION

Get the UnionCore demo environment running at `https://unioncore.ibew46.local` on the developer's MacBook Pro M4 Pro. This is for stakeholder demonstrations — specifically to show the Access Database owner that UnionCore is a credible, polished system worth granting data access to.

When complete, the developer should be able to:
1. Run one command to start the demo stack
2. Open `https://unioncore.ibew46.local` in a browser
3. Click through a self-signed certificate warning
4. See the UnionCore login page
5. Log in with demo credentials
6. Navigate the system with realistic-looking demo data

---

## PRE-FLIGHT CHECKLIST

Before starting any work, verify ALL of the following:

```bash
# 1. Git status clean
git status
# Expected: clean working tree on main or current working branch

# 2. Docker Desktop is running
docker info
# Expected: Server version, no errors

# 3. Docker Compose v2 available
docker compose version
# Expected: v2.20+

# 4. No services on port 80 or 443
lsof -i :80
lsof -i :443
# Expected: nothing, or only Docker

# 5. Current project structure — understand what exists
find . -name "Dockerfile*" -o -name "docker-compose*" -o -name "Caddyfile*" | head -20
ls -la deployment/ 2>/dev/null || echo "deployment/ directory does not exist"
ls -la deployment/caddy/ 2>/dev/null || echo "deployment/caddy/ directory does not exist"

# 6. Check if Dockerfile has a production stage already
grep -n "AS production" Dockerfile 2>/dev/null || echo "NO PRODUCTION STAGE FOUND"

# 7. Find where templates and static assets live (critical for Dockerfile COPY)
find . -type d -name "templates" | grep -v node_modules | grep -v __pycache__
find . -type d -name "static" | grep -v node_modules | grep -v __pycache__

# 8. Check if seed scripts exist
find . -name "*seed*" -o -name "*demo_data*" | grep -v __pycache__ | grep -v node_modules

# 9. Check current alembic config
cat alembic.ini | grep sqlalchemy.url
ls alembic/versions/ | head -10
```

**STOP HERE. Read the output. Understand the current state before proceeding.**

Record what you find:
- [ ] Does a `deployment/` directory exist? What's in it?
- [ ] Does the Dockerfile have a `production` stage?
- [ ] Where do `templates/` and `static/` live? (root? `src/`? elsewhere?)
- [ ] Do seed scripts exist? What do they seed?
- [ ] Is `alembic.ini` using an environment variable for `sqlalchemy.url` or a hardcoded string?

---

## PHASE 1: DOCKERFILE PRODUCTION STAGE

**Skip this phase if the Dockerfile already has a working `production` stage.**

### Step 1.1: Analyze the Existing Dockerfile

```bash
cat Dockerfile
```

Read the entire Dockerfile. Understand:
- What base image it uses
- What stages exist (development? builder? base?)
- How dependencies are installed
- What directories are COPYed
- Whether it uses a `.dockerignore` file

```bash
cat .dockerignore 2>/dev/null || echo "No .dockerignore found"
```

### Step 1.2: Add the Production Stage

Append a new `production` stage to the existing Dockerfile. **Do NOT modify or remove any existing stages.**

The production stage must:
1. Use the same Python base image version as the existing stages
2. Install only production dependencies (NO pytest, coverage, black, flake8, mypy)
3. Install `gunicorn` (the production ASGI server)
4. Copy application code, templates, static assets, and alembic migrations
5. Create and use a non-root user (`appuser`, UID 1000)
6. Expose port 8000
7. Default CMD uses gunicorn with uvicorn workers

**CRITICAL: Adapt COPY paths to match what you found in pre-flight step 7.** The template below is a starting point — adjust based on actual project structure.

```dockerfile
# ─── Production Stage ──────────────────────────────────────
# Used by demo and production docker-compose configs
FROM python:3.12-slim AS production

WORKDIR /app

# System dependencies (if WeasyPrint or other system libs are needed)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     <system-deps-if-needed> \
#     && rm -rf /var/lib/apt/lists/*

# Install production Python dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
# ⚠️  ADJUST THESE PATHS based on pre-flight findings
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Copy frontend assets — VERIFY actual locations first
# If templates are at src/templates/:
#   COPY src/templates/ ./src/templates/   (already covered by COPY src/)
# If templates are at root templates/:
#   COPY templates/ ./templates/
# Same logic for static/

# Security: non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "src.main:app", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]
```

### Step 1.3: Verify the Production Build

```bash
# Build the production stage
docker build --target production -t unioncore-prod-test .

# Verify the app imports cleanly
docker run --rm unioncore-prod-test python -c "from src.main import app; print('App loaded OK')"

# Verify non-root user
docker run --rm unioncore-prod-test whoami
# Expected: appuser

# Verify the existing development build still works
docker build --target development -t unioncore-dev-test . 2>/dev/null \
  || docker build -t unioncore-dev-test .
```

### Acceptance Criteria — Phase 1
- [ ] Production stage builds without errors
- [ ] App module imports successfully in production container
- [ ] Container runs as `appuser`, not root
- [ ] Development/default build is unaffected
- [ ] No dev tools (pytest, coverage) in production image

---

## PHASE 2: DEPLOYMENT DIRECTORY STRUCTURE

### Step 2.1: Create Directory Structure

Create the following if it doesn't already exist. **If files already exist, read them first — they may have been generated in a previous session. Update rather than overwrite.**

```
deployment/
├── docker-compose.demo.yml
├── .env.demo.example
├── caddy/
│   └── Caddyfile.demo
├── scripts/
│   └── setup-demo-macos.sh
└── README.md
```

```bash
mkdir -p deployment/caddy deployment/scripts
```

### Step 2.2: Create docker-compose.demo.yml

**If this file already exists, read it first and update rather than replace.**

This is a **standalone** compose file (not an overlay). It defines the full demo stack.

```yaml
# UnionCore Demo Configuration
#
# STANDALONE compose file for demo mode.
# Usage: docker compose -f docker-compose.demo.yml --env-file .env.demo up -d
#
# Designed for local laptop demonstrations on macOS.
# Provides HTTPS via Caddy with self-signed certificates.
# All services except Caddy are internal-only (no exposed ports).

services:
  # ═══════════════════════════════════════════════════════════
  # REVERSE PROXY — Entry point for all web traffic
  # ═══════════════════════════════════════════════════════════
  caddy:
    image: caddy:2-alpine
    container_name: unioncore-caddy
    restart: unless-stopped
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./caddy/Caddyfile.demo:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      api:
        condition: service_healthy
    networks:
      - unioncore-demo

  # ═══════════════════════════════════════════════════════════
  # APPLICATION SERVER — FastAPI via Gunicorn
  # ═══════════════════════════════════════════════════════════
  api:
    build:
      context: ..
      dockerfile: Dockerfile
      target: production
    container_name: unioncore-api
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://${DB_USER:-unioncore}:${DB_PASSWORD}@db:5432/${DB_NAME:-unioncore_demo}
      - STORAGE_ENDPOINT=minio:9000
      - STORAGE_ACCESS_KEY=${MINIO_ACCESS_KEY:-minioadmin}
      - STORAGE_SECRET_KEY=${MINIO_SECRET_KEY:-minioadmin}
      - SECRET_KEY=${JWT_SECRET}
      - ENVIRONMENT=demo
      - DEBUG=false
      - TRUSTED_HOST=unioncore.ibew46.local
    depends_on:
      db:
        condition: service_healthy
      minio:
        condition: service_started
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - unioncore-demo
    # No ports exposed — Caddy handles external access

  # ═══════════════════════════════════════════════════════════
  # DATABASE — PostgreSQL 16
  # ═══════════════════════════════════════════════════════════
  db:
    image: postgres:16-alpine
    container_name: unioncore-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=${DB_USER:-unioncore}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME:-unioncore_demo}
    volumes:
      - postgres_demo_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-unioncore}"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - unioncore-demo
    # No ports exposed — internal only

  # ═══════════════════════════════════════════════════════════
  # OBJECT STORAGE — MinIO (S3-compatible)
  # ═══════════════════════════════════════════════════════════
  minio:
    image: minio/minio:latest
    container_name: unioncore-minio
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=${MINIO_ACCESS_KEY:-minioadmin}
      - MINIO_ROOT_PASSWORD=${MINIO_SECRET_KEY:-minioadmin}
    volumes:
      - minio_demo_data:/data
    networks:
      - unioncore-demo
    # No ports exposed — internal only

volumes:
  postgres_demo_data:
  minio_demo_data:
  caddy_data:
  caddy_config:

networks:
  unioncore-demo:
    driver: bridge
```

**IMPORTANT NOTES:**
- The `build.context` is `..` because docker-compose.demo.yml lives in `deployment/`, and the Dockerfile is in the repo root
- The health check on the API assumes a `/api/v1/health` endpoint exists. **Verify this.** If the health endpoint is at a different path, adjust it. If no health endpoint exists, either create one or remove the healthcheck and use `condition: service_started` instead.
- The `DB_PASSWORD` and `JWT_SECRET` have no defaults — they MUST be set in `.env.demo`

### Step 2.3: Create Caddyfile.demo

```bash
cat > deployment/caddy/Caddyfile.demo << 'EOF'
# UnionCore Demo — Caddy Reverse Proxy Configuration
# Self-signed TLS for local laptop demonstrations
{
    # Use internal CA for self-signed certs (no internet required)
    local_certs
}

https://unioncore.ibew46.local, https://localhost {
    # Proxy all requests to FastAPI
    reverse_proxy api:8000

    # Security headers
    header {
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        # Remove server identification
        -Server
    }

    # Access logging
    log {
        output stdout
        format console
    }
}
EOF
```

### Step 2.4: Create .env.demo.example

```bash
cat > deployment/.env.demo.example << 'EOF'
# UnionCore Demo Environment Configuration
# Copy this file to .env.demo and fill in the values
# NEVER commit .env.demo to version control

# Database
DB_USER=unioncore
DB_PASSWORD=CHANGE_ME_demo_password_2026
DB_NAME=unioncore_demo

# JWT Secret (generate with: python -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET=CHANGE_ME_generate_a_real_secret

# MinIO Object Storage
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=CHANGE_ME_minio_secret_2026

# SendGrid (optional for demo — leave blank to disable email)
SENDGRID_API_KEY=
EOF
```

### Step 2.5: Create the macOS Setup Script

```bash
cat > deployment/scripts/setup-demo-macos.sh << 'SCRIPT_EOF'
#!/bin/bash
# UnionCore Demo — macOS Setup Script
# Adds unioncore.ibew46.local to /etc/hosts and creates .env.demo
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"

echo "╔══════════════════════════════════════════════════════╗"
echo "║        UnionCore Demo Environment Setup              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: /etc/hosts entry ────────────────────────────────
HOSTS_ENTRY="127.0.0.1    unioncore.ibew46.local"

if grep -q "unioncore.ibew46.local" /etc/hosts; then
    echo "✅ /etc/hosts already contains unioncore.ibew46.local"
else
    echo "Adding unioncore.ibew46.local to /etc/hosts (requires sudo)..."
    echo "$HOSTS_ENTRY" | sudo tee -a /etc/hosts > /dev/null
    echo "✅ Added to /etc/hosts"
fi

# ── Step 2: .env.demo file ─────────────────────────────────
ENV_FILE="$DEPLOY_DIR/.env.demo"

if [ -f "$ENV_FILE" ]; then
    echo "✅ .env.demo already exists at $ENV_FILE"
    echo "   Review it to ensure passwords are set."
else
    echo "Creating .env.demo from template..."
    cp "$DEPLOY_DIR/.env.demo.example" "$ENV_FILE"

    # Generate secure defaults
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    DB_PASS="demo_$(python3 -c "import secrets; print(secrets.token_hex(8))")"
    MINIO_PASS="minio_$(python3 -c "import secrets; print(secrets.token_hex(8))")"

    # Replace placeholders (macOS sed syntax)
    sed -i '' "s/CHANGE_ME_generate_a_real_secret/$JWT_SECRET/" "$ENV_FILE"
    sed -i '' "s/CHANGE_ME_demo_password_2026/$DB_PASS/" "$ENV_FILE"
    sed -i '' "s/CHANGE_ME_minio_secret_2026/$MINIO_PASS/" "$ENV_FILE"

    echo "✅ Created .env.demo with generated secrets"
    echo "   Location: $ENV_FILE"
fi

# ── Step 3: Verify Docker ──────────────────────────────────
if docker info > /dev/null 2>&1; then
    echo "✅ Docker Desktop is running"
else
    echo "❌ Docker Desktop is NOT running. Please start it first."
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Setup complete! Next steps:                         ║"
echo "║                                                      ║"
echo "║  cd deployment                                       ║"
echo "║  docker compose -f docker-compose.demo.yml \          ║"
echo "║    --env-file .env.demo up -d --build                ║"
echo "║                                                      ║"
echo "║  Then open: https://unioncore.ibew46.local            ║"
echo "╚══════════════════════════════════════════════════════╝"
SCRIPT_EOF

chmod +x deployment/scripts/setup-demo-macos.sh
```

### Step 2.6: Verify .gitignore Covers Secrets

```bash
# Check if .env.demo is gitignored
echo ".env.demo" | git check-ignore --stdin
# Expected: .env.demo

# If NOT ignored, add it
grep -q ".env.demo" .gitignore || echo -e "\n# Demo environment secrets\n.env.demo" >> .gitignore
grep -q ".env.demo" deployment/.gitignore 2>/dev/null || echo -e "\n# Demo environment secrets\n.env.demo" > deployment/.gitignore
```

### Acceptance Criteria — Phase 2
- [ ] `deployment/` directory structure matches the target
- [ ] `docker-compose.demo.yml` is valid YAML: `docker compose -f deployment/docker-compose.demo.yml config`
- [ ] `.env.demo.example` exists with placeholder values
- [ ] `.env.demo` is in `.gitignore` (verify with `git check-ignore`)
- [ ] `Caddyfile.demo` has correct domain (`unioncore.ibew46.local`)
- [ ] Setup script is executable: `ls -la deployment/scripts/setup-demo-macos.sh`
- [ ] No secrets are committed: `git diff --cached` shows no passwords

---

## PHASE 3: HOSTS FILE AND ENVIRONMENT SETUP

### Step 3.1: Run the Setup Script

```bash
cd deployment
chmod +x scripts/setup-demo-macos.sh
./scripts/setup-demo-macos.sh
```

This will:
1. Add `127.0.0.1 unioncore.ibew46.local` to `/etc/hosts` (asks for sudo)
2. Create `.env.demo` from the template with auto-generated secure passwords
3. Verify Docker Desktop is running

### Step 3.2: Verify Hosts Entry

```bash
ping -c 1 unioncore.ibew46.local
# Expected: PING unioncore.ibew46.local (127.0.0.1)
```

### Step 3.3: Verify .env.demo Has Real Values

```bash
cat deployment/.env.demo
```

Confirm that:
- `DB_PASSWORD` is NOT `CHANGE_ME...`
- `JWT_SECRET` is NOT `CHANGE_ME...`
- `MINIO_SECRET_KEY` is NOT `CHANGE_ME...`

### Acceptance Criteria — Phase 3
- [ ] `ping unioncore.ibew46.local` resolves to 127.0.0.1
- [ ] `.env.demo` exists with generated (not placeholder) secrets
- [ ] Docker Desktop is running

---

## PHASE 4: BUILD AND START THE DEMO STACK

### Step 4.1: Build and Start

```bash
cd deployment

# Build the production image and start all services
docker compose -f docker-compose.demo.yml --env-file .env.demo up -d --build
```

**Expected output:** Four containers starting: `unioncore-caddy`, `unioncore-api`, `unioncore-db`, `unioncore-minio`

### Step 4.2: Watch the Logs (Wait for Healthy)

```bash
# Watch all services
docker compose -f docker-compose.demo.yml --env-file .env.demo logs -f
```

Wait for:
1. `unioncore-db` to show `database system is ready to accept connections`
2. `unioncore-api` to show the Gunicorn workers started (or FastAPI startup message)
3. `unioncore-caddy` to show `serving initial configuration`

Press `Ctrl+C` to exit log following.

### Step 4.3: Verify All Containers Are Running

```bash
docker compose -f docker-compose.demo.yml --env-file .env.demo ps
```

**Expected:** All four services showing `Up` or `Up (healthy)`

### Step 4.4: Troubleshoot If Anything Failed

```bash
# If a container exited, check its logs
docker compose -f docker-compose.demo.yml --env-file .env.demo logs api
docker compose -f docker-compose.demo.yml --env-file .env.demo logs db
docker compose -f docker-compose.demo.yml --env-file .env.demo logs caddy
docker compose -f docker-compose.demo.yml --env-file .env.demo logs minio
```

Common issues:
- **API can't connect to DB:** Check DATABASE_URL in compose matches DB_USER/DB_PASSWORD/DB_NAME
- **Caddy certificate error:** Make sure `local_certs` is in the Caddyfile global block
- **Port conflict:** Run `lsof -i :443` — something else may be using the port
- **Build failed:** Dockerfile COPY path mismatch — go back to Phase 1 and verify paths

### Acceptance Criteria — Phase 4
- [ ] `docker compose ps` shows all 4 services running
- [ ] No containers in `Exit` or `Restarting` state
- [ ] API container health check passes (if configured)

---

## PHASE 5: DATABASE MIGRATIONS AND SEED DATA

### Step 5.1: Run Alembic Migrations

```bash
# Shell into the API container
docker compose -f docker-compose.demo.yml --env-file .env.demo exec api bash

# Inside the container:
alembic upgrade head
```

**If alembic can't find the database:** Check that `alembic.ini` reads `sqlalchemy.url` from the `DATABASE_URL` environment variable, not a hardcoded string. If it's hardcoded, you need to update `alembic/env.py` to read from `os.environ`.

```python
# In alembic/env.py, verify this pattern exists:
import os
config.set_main_option("sqlalchemy.url", os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url")))
```

### Step 5.2: Create a Demo Admin User

Still inside the API container:

```bash
# Check if there's an existing user creation script
find /app -name "*create_user*" -o -name "*seed*" -o -name "*admin*" | grep -v __pycache__
```

**If a seed script exists:**
```bash
python -m src.seeds.run_seed
# or whatever the actual seed command is
```

**If no seed script exists, create a demo admin user programmatically:**

```python
python3 << 'PYEOF'
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Adjust import paths based on actual project structure
try:
    from src.models.user import User
    from src.services.auth_service import AuthService
    print("Imports successful")
except ImportError as e:
    print(f"Import failed: {e}")
    print("You'll need to adjust the import paths for your project structure")
    exit(1)

# Check what's available and create a basic admin user
# This is a FALLBACK — use the project's actual seed scripts if they exist
PYEOF
```

**IMPORTANT:** The actual user creation method depends on the project's auth implementation. Check:
- Does `AuthService` have a `create_user` or `register` method?
- Does the `User` model use bcrypt for password hashing?
- What fields are required (username? email? role?)?

If you can't create a user programmatically, **document what's missing and flag it as a blocker.** The demo is useless without login credentials.

### Step 5.3: Verify Data

```bash
# Still inside the API container
python3 -c "
import asyncio
# Quick check — adjust imports to match project
print('Database connection and basic query test')
"
```

Exit the container:
```bash
exit
```

### Acceptance Criteria — Phase 5
- [ ] `alembic upgrade head` completed without errors
- [ ] At least one admin user exists with known credentials
- [ ] Database has tables created (verify via Alembic or direct query)

---

## PHASE 6: BROWSER VERIFICATION

### Step 6.1: Open the Demo

```bash
# On macOS
open https://unioncore.ibew46.local
```

### Step 6.2: Handle the Certificate Warning

You WILL see a certificate warning because Caddy is using a self-signed cert from its internal CA.

**Safari:** Click "Show Details" → "visit this website" → enter your Mac password
**Chrome:** Click "Advanced" → "Proceed to unioncore.ibew46.local (unsafe)"
**Firefox:** Click "Advanced" → "Accept the Risk and Continue"

**This is expected and correct.** Self-signed certs are not trusted by browsers. For a demo, this is fine — just click through it before the stakeholder arrives.

### Step 6.3: Verify the Login Page

You should see the UnionCore login page. Log in with the demo admin credentials created in Phase 5.

### Step 6.4: Smoke Test

After login, verify:
- [ ] Dashboard loads (or whatever the post-login landing page is)
- [ ] Navigation works (sidebar, top menu)
- [ ] At least one data page loads without errors (e.g., member list, referral books)

### Acceptance Criteria — Phase 6
- [ ] `https://unioncore.ibew46.local` loads in a browser
- [ ] Security headers are present: `curl -kI https://unioncore.ibew46.local` shows X-Frame-Options, X-Content-Type-Options, etc.
- [ ] Login works with demo credentials
- [ ] Post-login navigation functions

---

## PHASE 7: DEMO OPERATIONS REFERENCE

These are the commands the developer will use day-to-day with the demo stack. **Add these to `deployment/README.md`.**

```markdown
## Quick Reference

### Start the demo
```bash
cd deployment
docker compose -f docker-compose.demo.yml --env-file .env.demo up -d
```

### Stop the demo (preserves data)
```bash
docker compose -f docker-compose.demo.yml --env-file .env.demo down
```

### Stop and DESTROY all data
```bash
docker compose -f docker-compose.demo.yml --env-file .env.demo down -v
```

### Rebuild after code changes
```bash
docker compose -f docker-compose.demo.yml --env-file .env.demo up -d --build
```

### View logs
```bash
# All services
docker compose -f docker-compose.demo.yml --env-file .env.demo logs -f

# Specific service
docker compose -f docker-compose.demo.yml --env-file .env.demo logs -f api
```

### Shell into the API container
```bash
docker compose -f docker-compose.demo.yml --env-file .env.demo exec api bash
```

### Run database migrations
```bash
docker compose -f docker-compose.demo.yml --env-file .env.demo exec api alembic upgrade head
```

### Database backup
```bash
docker compose -f docker-compose.demo.yml --env-file .env.demo exec db \
  pg_dump -U unioncore unioncore_demo > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Database restore
```bash
cat backup_file.sql | docker compose -f docker-compose.demo.yml --env-file .env.demo exec -T db \
  psql -U unioncore unioncore_demo
```
```

### Acceptance Criteria — Phase 7
- [ ] `deployment/README.md` contains all quick reference commands
- [ ] Commands are tested and work correctly

---

## ANTI-PATTERNS — DO NOT

1. **DO NOT** expose database or MinIO ports to the host in the demo compose. Only Caddy (80/443) should be exposed.
2. **DO NOT** use `DEBUG=true` in the demo stack. This exposes stack traces.
3. **DO NOT** put real member PII in the demo database. Use realistic-but-fake names and data.
4. **DO NOT** commit `.env.demo` to git. Only `.env.demo.example` gets committed.
5. **DO NOT** leave the demo stack running unattended on a shared network.
6. **DO NOT** modify the development `docker-compose.yml` to accommodate demo needs. The demo has its own standalone compose file.
7. **DO NOT** install dev tools in the production Docker stage.
8. **DO NOT** run the API container as root.
9. **DO NOT** skip the Alembic migration step — the database needs its schema.
10. **DO NOT** hardcode passwords in `docker-compose.demo.yml` — they come from `.env.demo`.

---

## KNOWN BLOCKERS AND DECISION POINTS

| Blocker | Impact | Resolution |
|---------|--------|------------|
| No Dockerfile `production` stage | Cannot build demo image | Phase 1 of this document |
| No health check endpoint (`/api/v1/health`) | Compose health check fails, Caddy may start before API | Create a basic health endpoint OR remove health check from compose |
| No seed scripts or stale seed scripts | Demo shows empty system — bad stakeholder impression | Generate or update seed scripts (may require Spoke 1 + Spoke 2 coordination) |
| Alembic uses hardcoded DATABASE_URL | Migrations fail in demo container | Update `alembic/env.py` to read from environment variable |
| Templates/static at unexpected paths | Dockerfile COPY fails | Pre-flight step 7 catches this — adapt COPY paths accordingly |

**If you hit a blocker that requires domain-specific decisions (e.g., "what demo data should the dispatch board show?"), STOP and generate a handoff note to the Hub.** Do not make stakeholder-facing content decisions in an infrastructure context.

---

## GIT COMMIT

After all phases complete:

```
feat(infra): add demo deployment environment

- Add Dockerfile production stage (non-root, gunicorn)
- Add deployment/docker-compose.demo.yml (standalone demo stack)
- Add Caddy reverse proxy with self-signed TLS
- Add .env.demo.example template
- Add macOS setup script (hosts file + env generation)
- Add deployment/README.md with operations reference
- Verify all existing tests still pass
- Spoke 3: Infrastructure
```

---

## SESSION CLOSE-OUT

After completion:
- [ ] Update `CLAUDE.md` — note demo environment is operational
- [ ] Update `CHANGELOG.md` — add demo deployment entry
- [ ] Update ANY & ALL relevant documents under `/docs/*`
- [ ] Run the full test suite to verify no regressions: `pytest`
- [ ] Note any cross-Spoke impacts requiring handoff notes (especially if seed data is missing)
- [ ] Confirm the demo URL works end-to-end in a browser

**Return to Hub with:**
1. Confirmation that all acceptance criteria passed (or which ones didn't and why)
2. Any issues discovered (especially Dockerfile COPY path adjustments, missing health endpoint, seed data gaps)
3. Updated `CHANGELOG.md` entry
4. Version bump recommendation for `CLAUDE.md`

---

*Hub → Claude Code Direct Instruction — 2026-02-09*
*UnionCore (IP2A-Database-v2)*
