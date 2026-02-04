# Runbook: Disaster Recovery

> **Document Created:** January 28, 2026
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Active
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)

---

## Overview

Recover IP2A Database (UnionCore) from partial or complete system failure.

**Primary Deployment:** Railway (cloud PaaS) with PostgreSQL 16.
**Source Code:** GitHub — https://github.com/theace26/IP2A-Database-v2

**Estimated time:** 30 minutes – 2 hours depending on scenario

## Prerequisites

- Access to GitHub repository
- Railway CLI installed and authenticated, or Railway dashboard access
- Access to backup files (S3 or local)
- For full rebuild: Railway account with billing configured

---

## SCENARIOS

### Scenario A: Application Service Crashed

**Symptoms:** API not responding, but Railway PostgreSQL service is still running.

**Recovery:**
```bash
# Check Railway service status
# Railway dashboard → Project → Service → check "Active" status

# Restart the application service via Railway
railway restart

# Check logs for errors
railway logs --tail 50

# Check Sentry for error details
# https://sentry.io → Filter by environment: production

# Verify health
curl https://your-app.railway.app/health/ready
```

### Scenario B: Database Service Crashed

**Symptoms:** API shows database connection errors, Sentry reports connection failures.

**Recovery:**
```bash
# Check Railway PostgreSQL service status
# Railway dashboard → Project → PostgreSQL service

# If service is down, restart it via Railway dashboard
# PostgreSQL service → Settings → Restart

# Wait 30–60 seconds for PostgreSQL to initialize

# Restart the application service
railway restart

# Verify health
curl https://your-app.railway.app/health/ready | jq .checks.database
```

### Scenario C: Railway Region Outage

**Symptoms:** Both application and database services unreachable, Railway status page shows incident.

**Recovery:**
1. Check Railway status page: https://status.railway.app
2. Wait for Railway to resolve the outage (most outages resolve within 1–2 hours)
3. If extended outage, consider deploying to an alternative Railway region:
   ```bash
   # Create new project in different region
   railway init --name ip2a-disaster-recovery
   # Set environment variables and deploy
   ```

### Scenario D: Database Corruption or Data Loss

**Symptoms:** Application runs but data is missing, corrupted, or integrity checks fail.

**Recovery:**
```bash
# 1. Assess the damage
./ip2adb integrity --force --no-files

# 2. If auto-repairable
./ip2adb integrity --force --repair --dry-run
./ip2adb integrity --force --repair

# 3. If data loss, restore from backup
# See Backup & Restore Runbook: backup-restore.md
```

### Scenario E: Complete Rebuild (Worst Case)

**Symptoms:** Everything is lost — need to rebuild from scratch.

**Recovery:**

1. **Create new Railway project**
   ```bash
   railway login
   railway init --name ip2a-production
   ```

2. **Add PostgreSQL service**
   - Railway dashboard → New Service → PostgreSQL
   - Note the `DATABASE_URL` from Variables

3. **Clone repository**
   ```bash
   git clone https://github.com/theace26/IP2A-Database-v2.git
   cd IP2A-Database-v2
   git checkout develop
   ```

4. **Set environment variables** (see [Deployment Runbook](deployment.md) for full list)
   ```bash
   railway variables set AUTH_JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
   railway variables set FLASK_ENV=production
   railway variables set SENTRY_DSN=<your-sentry-dsn>
   railway variables set STRIPE_SECRET_KEY=<your-stripe-key>
   railway variables set STRIPE_WEBHOOK_SECRET=<your-webhook-secret>
   railway variables set STRIPE_PUBLISHABLE_KEY=<your-publishable-key>
   # ... set S3 variables, SECRET_KEY, etc.
   ```

5. **Deploy application**
   ```bash
   railway up --detach
   ```

6. **Run migrations**
   ```bash
   railway run alembic upgrade head
   ```

7. **Restore database from backup**
   Follow [Backup & Restore Runbook](backup-restore.md) restore procedure.

8. **Verify system**
   ```bash
   curl https://your-app.railway.app/health/ready

   # Run integrity check
   railway run ./ip2adb integrity --force --no-files
   ```

9. **Update Stripe webhook URL**
   - Stripe dashboard → Webhooks → Update endpoint URL to new Railway URL

10. **Update Sentry project DSN** if using a new Sentry project

### Scenario F: Local Development Recovery

For rebuilding a local development environment:

```bash
# Clone repository
git clone https://github.com/theace26/IP2A-Database-v2.git
cd IP2A-Database-v2
git checkout develop

# Start with Docker Compose
cp .env.compose.example .env.compose
# Edit .env.compose with local credentials
docker-compose up -d

# Run migrations
docker exec ip2a-api alembic upgrade head

# Seed development data
./ip2adb seed --quick

# Verify
curl http://localhost:5000/health
```

---

## BACKUP LOCATIONS

| Backup Type | Location | Retention |
|-------------|----------|-----------|
| Railway auto-backups | Railway PostgreSQL service | Varies by plan |
| Manual pg_dump | S3 (`s3://ip2a-backups/`) | 30 days |
| Audit log archives | S3 Glacier (`s3://ip2a-audit-archive/`) | 7 years (NLRA) |
| Source code | GitHub (theace26/IP2A-Database-v2) | Indefinite |
| File attachments | S3 (primary bucket) | Indefinite |

---

## RECOVERY PRIORITY ORDER

When recovering, prioritize in this order:

1. **Database** — Member data, dues records, audit logs are the most critical
2. **Application** — The Flask application serving the UI and API
3. **Monitoring** — Sentry error tracking
4. **Payments** — Stripe webhook integration
5. **Storage** — S3 file attachments
6. **Analytics** — Chart.js dashboards (can be regenerated from data)

---

## Contacts

| Role | Contact |
|------|---------|
| Primary Developer / DBA | Xerxes |
| GitHub | https://github.com/theace26/IP2A-Database-v2 |
| Railway Support | https://railway.app/help |
| Railway Status | https://status.railway.app |
| Stripe Support | https://support.stripe.com |
| Sentry Support | https://sentry.io/support |
| AWS Support (S3) | AWS Console |

---

## Cross-References

| Document | Location |
|----------|----------|
| Backup & Restore Runbook | `/docs/runbooks/backup-restore.md` |
| Deployment Runbook | `/docs/runbooks/deployment.md` |
| Incident Response Runbook | `/docs/runbooks/incident-response.md` |
| Audit Maintenance Runbook | `/docs/runbooks/audit-maintenance.md` |
| ip2adb CLI Reference | `/docs/reference/ip2adb-cli.md` |
| ADR-007: Monitoring Strategy (Sentry) | `/docs/decisions/ADR-007-monitoring-strategy.md` |

---

## 📄 End-of-Session Documentation (MANDATORY)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture
> progress made this session. Scan `/docs/*` and make or create any relevant
> updates/documents to keep a historical record as the project progresses.
> Do not forget about ADRs — update as necessary.

---

*Document Version: 2.0*
*Last Updated: February 3, 2026*
