# Runbook: Deployment

## Overview
Deploy a new version of IP2A Database to production.

**Estimated time:** 15-30 minutes

## Prerequisites
- Git access to repository
- SSH access to server (or Railway/Render dashboard access)
- Docker access

---

## REQUIRED ENVIRONMENT VARIABLES

These environment variables **MUST** be set in production. Missing any of these will cause issues.

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `AUTH_JWT_SECRET_KEY` | Yes | JWT signing key (see below) |
| `S3_ENDPOINT_URL` | For docs | S3-compatible storage endpoint |
| `S3_ACCESS_KEY_ID` | For docs | S3 access key |
| `S3_SECRET_ACCESS_KEY` | For docs | S3 secret key |
| `S3_BUCKET_NAME` | For docs | S3 bucket name |

### Generating JWT Secret Key

**CRITICAL:** If `AUTH_JWT_SECRET_KEY` is not set, a random key is generated on each restart. This invalidates all user sessions!

```bash
# Generate a secure key
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Set in Railway/Render environment variables:
AUTH_JWT_SECRET_KEY=<paste-key-here>
```

See: `docs/BUGS_LOG.md` Bug #006 for details.

---

## PRE-DEPLOYMENT

### Step 1: Backup Database
Follow [backup-restore.md](backup-restore.md) backup procedure first!

### Step 2: Review Changes
```bash
git log main..HEAD --oneline
```

---

## DEPLOYMENT

### Step 1: Connect to Server
```bash
ssh user@ip2a-server
cd ~/Projects/IP2A-Database-v2
```

### Step 2: Pull Latest Code
```bash
git fetch origin
git checkout main
git pull origin main
```

### Step 3: Rebuild and Restart
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Step 4: Run Migrations
```bash
docker exec ip2a-api alembic upgrade head
```

---

## VERIFICATION

### Step 1: Check Services Running
```bash
docker-compose ps
```
All services should show "Up".

### Step 2: Check API Health
```bash
curl http://localhost:8000/health
```

### Step 3: Check Logs for Errors
```bash
docker-compose logs --tail=50 api
```

---

## ROLLBACK

If deployment fails:

### Step 1: Revert to Previous Version
```bash
git checkout HEAD~1
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Step 2: Restore Database if Needed
Follow [backup-restore.md](backup-restore.md) restore procedure.

---

## Contacts
- Primary: [TODO: Add contact]
- Backup: [TODO: Add contact]
