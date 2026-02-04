# Runbook: Deployment

> **Document Created:** January 28, 2026
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Active
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)

---

## Overview

Deploy a new version of IP2A Database (UnionCore) to production.

**Primary Deployment:** Railway (cloud PaaS) — auto-deploys from GitHub on push to `develop`.
**Local Development:** Docker Compose or `flask run` for local testing.

**Estimated time:** 5–15 minutes (Railway auto-deploy), 15–30 minutes (manual/first-time)

## Prerequisites

- Git access to repository (https://github.com/theace26/IP2A-Database-v2)
- Railway CLI installed and authenticated (`railway login`), or Railway dashboard access
- For local dev: Docker + Docker Compose, or Python 3.12 with venv

---

## REQUIRED ENVIRONMENT VARIABLES

These environment variables **MUST** be set in the Railway service. Missing any of these will cause issues.

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (auto-set by Railway) |
| `AUTH_JWT_SECRET_KEY` | Yes | JWT signing key (see below) |
| `SENTRY_DSN` | Yes | Sentry error monitoring DSN |
| `STRIPE_SECRET_KEY` | Yes | Stripe API secret key |
| `STRIPE_WEBHOOK_SECRET` | Yes | Stripe webhook signing secret |
| `STRIPE_PUBLISHABLE_KEY` | Yes | Stripe publishable key (frontend) |
| `S3_ENDPOINT_URL` | For docs | S3-compatible storage endpoint |
| `S3_ACCESS_KEY_ID` | For docs | S3 access key |
| `S3_SECRET_ACCESS_KEY` | For docs | S3 secret key |
| `S3_BUCKET_NAME` | For docs | S3 bucket name |
| `FLASK_ENV` | Recommended | `production` or `development` |
| `SECRET_KEY` | Yes | Flask session secret key |

### Generating JWT Secret Key

**CRITICAL:** If `AUTH_JWT_SECRET_KEY` is not set, a random key is generated on each restart. This invalidates all user sessions!

```bash
# Generate a secure key
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Set in Railway environment variables:
# Railway → Project → Service → Variables → New Variable
# AUTH_JWT_SECRET_KEY=<paste-key-here>
```

See: `docs/BUGS_LOG.md` Bug #006 for details.

---

## DEPLOYMENT — RAILWAY (PRIMARY)

### Automatic Deployment (Standard)

Railway auto-deploys when changes are pushed to the `develop` branch:

```bash
# 1. Ensure all tests pass locally
pytest -v

# 2. Commit and push to develop
git add .
git commit -m "feat: description of changes"
git push origin develop

# 3. Railway auto-detects the push and deploys
# Monitor in Railway dashboard → Deployments tab
```

### Manual Deployment (Railway CLI)

```bash
# Deploy from current local state
railway up --detach

# Or link to specific service first
railway link
railway up
```

### First-Time Railway Setup

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to existing project
railway link

# Set environment variables (if not already set)
railway variables set AUTH_JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
railway variables set FLASK_ENV=production
# ... set remaining variables
```

---

## PRE-DEPLOYMENT CHECKLIST

### Step 1: Backup Database
Follow [Backup & Restore Runbook](backup-restore.md) backup procedure first!

### Step 2: Run Tests
```bash
# Run full test suite (~470 tests)
pytest -v

# Or run quick validation
./ip2adb all --quick
```

### Step 3: Review Changes
```bash
git log origin/develop..HEAD --oneline
```

### Step 4: Check for Migration Changes
```bash
# If there are new Alembic migrations, they will run automatically
# Verify migrations are clean
alembic check
```

---

## POST-DEPLOYMENT VERIFICATION

### Step 1: Check Deployment Status
- Railway dashboard → Deployments tab → Verify "Success" status
- Check build logs for any warnings

### Step 2: Check Health Endpoint
```bash
curl https://your-app.railway.app/health/ready
# Should return JSON with all checks passing
```

### Step 3: Check Sentry for Errors
- Open Sentry dashboard
- Filter by environment: `production`
- Check for new errors in the last 15 minutes

### Step 4: Verify Key Features
- [ ] Login works (JWT sessions valid)
- [ ] Member search returns results
- [ ] Dues payments page loads
- [ ] Stripe webhook endpoint responds (check Stripe dashboard)

---

## ROLLBACK

If deployment fails or introduces issues:

### Railway Rollback (Fastest)

```bash
# Via Railway dashboard:
# Deployments tab → Find last good deployment → Click "Redeploy"

# Via Railway CLI:
railway rollback
```

### Git-based Rollback

```bash
# Revert the problematic commit (creates new commit — preferred)
git revert <commit-hash>
git push origin develop
# Railway will auto-deploy the revert

# Or reset to previous state (destructive — last resort)
git reset --hard <good-commit-hash>
git push origin develop --force
```

### Database Rollback (if needed)

If migrations caused issues:
```bash
# Connect to Railway PostgreSQL
railway connect postgres

# Or rollback Alembic migration
alembic downgrade -1
```

For full database restore, follow [Backup & Restore Runbook](backup-restore.md).

---

## LOCAL DEVELOPMENT DEPLOYMENT

### Docker Compose (Full Stack)

```bash
cd ~/Projects/IP2A-Database-v2

# Start all services
docker-compose up -d

# Run migrations
docker exec ip2a-api alembic upgrade head

# Verify
curl http://localhost:5000/health
```

### Flask Development Server

```bash
cd ~/Projects/IP2A-Database-v2

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Set environment variables
export FLASK_ENV=development
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ip2a_db

# Run migrations
alembic upgrade head

# Start Flask dev server
flask run
# → http://localhost:5000
```

> **Note:** The development server uses `flask run` (port 5000), not `uvicorn` (port 8000).
> The project uses Flask, not FastAPI.

---

## Branch Strategy

| Branch | Purpose | Deploys To |
|--------|---------|------------|
| `develop` | Active development (v0.9.4-alpha) | Railway (auto-deploy) |
| `main` | Stable releases | Manual deploy (currently behind develop) |
| Feature branches | Individual features | Local only |

> **Current State:** The `main` branch needs a merge from `develop`. All active work
> happens on `develop`.

---

## Contacts

| Role | Contact |
|------|---------|
| Primary Developer | Xerxes |
| Railway Support | https://railway.app/help |
| Stripe Support | https://support.stripe.com |
| Sentry Support | https://sentry.io/support |

---

## Cross-References

| Document | Location |
|----------|----------|
| Backup & Restore Runbook | `/docs/runbooks/backup-restore.md` |
| Incident Response Runbook | `/docs/runbooks/incident-response.md` |
| Disaster Recovery Runbook | `/docs/runbooks/disaster-recovery.md` |
| ip2adb CLI Reference | `/docs/reference/ip2adb-cli.md` |
| ADR-007: Monitoring Strategy (Sentry) | `/docs/decisions/ADR-007-monitoring-strategy.md` |
| BUGS_LOG (Bug #006 — JWT Secret) | `/docs/BUGS_LOG.md` |

---

## 📄 End-of-Session Documentation (MANDATORY)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture
> progress made this session. Scan `/docs/*` and make or create any relevant
> updates/documents to keep a historical record as the project progresses.
> Do not forget about ADRs — update as necessary.

---

*Document Version: 2.0*
*Last Updated: February 3, 2026*
