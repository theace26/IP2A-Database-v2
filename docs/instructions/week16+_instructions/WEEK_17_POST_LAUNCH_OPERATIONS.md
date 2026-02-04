# Week 17: Post-Launch Operations & Maintenance

**Version:** 1.0.0  
**Created:** February 2, 2026  
**Branch:** `develop`  
**Estimated Effort:** 4-6 hours (2 sessions)  
**Dependencies:** Week 16 (Production Hardening) complete, system live

---

## Overview

With the system live, this week establishes **operational procedures** for ongoing maintenance, monitoring, and support. This includes backup automation, monitoring dashboards, user support workflows, and scheduled maintenance tasks.

### Objectives

- [ ] Automated backup scripts with verification
- [ ] Monitoring dashboard setup
- [ ] User support ticketing integration
- [ ] Scheduled maintenance jobs (audit archival, cleanup)
- [ ] Runbook updates for common operations
- [ ] On-call documentation

### Out of Scope

- New feature development
- Major refactoring
- Database migrations (unless for maintenance)

---

## Pre-Flight Checklist

- [ ] On `develop` branch
- [ ] Production system stable for 1+ week
- [ ] Week 16 security/performance complete
- [ ] Access to production logs
- [ ] Backup storage configured (S3/local)

---

## Phase 1: Automated Backups (Session 1)

### 1.1 Backup Script

Create `scripts/backup_database.sh`:

```bash
#!/bin/bash
# Database backup script for UnionCore
# Run via cron: 0 2 * * * /path/to/backup_database.sh

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/unioncore}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DB_HOST="${DB_HOST:-localhost}"
DB_NAME="${DB_NAME:-unioncore}"
DB_USER="${DB_USER:-postgres}"
S3_BUCKET="${S3_BUCKET:-}"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/unioncore_${TIMESTAMP}.sql.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

# Create backup
PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    | gzip > "$BACKUP_FILE"

# Verify backup
if [ ! -s "$BACKUP_FILE" ]; then
    echo "[$(date)] ERROR: Backup file is empty!"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date)] Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# Upload to S3 if configured
if [ -n "$S3_BUCKET" ]; then
    echo "[$(date)] Uploading to S3..."
    aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/backups/$(basename $BACKUP_FILE)"
    echo "[$(date)] S3 upload complete"
fi

# Clean up old backups
echo "[$(date)] Cleaning backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "unioncore_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] Backup complete!"
```

### 1.2 Backup Verification Script

Create `scripts/verify_backup.sh`:

```bash
#!/bin/bash
# Verify backup integrity

set -e

BACKUP_FILE="$1"
TEST_DB="unioncore_backup_test"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "[$(date)] Verifying backup: $BACKUP_FILE"

# Create test database
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -c "DROP DATABASE IF EXISTS $TEST_DB;"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -c "CREATE DATABASE $TEST_DB;"

# Restore to test database
echo "[$(date)] Restoring to test database..."
gunzip -c "$BACKUP_FILE" | PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$TEST_DB"

# Verify tables exist
TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$TEST_DB" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

echo "[$(date)] Found $TABLE_COUNT tables"

# Check critical tables
for table in members users audit_logs dues_payments students; do
    COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$TEST_DB" -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "0")
    echo "[$(date)] $table: $COUNT rows"
done

# Clean up
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -c "DROP DATABASE $TEST_DB;"

echo "[$(date)] Backup verification complete!"
```

### 1.3 Cron Configuration

Create `scripts/crontab.example`:

```cron
# UnionCore Scheduled Tasks
# Install with: crontab scripts/crontab.example

# Database backup - Daily at 2 AM
0 2 * * * /app/scripts/backup_database.sh >> /var/log/unioncore/backup.log 2>&1

# Audit log archival - Weekly on Sunday at 3 AM
0 3 * * 0 /app/scripts/archive_audit_logs.sh >> /var/log/unioncore/audit_archive.log 2>&1

# Session cleanup - Daily at 4 AM
0 4 * * * /app/scripts/cleanup_sessions.sh >> /var/log/unioncore/cleanup.log 2>&1

# Health check - Every 5 minutes
*/5 * * * * curl -sf http://localhost:8000/health/ready > /dev/null || echo "Health check failed at $(date)" >> /var/log/unioncore/health.log
```

---

## Phase 2: Audit Log Archival (Session 1)

### 2.1 Archive Script

Create `scripts/archive_audit_logs.sh`:

```bash
#!/bin/bash
# Archive audit logs older than 1 year to S3 Glacier

set -e

ARCHIVE_THRESHOLD_DAYS=365
S3_BUCKET="${S3_BUCKET:-}"
ARCHIVE_PREFIX="audit-archive"

echo "[$(date)] Starting audit log archival..."

# Export old audit logs to CSV
ARCHIVE_FILE="/tmp/audit_logs_archive_$(date +%Y%m%d).csv"

PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "\COPY (
    SELECT * FROM audit_logs 
    WHERE created_at < NOW() - INTERVAL '$ARCHIVE_THRESHOLD_DAYS days'
) TO '$ARCHIVE_FILE' WITH CSV HEADER;"

if [ -s "$ARCHIVE_FILE" ]; then
    ROW_COUNT=$(wc -l < "$ARCHIVE_FILE")
    echo "[$(date)] Exported $((ROW_COUNT - 1)) records to $ARCHIVE_FILE"
    
    # Compress
    gzip "$ARCHIVE_FILE"
    
    # Upload to S3 Glacier
    if [ -n "$S3_BUCKET" ]; then
        aws s3 cp "${ARCHIVE_FILE}.gz" \
            "s3://$S3_BUCKET/$ARCHIVE_PREFIX/$(basename ${ARCHIVE_FILE}.gz)" \
            --storage-class GLACIER
        echo "[$(date)] Uploaded to S3 Glacier"
    fi
    
    # Delete archived records (only after successful upload)
    # CAUTION: Uncomment only when confident in backup
    # PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
    #     DELETE FROM audit_logs 
    #     WHERE created_at < NOW() - INTERVAL '$ARCHIVE_THRESHOLD_DAYS days';"
    
    rm -f "${ARCHIVE_FILE}.gz"
else
    echo "[$(date)] No records to archive"
fi

echo "[$(date)] Audit archival complete!"
```

---

## Phase 3: Monitoring Dashboard (Session 2)

### 3.1 Admin Metrics Endpoint

Create `src/routers/ui/admin_metrics.py`:

```python
"""Admin metrics dashboard."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_async_session
from src.models import Member, User, AuditLog, DuesPayment, Student
from src.routers.dependencies.auth_cookie import get_current_user_from_cookie, require_admin
from src.templates import templates

router = APIRouter(prefix="/admin/metrics", tags=["admin-metrics"])


@router.get("", response_class=HTMLResponse)
@require_admin
async def metrics_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user_from_cookie),
):
    """Admin metrics dashboard."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today_start - timedelta(days=7)
    month_ago = today_start - timedelta(days=30)
    
    # User metrics
    total_users = await db.scalar(select(func.count(User.id)))
    active_users_today = await db.scalar(
        select(func.count(User.id))
        .where(User.last_login >= today_start)
    )
    
    # Member metrics
    total_members = await db.scalar(select(func.count(Member.id)))
    active_members = await db.scalar(
        select(func.count(Member.id))
        .where(Member.status == "active")
    )
    
    # Audit metrics
    audits_today = await db.scalar(
        select(func.count(AuditLog.id))
        .where(AuditLog.created_at >= today_start)
    )
    audits_week = await db.scalar(
        select(func.count(AuditLog.id))
        .where(AuditLog.created_at >= week_ago)
    )
    
    # Payment metrics
    payments_month = await db.scalar(
        select(func.sum(DuesPayment.amount))
        .where(DuesPayment.payment_date >= month_ago)
        .where(DuesPayment.status == "completed")
    ) or 0
    
    # Student metrics
    active_students = await db.scalar(
        select(func.count(Student.id))
        .where(Student.status == "active")
    )
    
    return templates.TemplateResponse(
        "admin/metrics.html",
        {
            "request": request,
            "user": current_user,
            "metrics": {
                "users": {
                    "total": total_users,
                    "active_today": active_users_today,
                },
                "members": {
                    "total": total_members,
                    "active": active_members,
                },
                "audit": {
                    "today": audits_today,
                    "week": audits_week,
                },
                "payments": {
                    "month_total": float(payments_month),
                },
                "students": {
                    "active": active_students,
                },
            },
            "generated_at": now.isoformat(),
        }
    )
```

### 3.2 Metrics Dashboard Template

Create `src/templates/admin/metrics.html`:

```html
{% extends "base.html" %}
{% block title %}System Metrics{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-6">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold">System Metrics</h1>
        <span class="text-sm text-gray-500">
            Generated: {{ generated_at[:19].replace('T', ' ') }}
        </span>
    </div>
    
    <!-- User Metrics -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-title">Total Users</div>
            <div class="stat-value text-primary">{{ metrics.users.total }}</div>
            <div class="stat-desc">{{ metrics.users.active_today }} active today</div>
        </div>
        
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-title">Members</div>
            <div class="stat-value">{{ metrics.members.total }}</div>
            <div class="stat-desc">{{ metrics.members.active }} active</div>
        </div>
        
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-title">Audit Logs Today</div>
            <div class="stat-value text-info">{{ metrics.audit.today }}</div>
            <div class="stat-desc">{{ metrics.audit.week }} this week</div>
        </div>
        
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-title">Payments (30d)</div>
            <div class="stat-value text-success">${{ "%.2f"|format(metrics.payments.month_total) }}</div>
            <div class="stat-desc">Completed payments</div>
        </div>
    </div>
    
    <!-- Quick Actions -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Quick Actions</h2>
            <div class="flex flex-wrap gap-2">
                <a href="/admin/audit-logs" class="btn btn-outline btn-sm">View Audit Logs</a>
                <a href="/reports" class="btn btn-outline btn-sm">Generate Reports</a>
                <a href="/health/ready" target="_blank" class="btn btn-outline btn-sm">Health Check</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Phase 4: Support & Runbooks (Session 2)

### 4.1 Update Runbook Index

Update `docs/runbooks/README.md`:

```markdown
# Operational Runbooks

## Daily Operations
| Runbook | Purpose | Frequency |
|---------|---------|-----------|
| [Health Check](health-check.md) | Verify system status | Every 5 min (automated) |
| [Log Review](log-review.md) | Check for errors | Daily |

## Weekly Operations
| Runbook | Purpose | Frequency |
|---------|---------|-----------|
| [Backup Verification](backup-verify.md) | Test restore process | Weekly |
| [Performance Review](performance-review.md) | Check metrics | Weekly |

## Monthly Operations
| Runbook | Purpose | Frequency |
|---------|---------|-----------|
| [Audit Archival](audit-archival.md) | Archive old logs | Monthly |
| [Security Review](security-review.md) | Check for vulnerabilities | Monthly |

## Emergency Procedures
| Runbook | Purpose |
|---------|---------|
| [Incident Response](incident-response.md) | Handle outages |
| [Rollback](rollback.md) | Revert deployments |
| [Disaster Recovery](disaster-recovery.md) | Full restoration |
```

### 4.2 Incident Response Runbook

Create `docs/runbooks/incident-response.md`:

```markdown
# Incident Response Runbook

## Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| P1 - Critical | System down | 15 minutes | Database offline |
| P2 - High | Major feature broken | 1 hour | Login failing |
| P3 - Medium | Feature degraded | 4 hours | Reports slow |
| P4 - Low | Minor issue | Next business day | UI glitch |

## Response Steps

### 1. Assess (5 minutes)
- [ ] Check /health/ready endpoint
- [ ] Check Railway/Render dashboard
- [ ] Check error logs: `railway logs` or Sentry
- [ ] Determine severity level

### 2. Communicate (5 minutes)
- [ ] Update status page (if applicable)
- [ ] Notify affected users
- [ ] Alert on-call team

### 3. Investigate (varies)
- [ ] Check recent deployments
- [ ] Review error logs
- [ ] Check database connections
- [ ] Verify external services (Stripe, S3)

### 4. Resolve
- [ ] Apply fix or rollback
- [ ] Verify resolution
- [ ] Monitor for recurrence

### 5. Document
- [ ] Create incident report
- [ ] Update runbooks if needed
- [ ] Schedule post-mortem (P1/P2 only)

## Common Issues

### Database Connection Errors
```bash
# Check database status
railway connect postgres

# Verify connection pool
curl http://localhost:8000/health/ready | jq .checks.database
```

### High Memory Usage
```bash
# Check container resources
railway logs --filter memory

# Restart if needed
railway restart
```

### Payment Webhook Failures
```bash
# Check Stripe dashboard for failed webhooks
# Retry from Stripe dashboard
# Check webhook endpoint logs
```

## Contacts

| Role | Contact |
|------|---------|
| Primary On-Call | [Your contact] |
| Secondary | [Backup contact] |
| Stripe Support | https://support.stripe.com |
| Railway Support | https://railway.app/help |
```

---

## Testing Requirements

### Test Files

- `tests/test_scripts/test_backup.py` - Backup script tests
- `src/tests/test_admin_metrics.py` - Metrics endpoint tests

### Manual Verification

1. **Backup**: Run backup script, verify file created
2. **Restore**: Test restore to staging
3. **Metrics**: Access /admin/metrics as admin
4. **Health**: Verify /health/ready shows all checks

---

## Acceptance Criteria

### Required

- [ ] Backup script runs successfully
- [ ] Backup verification script works
- [ ] Cron jobs documented
- [ ] Audit archival script ready
- [ ] Admin metrics dashboard functional
- [ ] Runbooks updated
- [ ] Incident response documented
- [ ] All scripts executable and tested

### Optional

- [ ] Slack/email alerting integration
- [ ] Automated restore testing
- [ ] Uptime monitoring (Pingdom/UptimeRobot)

---

## 📝 MANDATORY: End-of-Session Documentation

> **REQUIRED:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. **Do not forget about ADRs—update as necessary.**

### Quick Checklist

- [ ] `/CHANGELOG.md` — Version bump (v0.9.2-alpha)
- [ ] `/CLAUDE.md` — Update operations section
- [ ] `/docs/IP2A_MILESTONE_CHECKLIST.md` — Mark Week 17 complete
- [ ] `/docs/runbooks/*` — **Update all runbooks**
- [ ] `/docs/reports/session-logs/YYYY-MM-DD-operations-setup.md` — **Create session log**

---

*Last Updated: February 2, 2026*
