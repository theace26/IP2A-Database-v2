# Runbook: Database Backup and Restore

> **Document Created:** January 28, 2026
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Active
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)

---

## Overview

Procedures for backing up and restoring the IP2A PostgreSQL 16 database.

**Deployment:** Railway (cloud PaaS) — PostgreSQL provided as a Railway service.

**Estimated time:**
- Backup: 5–10 minutes
- Restore: 15–30 minutes

## Prerequisites

- Railway CLI installed and authenticated (`railway login`)
- Access to Railway project dashboard
- Backup storage location access (local or S3)
- For local dev: Docker access

---

## BACKUP PROCEDURE

### Railway (Production)

#### Option A: Railway Dashboard (Easiest)

1. Open Railway dashboard → Select project → Select PostgreSQL service
2. Navigate to **Data** tab
3. Use built-in backup/snapshot tools
4. Download backup if needed for off-site storage

#### Option B: Railway CLI

```bash
# Connect to Railway PostgreSQL and create dump
railway connect postgres
# Then in the psql session:
# \q  (exit, use pg_dump instead)

# Or use pg_dump directly with Railway connection string
# Get DATABASE_URL from Railway dashboard → Variables
pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d_%H%M%S).sql
```

#### Option C: Direct pg_dump with Railway URL

```bash
# Set the Railway DATABASE_URL (from Railway dashboard → Service → Variables)
export DATABASE_URL="postgresql://user:pass@host:port/dbname"

# Create backup
pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backup_*.sql | tail -1
# File should be > 1MB for a populated database
```

#### Copy to Safe Location

```bash
# Copy to S3 for off-site storage (recommended)
aws s3 cp backup_*.sql s3://ip2a-backups/$(date +%Y/%m)/

# Or copy to local secure location
cp backup_*.sql /path/to/backup/location/
```

### Local Development (Docker Compose)

```bash
# Connect to local dev environment
cd ~/Projects/IP2A-Database-v2

# Create backup from Docker PostgreSQL
docker exec ip2a-db pg_dump -U postgres ip2a_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify
ls -lh backup_*.sql | tail -1
```

---

## RESTORE PROCEDURE

⚠️ **WARNING: This OVERWRITES the current database!**

### Railway (Production)

#### Option A: Railway Dashboard

1. Open Railway dashboard → Select PostgreSQL service
2. Use built-in restore/import tools if available
3. Or use CLI method below

#### Option B: Railway CLI / Direct Connection

```bash
# Set the Railway DATABASE_URL
export DATABASE_URL="postgresql://user:pass@host:port/dbname"

# Drop and recreate database (DESTRUCTIVE)
psql "$DATABASE_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Restore from backup
psql "$DATABASE_URL" < /path/to/backup_file.sql

# Verify
curl https://your-app.railway.app/health/ready
```

### Local Development (Docker Compose)

```bash
# Stop application
docker-compose stop api

# Restore database
docker exec -i ip2a-db psql -U postgres -c "DROP DATABASE IF EXISTS ip2a_db;"
docker exec -i ip2a-db psql -U postgres -c "CREATE DATABASE ip2a_db;"
docker exec -i ip2a-db psql -U postgres ip2a_db < /path/to/backup_file.sql

# Restart application
docker-compose start api

# Verify
curl http://localhost:5000/health
```

---

## Scheduled Backups

### Recommended Schedule

| Frequency | Type | Retention |
|-----------|------|-----------|
| Daily | Automated (Railway built-in) | 7 days |
| Weekly | Manual pg_dump to S3 | 30 days |
| Monthly | Full backup to S3 + local | 1 year |
| Pre-deployment | Manual snapshot | Until next deployment verified |

### Audit Log Considerations

The `audit_logs` table has immutability triggers (BEFORE UPDATE/DELETE) and a 7-year NLRA retention requirement. Backups must preserve:
- All audit log data (never truncate)
- Immutability trigger definitions
- See [Audit Maintenance Runbook](audit-maintenance.md) for archival procedures

---

## Troubleshooting

### Problem: "database is being accessed by other users"

**Local dev:** `docker-compose down` then `docker-compose up -d db`, wait 10 seconds, retry.

**Railway:** Use the Railway dashboard to restart the PostgreSQL service, or terminate active connections:
```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'railway' AND pid <> pg_backend_pid();
```

### Problem: Backup file is empty or too small

- Verify `DATABASE_URL` is correct
- Check that the database has data: `psql "$DATABASE_URL" -c "SELECT count(*) FROM members;"`
- Ensure pg_dump completed without errors

### Problem: Restore fails with permission errors

- Ensure the database user has CREATEDB or superuser privileges
- On Railway, use the credentials from the Railway-provided `DATABASE_URL`

---

## Contacts

| Role | Contact |
|------|---------|
| Primary DBA / Developer | Xerxes |
| Railway Support | https://railway.app/help |

---

## Cross-References

| Document | Location |
|----------|----------|
| Deployment Runbook | `/docs/runbooks/deployment.md` |
| Disaster Recovery Runbook | `/docs/runbooks/disaster-recovery.md` |
| Incident Response Runbook | `/docs/runbooks/incident-response.md` |
| Audit Maintenance Runbook | `/docs/runbooks/audit-maintenance.md` |
| ADR-012: Audit Logging Strategy | `/docs/decisions/ADR-012-audit-logging-strategy.md` |

---

## 📄 End-of-Session Documentation (MANDATORY)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture
> progress made this session. Scan `/docs/*` and make or create any relevant
> updates/documents to keep a historical record as the project progresses.
> Do not forget about ADRs — update as necessary.

---

*Document Version: 2.0*
*Last Updated: February 3, 2026*
