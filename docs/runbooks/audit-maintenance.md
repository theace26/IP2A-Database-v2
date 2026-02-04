# Audit Log Maintenance Runbook

> **Document Created:** February 3, 2026
> **Last Updated:** February 3, 2026
> **Version:** 1.0
> **Status:** Active
> **Project Version:** v0.9.4-alpha

---

## Overview

This runbook covers maintenance procedures for the IP2A audit logging system, which is designed for NLRA 7-year compliance. The audit system consists of:

1. **PostgreSQL `audit_logs` table** — Immutable business audit trail
2. **Immutability triggers** — Prevent UPDATE/DELETE operations
3. **Role-based access** — Field-level redaction for sensitive data
4. **Archive process** — Glacier archival for older records

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| [ADR-012: Audit Logging](../decisions/ADR-012-audit-logging.md) | Architecture decision |
| [Audit Architecture](../architecture/AUDIT_ARCHITECTURE.md) | System design |
| [scripts/archive_audit_logs.sh](../../scripts/archive_audit_logs.sh) | Archival script |
| [Backup & Restore Runbook](backup-restore.md) | Database backup procedures |

---

## Scheduled Tasks

### Daily

| Time | Task | Script | Notes |
|------|------|--------|-------|
| 02:00 | Verify audit log integrity | `scripts/verify_audit_integrity.sh` | Check immutability trigger is active |

### Monthly

| Day | Task | Script | Notes |
|-----|------|--------|-------|
| 1st | Archive audit logs > 3 years old | `scripts/archive_audit_logs.sh` | Moves to S3 Glacier |
| 1st | Generate audit statistics report | Manual query | Track growth trends |

### Annually

| Task | Timeline | Notes |
|------|----------|-------|
| Review retention policy | Q1 | Ensure 7-year NLRA compliance |
| Test restore from archive | Q2 | Verify archived logs are recoverable |
| Capacity planning | Q4 | Project storage needs for next year |

---

## Procedures

### 1. Verify Immutability Trigger

**Purpose:** Ensure audit logs cannot be modified or deleted.

```bash
# Run verification script
./scripts/verify_audit_integrity.sh

# Or manually test trigger
psql -d ip2a_production -c "
  UPDATE audit_logs SET action = 'TEST' WHERE id = 1;
"
# Should fail with: "Audit log records cannot be modified"
```

**Expected Output:**
```
ERROR: Audit log records cannot be modified
CONTEXT: PL/pgSQL function prevent_audit_modification() line 3 at RAISE
```

### 2. Archive Old Audit Logs

**Purpose:** Move logs older than 3 years to S3 Glacier for cost-effective long-term storage.

```bash
# Set retention date (3 years ago)
export ARCHIVE_BEFORE=$(date -d "3 years ago" +%Y-%m-%d)

# Run archive script
./scripts/archive_audit_logs.sh

# Verify archive was created
aws s3 ls s3://ip2a-audit-archive/
```

**Archive Format:**
```
s3://ip2a-audit-archive/
├── 2023/
│   ├── audit_logs_2023_Q1.csv.gz
│   ├── audit_logs_2023_Q2.csv.gz
│   ├── audit_logs_2023_Q3.csv.gz
│   └── audit_logs_2023_Q4.csv.gz
└── manifests/
    └── archive_manifest_2023.json
```

### 3. Restore Archived Logs

**Purpose:** Retrieve archived logs for compliance audits or investigations.

```bash
# Request restore from Glacier (takes 3-5 hours for standard retrieval)
aws s3api restore-object \
  --bucket ip2a-audit-archive \
  --key 2023/audit_logs_2023_Q1.csv.gz \
  --restore-request '{"Days":7,"GlacierJobParameters":{"Tier":"Standard"}}'

# Check restore status
aws s3api head-object \
  --bucket ip2a-audit-archive \
  --key 2023/audit_logs_2023_Q1.csv.gz

# Download once available
aws s3 cp s3://ip2a-audit-archive/2023/audit_logs_2023_Q1.csv.gz ./
gunzip audit_logs_2023_Q1.csv.gz

# Import to temporary table for querying
psql -d ip2a_production -c "
  CREATE TEMP TABLE archived_audit_logs (LIKE audit_logs);
  COPY archived_audit_logs FROM '/path/to/audit_logs_2023_Q1.csv' CSV HEADER;
"
```

### 4. Export Audit Logs for Compliance

**Purpose:** Generate audit exports for legal/compliance review.

```bash
# Export specific date range
psql -d ip2a_production -c "
  COPY (
    SELECT
      id, table_name, record_id, action,
      user_id, created_at,
      -- Redact sensitive fields for non-admin export
      CASE WHEN table_name = 'users' AND old_values ? 'password_hash'
           THEN jsonb_set(old_values, '{password_hash}', '\"[REDACTED]\"')
           ELSE old_values
      END as old_values,
      CASE WHEN table_name = 'users' AND new_values ? 'password_hash'
           THEN jsonb_set(new_values, '{password_hash}', '\"[REDACTED]\"')
           ELSE new_values
      END as new_values
    FROM audit_logs
    WHERE created_at BETWEEN '2025-01-01' AND '2025-12-31'
    ORDER BY created_at
  ) TO '/tmp/audit_export_2025.csv' CSV HEADER;
"
```

### 5. Monitor Audit Log Growth

**Purpose:** Track storage usage and plan for capacity.

```sql
-- Current audit log size
SELECT
  pg_size_pretty(pg_total_relation_size('audit_logs')) as total_size,
  (SELECT count(*) FROM audit_logs) as total_records,
  (SELECT count(*) FROM audit_logs WHERE created_at > now() - interval '30 days') as last_30_days,
  (SELECT count(*) FROM audit_logs WHERE created_at > now() - interval '7 days') as last_7_days;

-- Growth by month
SELECT
  date_trunc('month', created_at) as month,
  count(*) as records,
  pg_size_pretty(sum(pg_column_size(row(audit_logs.*)))) as estimated_size
FROM audit_logs
GROUP BY 1
ORDER BY 1 DESC
LIMIT 12;

-- Most active tables
SELECT
  table_name,
  count(*) as total_records,
  count(*) FILTER (WHERE action = 'CREATE') as creates,
  count(*) FILTER (WHERE action = 'UPDATE') as updates,
  count(*) FILTER (WHERE action = 'DELETE') as deletes
FROM audit_logs
WHERE created_at > now() - interval '30 days'
GROUP BY 1
ORDER BY 2 DESC;
```

---

## Troubleshooting

### Trigger Not Preventing Modifications

**Symptom:** UPDATE/DELETE on audit_logs succeeds (should fail)

**Diagnosis:**
```sql
-- Check if trigger exists
SELECT tgname, tgenabled FROM pg_trigger
WHERE tgrelid = 'audit_logs'::regclass;

-- Check trigger function exists
SELECT proname FROM pg_proc
WHERE proname = 'prevent_audit_modification';
```

**Resolution:**
```sql
-- Recreate trigger
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'Audit log records cannot be modified';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_logs_immutable_update
  BEFORE UPDATE ON audit_logs
  FOR EACH ROW
  EXECUTE FUNCTION prevent_audit_modification();

CREATE TRIGGER audit_logs_immutable_delete
  BEFORE DELETE ON audit_logs
  FOR EACH ROW
  EXECUTE FUNCTION prevent_audit_modification();
```

### Archive Script Fails

**Symptom:** `archive_audit_logs.sh` exits with error

**Common Causes:**
1. AWS credentials not configured
2. S3 bucket doesn't exist
3. Insufficient disk space for temp files

**Resolution:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify bucket exists
aws s3 ls s3://ip2a-audit-archive/

# Check disk space
df -h /tmp

# Run with verbose logging
DEBUG=1 ./scripts/archive_audit_logs.sh
```

### Audit Logs Growing Too Fast

**Symptom:** Unexpected storage consumption

**Diagnosis:**
```sql
-- Find what's causing the growth
SELECT
  table_name,
  action,
  date_trunc('day', created_at) as day,
  count(*) as records
FROM audit_logs
WHERE created_at > now() - interval '7 days'
GROUP BY 1, 2, 3
ORDER BY 4 DESC
LIMIT 20;

-- Check for potential infinite loops or excessive logging
SELECT
  user_id,
  count(*) as records,
  count(DISTINCT session_id) as sessions
FROM audit_logs
WHERE created_at > now() - interval '1 day'
GROUP BY 1
ORDER BY 2 DESC
LIMIT 10;
```

---

## Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| Primary DBA / Developer | Xerxes | 4 hours |
| Compliance Officer | (Internal — IBEW Local 46) | Business hours |
| AWS Support | AWS Console | As needed |
| Railway Support | https://railway.app/help | As needed |

---

## Compliance Notes

### NLRA Requirements

- **Retention Period:** 7 years minimum for member-related records
- **Immutability:** Logs must not be modifiable after creation
- **Availability:** Must be retrievable within 30 days for legal proceedings
- **Access Control:** Role-based access with field-level redaction

### Audited Tables

The following tables require mandatory audit logging:

| Table | Requirement | Notes |
|-------|-------------|-------|
| `members` | All actions | Core member data |
| `member_notes` | All actions | Staff documentation |
| `member_employments` | All actions | Employment history |
| `students` | All actions | Training records |
| `users` | All actions | System accounts |
| `dues_payments` | All actions | Financial transactions |
| `grievances` | All actions | Labor relations |
| `benevolence_applications` | All actions | Financial assistance |
| `registrations` | All actions | Phase 7: Referral system |
| `dispatches` | All actions | Phase 7: Dispatch records |
| `check_marks` | All actions | Phase 7: Penalty tracking |

---

---

## Cross-References

| Document | Location |
|----------|----------|
| ADR-012: Audit Logging Strategy | `/docs/decisions/ADR-012-audit-logging-strategy.md` |
| Audit Architecture | `/docs/architecture/AUDIT_ARCHITECTURE.md` |
| Audit API Reference | `/docs/reference/audit-api.md` |
| Archive Script | `/scripts/archive_audit_logs.sh` |
| Backup & Restore Runbook | `/docs/runbooks/backup-restore.md` |
| Incident Response Runbook | `/docs/runbooks/incident-response.md` |

---

## 📄 End-of-Session Documentation (MANDATORY)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture
> progress made this session. Scan `/docs/*` and make or create any relevant
> updates/documents to keep a historical record as the project progresses.
> Do not forget about ADRs — update as necessary.

---

*Document Version: 1.1*
*Last Updated: February 3, 2026*
