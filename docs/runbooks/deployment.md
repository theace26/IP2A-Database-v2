# Runbook: Deployment

## Overview
Deploy a new version of IP2A Database to production.

**Estimated time:** 15-30 minutes

## Prerequisites
- Git access to repository
- SSH access to server
- Docker access

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
