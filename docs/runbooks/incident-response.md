# Incident Response Runbook

> **Document Created:** February 2, 2026
> **Last Updated:** February 3, 2026
> **Version:** 1.1
> **Status:** Active
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)

---

## Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| P1 — Critical | System down | 15 minutes | Database offline |
| P2 — High | Major feature broken | 1 hour | Login failing |
| P3 — Medium | Feature degraded | 4 hours | Reports slow |
| P4 — Low | Minor issue | Next business day | UI glitch |

## Response Steps

### 1. Assess (5 minutes)

- [ ] Check `/health/ready` endpoint
- [ ] Check Railway dashboard (https://railway.app/dashboard)
- [ ] Check Sentry for errors (https://sentry.io)
- [ ] Determine severity level

### 2. Communicate (5 minutes)

- [ ] Update status page (if applicable)
- [ ] Notify affected users
- [ ] Alert on-call team

### 3. Investigate (varies)

- [ ] Check recent deployments on Railway
- [ ] Review error logs in Sentry
- [ ] Check database connections (Railway PostgreSQL)
- [ ] Verify external services (Stripe, S3)

### 4. Resolve

- [ ] Apply fix or rollback (see Rollback Procedure below)
- [ ] Verify resolution
- [ ] Monitor for recurrence via Sentry

### 5. Document

- [ ] Create incident report (template below)
- [ ] Update runbooks if needed
- [ ] Schedule post-mortem (P1/P2 only)

---

## Common Issues

### Database Connection Errors

```bash
# Check database status via Railway
railway connect postgres

# Verify connection pool via health endpoint
curl https://your-app.railway.app/health/ready | jq .checks.database

# Check active connections (in psql via Railway)
railway connect postgres
SELECT count(*) FROM pg_stat_activity;
```

### High Memory Usage

```bash
# Check container resources on Railway dashboard
# Railway → Project → Service → Metrics tab

# Restart if needed
railway restart

# Check Sentry for memory-related errors
```

### Payment Webhook Failures

1. Check Stripe dashboard for failed webhooks (https://dashboard.stripe.com/webhooks)
2. Retry from Stripe dashboard
3. Check Sentry for webhook endpoint errors

```bash
# Check for webhook errors in Railway logs
railway logs | grep -i stripe

# Or check Sentry for tagged errors
# Filter by: transaction = "/webhooks/stripe"
```

### Authentication Issues

```bash
# Check JWT secret is configured in Railway environment
# Railway → Project → Service → Variables tab
# Verify AUTH_JWT_SECRET_KEY is set

# If sessions are being invalidated on restart, the JWT secret
# may be auto-generated instead of persistent. See BUGS_LOG.md Bug #006.
```

### S3/Storage Issues

```bash
# Check S3 connectivity via health endpoint
curl https://your-app.railway.app/health/ready | jq .checks.s3

# Verify credentials are set in Railway environment variables
# S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_BUCKET_NAME
```

---

## Rollback Procedure

### Railway (Primary)

```bash
# List recent deployments on Railway dashboard
# Railway → Project → Service → Deployments tab

# Rollback to previous deployment via Railway dashboard
# Click on the previous successful deployment → "Redeploy"

# Or via Railway CLI
railway up --detach  # Re-deploy from current git state
```

### Git-based Rollback

```bash
# Find last good commit
git log --oneline -10

# Revert to previous commit (creates new commit — preferred)
git revert <commit-hash>
git push origin develop

# Or force checkout (destructive — use only if necessary)
git reset --hard <commit-hash>
git push origin develop --force

# Railway will auto-deploy from the develop branch
```

> **Branch Note:** Production deploys from `develop` (v0.9.4-alpha).
> The `main` branch needs a merge from `develop` and is currently behind.

---

## Contacts

| Role | Contact |
|------|---------|
| Primary On-Call | Xerxes (Union Business Rep / Developer) |
| Stripe Support | https://support.stripe.com |
| Railway Support | https://railway.app/help |
| Sentry Support | https://sentry.io/support |

---

## Post-Incident Template

```markdown
# Incident Report: [Title]

**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P1/P2/P3/P4
**Affected:** [Systems/Users affected]

## Summary
[Brief description of what happened]

## Timeline
- HH:MM — Incident detected
- HH:MM — Investigation started
- HH:MM — Root cause identified
- HH:MM — Fix deployed
- HH:MM — Verified resolved

## Root Cause
[What caused the issue]

## Resolution
[How it was fixed]

## Action Items
- [ ] [Preventive measures]
- [ ] [Process improvements]
- [ ] [Documentation updates]

## Lessons Learned
[What we learned from this incident]
```

---

## Cross-References

| Document | Location |
|----------|----------|
| Deployment Runbook | `/docs/runbooks/deployment.md` |
| Backup & Restore Runbook | `/docs/runbooks/backup-restore.md` |
| Disaster Recovery Runbook | `/docs/runbooks/disaster-recovery.md` |
| Audit Maintenance Runbook | `/docs/runbooks/audit-maintenance.md` |
| ADR-007: Monitoring Strategy (Sentry) | `/docs/decisions/ADR-007-monitoring-strategy.md` |
| BUGS_LOG | `/docs/BUGS_LOG.md` |

---

## 📄 End-of-Session Documentation (MANDATORY)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture
> progress made this session. Scan `/docs/*` and make or create any relevant
> updates/documents to keep a historical record as the project progresses.
> Do not forget about ADRs — update as necessary.

---

*Document Version: 1.1*
*Last Updated: February 3, 2026*
