# Runbooks

Operational procedures for IP2A Database system administration.

## What is a Runbook?

A runbook is a step-by-step procedure for performing operational tasks. They are written so that someone unfamiliar with the system can follow them during an emergency.

## Available Runbooks

### Deployment & Operations

| Runbook | Purpose | Last Updated |
|---------|---------|--------------|
| [deployment.md](deployment.md) | Deploy new version | February 2026 |
| [backup-restore.md](backup-restore.md) | Backup and restore database | February 2026 |
| [disaster-recovery.md](disaster-recovery.md) | Recover from system failure | February 2026 |
| [incident-response.md](incident-response.md) | Handle outages and incidents | February 2026 |

### Scheduled Tasks

| Task | Frequency | Script |
|------|-----------|--------|
| Database Backup | Daily 2 AM | `scripts/backup_database.sh` |
| Audit Archival | Weekly Sun 3 AM | `scripts/archive_audit_logs.sh` |
| Session Cleanup | Daily 4 AM | `scripts/cleanup_sessions.sh` |
| Health Check | Every 5 min | `curl /health/ready` |

See `scripts/crontab.example` for cron configuration.

### Quick Health Check

```bash
# Liveness check
curl http://localhost:8000/health/live

# Readiness check (includes DB, S3)
curl http://localhost:8000/health/ready

# Metrics
curl http://localhost:8000/health/metrics
```

## Runbook Template

When creating a new runbook, include:
1. Overview and estimated time
2. Prerequisites
3. Step-by-step procedure with exact commands
4. Verification steps
5. Troubleshooting section
6. Rollback procedure
7. Emergency contacts
