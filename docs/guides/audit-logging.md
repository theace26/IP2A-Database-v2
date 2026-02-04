# Audit Logging Industry Standards & Best Practices

> **Document Created:** January 27, 2026
> **Last Updated:** February 3, 2026
> **Version:** 1.1
> **Status:** Active — Reference Guide
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)

---

## Overview

This document outlines industry standards for audit logging and provides recommendations for the IP2A Database v2 (UnionCore) implementation. The audit logging foundation is fully implemented ([ADR-012](../decisions/ADR-012-audit-logging.md)); this guide covers best practices for retention, compression, archiving, and compliance as the system scales.

### Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Audit log table + schema | ✅ Complete | Full 5 W's coverage |
| Basic indexing | ✅ Complete | Table name, record ID indexes |
| Middleware for context capture | ✅ Complete | IP address, user-agent, session info |
| Audit service functions | ✅ Complete | CREATE, READ, UPDATE, DELETE tracking |
| Sentry integration | ✅ Complete | Error tracking + performance ([ADR-007](../decisions/ADR-007-monitoring-strategy.md)) |
| GIN indexes for JSONB | 🔜 Future | Add when query volume warrants it |
| Table partitioning | 🔜 Future | Add when table exceeds ~10M rows |
| S3 archival pipeline | 🔜 Future | Add when retention window requires it |
| Automated retention enforcement | 🔜 Future | Add alongside archival pipeline |

---

## 1. What to Log (The "5 W's")

### Industry Standard: The "5 W's" of Audit Logging

| Element | Description | Our Implementation |
|---------|-------------|-------------------|
| **Who** | User/system performing action | ✅ `changed_by` field |
| **What** | Action performed + data changed | ✅ `action`, `old_values`, `new_values`, `changed_fields` |
| **When** | Timestamp of action | ✅ `changed_at` with server-side timestamp |
| **Where** | Source IP address | ✅ `ip_address` field |
| **Why** | Business reason/context | ✅ `notes` field (optional) |

**Additional Best Practices:**

- ✅ User-Agent (device/browser identification)
- ✅ Table and record identification
- ✅ Full before/after state for compliance

---

## 2. Retention Periods

### Industry Standards by Compliance Framework

| Framework | Minimum Retention | Typical Retention |
|-----------|-------------------|-------------------|
| **SOX (Sarbanes-Oxley)** | 7 years | 7 years |
| **HIPAA** | 6 years | 6 years |
| **GDPR** | Varies | 1–7 years |
| **PCI DSS** | 3 months (1 year recommended) | 1 year |
| **SOC 2** | 1 year | 3–7 years |
| **NLRA (Union Records)** | 7 years | 7 years |
| **General Best Practice** | 2 years | 3–5 years |

**Recommendation for UnionCore:**

- **Hot storage:** 1 year (active PostgreSQL table on Railway)
- **Warm storage:** 2–6 years (compressed/partitioned)
- **Cold storage:** 7+ years (S3/Glacier archive)
- **Delete after:** 7 years (unless legal hold — NLRA compliance)

---

## 3. Compression & Archiving Strategies

### Tier 1: Hot Storage (0–12 months)

**Storage:** PostgreSQL on Railway (current deployment)
**Compression:** JSONB native compression (~50–70% compression ratio)
**Access:** Real-time queries (<100ms)
**Cost:** Included in Railway plan

```sql
-- Current implementation (no changes needed)
SELECT * FROM audit_logs
WHERE changed_at > NOW() - INTERVAL '1 year';
```

### Tier 2: Warm Storage (1–3 years)

**Storage:** Partitioned PostgreSQL tables
**Compression:** Table-level compression + JSONB
**Access:** Fast queries (<1s)

```sql
-- Create monthly partitions (implement when table exceeds ~10M rows)
CREATE TABLE audit_logs_2026_01 PARTITION OF audit_logs
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE audit_logs_2026_02 PARTITION OF audit_logs
FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
```

### Tier 3: Cold Storage (3–7 years)

**Storage:** S3 Standard or Glacier
**Compression:** gzip or zstd (~80–90% compression ratio)
**Access:** Slow (minutes to hours)

```python
# Monthly archival job (implement when retention window requires it)
import gzip
import boto3
from datetime import datetime, timedelta

def archive_old_logs():
    """Archive logs older than 3 years to S3."""
    cutoff_date = datetime.now() - timedelta(days=3*365)

    logs = db.query(AuditLog).filter(
        AuditLog.changed_at < cutoff_date
    ).all()

    s3 = boto3.client('s3')
    data = json.dumps([log.to_dict() for log in logs])
    compressed = gzip.compress(data.encode())

    filename = f"audit_logs_{cutoff_date.strftime('%Y-%m')}.json.gz"
    s3.put_object(
        Bucket='ip2a-audit-archive',
        Key=f'audit_logs/{filename}',
        Body=compressed,
        StorageClass='GLACIER'
    )

    # Delete from PostgreSQL after successful upload
    db.query(AuditLog).filter(
        AuditLog.changed_at < cutoff_date
    ).delete()
    db.commit()
```

---

## 4. Compression Ratios & Storage Estimates

### Typical Audit Log Sizes

| Component | Uncompressed | JSONB | gzip | zstd |
|-----------|--------------|-------|------|------|
| **Per Record** | ~2 KB | ~1 KB | ~200–400 bytes | ~150–300 bytes |
| **100K records** | 200 MB | 100 MB | 20–40 MB | 15–30 MB |
| **1M records** | 2 GB | 1 GB | 200–400 MB | 150–300 MB |
| **10M records** | 20 GB | 10 GB | 2–4 GB | 1.5–3 GB |

**Compression Ratio Summary:**

- **JSONB (PostgreSQL native):** 50–70% compression
- **gzip:** 80–90% compression
- **zstd:** 85–92% compression (faster than gzip)

### Storage Cost Estimates (AWS US-East-1, for reference)

| Tier | Storage Type | Cost/GB/Month | 10M Records/Month | Annual Cost |
|------|--------------|---------------|-------------------|-------------|
| Hot | RDS PostgreSQL (SSD) | $0.115 | $1.15 | $13.80 |
| Warm | RDS PostgreSQL (gp3) | $0.08 | $0.80 | $9.60 |
| Cold | S3 Standard | $0.023 | $0.05 | $0.60 |
| Archive | S3 Glacier Deep | $0.00099 | $0.002 | $0.02 |

> **Note:** UnionCore currently deploys on Railway, not AWS. These estimates are for reference if/when a tiered archival strategy is implemented. Railway PostgreSQL costs are bundled into the plan.

---

## 5. Performance Optimization

### Indexes (Current Implementation ✅)

```sql
-- Primary indexes (from migration — already deployed)
CREATE INDEX ix_audit_logs_table_name ON audit_logs(table_name);
CREATE INDEX ix_audit_logs_record_id ON audit_logs(record_id);
```

### Recommended Future Indexes

```sql
-- Add when query patterns warrant (monitor via Sentry performance)
CREATE INDEX idx_audit_logs_changed_at_desc
ON audit_logs(changed_at DESC);

CREATE INDEX idx_audit_logs_changed_by
ON audit_logs(changed_by)
WHERE changed_by != 'anonymous';

CREATE INDEX idx_audit_logs_action
ON audit_logs(action);

-- Composite indexes for common queries
CREATE INDEX idx_audit_logs_table_record
ON audit_logs(table_name, record_id, changed_at DESC);

CREATE INDEX idx_audit_logs_user_date
ON audit_logs(changed_by, changed_at DESC);
```

### Partitioning Strategy (Future)

**Recommended: Monthly partitions by `changed_at`** — implement when table exceeds ~10M rows.

```sql
-- Convert to partitioned table (requires maintenance window)
CREATE TABLE audit_logs (
    id SERIAL,
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(50) NOT NULL,
    action VARCHAR(10) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    changed_fields JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    notes TEXT,
    PRIMARY KEY (id, changed_at)
) PARTITION BY RANGE (changed_at);
```

**Benefits:** Fast queries on recent data (partition pruning), easy to drop/archive old partitions, better compression on old partitions, parallel query execution.

---

## 6. Security & Access Control

### Industry Standards

| Requirement | Implementation |
|-------------|----------------|
| **Immutability** | Revoke UPDATE/DELETE permissions |
| **Access Control** | Read-only for most users (RBAC enforced) |
| **Encryption at Rest** | Railway PostgreSQL encryption |
| **Encryption in Transit** | SSL connections (Railway default) |
| **Audit the Auditors** | Log access to audit logs |
| **Tamper Detection** | Cryptographic signatures (optional, future) |

### Implementation

```sql
-- Revoke write permissions on production
REVOKE UPDATE, DELETE ON audit_logs FROM app_user;
GRANT INSERT, SELECT ON audit_logs TO app_user;

-- Read-only audit viewer role
CREATE ROLE audit_viewer;
GRANT SELECT ON audit_logs TO audit_viewer;

-- Audit admin role (for retention/archival)
CREATE ROLE audit_admin;
GRANT SELECT, DELETE ON audit_logs TO audit_admin;
```

---

## 7. Automated Retention & Archival (Future)

### Recommended Automation Strategy

```python
# /scripts/audit_maintenance.py
"""
Automated audit log maintenance job.
Implement when archival pipeline is needed.

Run via cron or Railway scheduled job:
0 2 * * * cd /app && python scripts/audit_maintenance.py
"""

from datetime import datetime, timedelta
from sqlalchemy import text
from src.db.session import get_db
import gzip
import json
import boto3

def archive_old_logs(db, days_old=1095):  # 3 years
    """Archive logs older than N days to S3."""
    cutoff = datetime.now() - timedelta(days=days_old)

    result = db.execute(text("""
        SELECT * FROM audit_logs
        WHERE changed_at < :cutoff
        ORDER BY changed_at
    """), {"cutoff": cutoff})

    logs = result.fetchall()
    if not logs:
        print("No logs to archive")
        return

    data = [dict(row) for row in logs]
    json_data = json.dumps(data, default=str)
    compressed = gzip.compress(json_data.encode())

    s3 = boto3.client('s3')
    filename = f"audit_logs_{cutoff.strftime('%Y%m')}.json.gz"
    s3.put_object(
        Bucket='ip2a-audit-archive',
        Key=f'audit_logs/{filename}',
        Body=compressed,
        StorageClass='GLACIER_IR'
    )

    db.execute(text("""
        DELETE FROM audit_logs WHERE changed_at < :cutoff
    """), {"cutoff": cutoff})
    db.commit()
    print(f"Archived {len(logs)} logs to {filename}")

def delete_expired_logs(db, days_old=2555):  # 7 years (NLRA compliance)
    """Delete logs older than 7 years (past retention period)."""
    cutoff = datetime.now() - timedelta(days=days_old)
    result = db.execute(text("""
        DELETE FROM audit_logs WHERE changed_at < :cutoff RETURNING id
    """), {"cutoff": cutoff})
    deleted = result.rowcount
    db.commit()
    print(f"Deleted {deleted} expired logs (older than 7 years)")

def vacuum_and_analyze(db):
    """Reclaim space and update statistics."""
    db.execute(text("VACUUM ANALYZE audit_logs"))
    print("Vacuumed and analyzed audit_logs table")

if __name__ == "__main__":
    db = next(get_db())
    print(f"Running audit maintenance at {datetime.now()}")
    archive_old_logs(db, days_old=1095)
    delete_expired_logs(db, days_old=2555)
    vacuum_and_analyze(db)
    print("Audit maintenance complete")
```

---

## 8. Monitoring & Alerting

> **Current monitoring:** Sentry ([ADR-007](../decisions/ADR-007-monitoring-strategy.md)) handles error tracking and performance monitoring. The metrics below describe future enhancements for audit-specific alerting.

### Key Metrics to Monitor

| Metric | Threshold | Alert Level |
|--------|-----------|-------------|
| **Table size** | > 100 GB | Warning |
| **Growth rate** | > 10 GB/day | Warning |
| **Query time** | > 5 seconds | Critical |
| **Failed archival** | Any failure | Critical |
| **Suspicious patterns** | > 1000 reads/hour by user | Warning |
| **Bulk deletes** | > 100 deletes/hour | Critical |

### Implementation (Future Enhancement)

```python
def check_audit_health(db):
    """Check audit log health metrics. Report to Sentry if thresholds exceeded."""

    # Table size
    result = db.execute(text("""
        SELECT pg_size_pretty(pg_total_relation_size('audit_logs')) as size,
               pg_total_relation_size('audit_logs') as size_bytes
    """))
    size_pretty, size_bytes = result.fetchone()

    if size_bytes > 100_000_000_000:  # 100 GB
        sentry_sdk.capture_message(f"Audit logs table is large: {size_pretty}")

    # Growth rate (logs in last 24 hours)
    result = db.execute(text("""
        SELECT COUNT(*) FROM audit_logs
        WHERE changed_at > NOW() - INTERVAL '24 hours'
    """))
    daily_count = result.scalar()

    if daily_count > 1_000_000:
        sentry_sdk.capture_message(f"High audit log volume: {daily_count:,} logs in 24h")

    # Suspicious read patterns
    result = db.execute(text("""
        SELECT changed_by, COUNT(*) as read_count
        FROM audit_logs
        WHERE action = 'READ'
          AND changed_at > NOW() - INTERVAL '1 hour'
        GROUP BY changed_by
        HAVING COUNT(*) > 1000
    """))

    for user, count in result:
        sentry_sdk.capture_message(
            f"Suspicious read pattern: {user} made {count} reads in 1 hour"
        )
```

---

## 9. Query Performance Best Practices

### Fast Queries

```sql
-- ✅ GOOD: Uses indexes
SELECT * FROM audit_logs
WHERE table_name = 'members'
  AND record_id = '123'
  AND changed_at > NOW() - INTERVAL '30 days'
ORDER BY changed_at DESC
LIMIT 100;

-- ✅ GOOD: Uses partition pruning (if partitioned)
SELECT * FROM audit_logs
WHERE changed_at BETWEEN '2026-01-01' AND '2026-01-31'
  AND changed_by = 'user@example.com';

-- ✅ GOOD: Counts with filters
SELECT COUNT(*) FROM audit_logs
WHERE changed_at > NOW() - INTERVAL '7 days';
```

### Slow Queries (Avoid)

```sql
-- ❌ BAD: Full table scan
SELECT * FROM audit_logs
WHERE notes LIKE '%keyword%';

-- ❌ BAD: Unfiltered count
SELECT COUNT(*) FROM audit_logs;  -- Scans entire table

-- ❌ BAD: JSONB queries without indexes
SELECT * FROM audit_logs
WHERE new_values->>'status' = 'ACTIVE';  -- Slow without GIN index
```

### Optimization: JSONB GIN Indexes (Future)

```sql
-- Add when JSONB query patterns emerge
CREATE INDEX idx_audit_logs_old_values_gin ON audit_logs USING GIN (old_values);
CREATE INDEX idx_audit_logs_new_values_gin ON audit_logs USING GIN (new_values);

-- Then this query becomes fast:
SELECT * FROM audit_logs
WHERE new_values @> '{"status": "ACTIVE"}';
```

---

## 10. Compliance Checklists

### NLRA / Union Record Requirements (Primary)

- [x] Log all access to member records (READ tracking)
- [x] Log all modifications (CREATE, UPDATE, DELETE)
- [x] Immutable logs (application-level enforcement)
- [x] 7-year retention capability (schema supports archival)
- [ ] Automated 7-year retention enforcement (future)
- [ ] Annual audit trail review procedures

### SOC 2 Type II Requirements

- [x] Log all access to sensitive data (READ tracking)
- [x] Log all modifications (CREATE, UPDATE, DELETE)
- [x] Immutable logs (no updates/deletes at app level)
- [x] Retention for 1+ years
- [ ] Annual attestation report
- [ ] Log review procedures documented

### GDPR Requirements

- [x] Right to access (query audit logs for data subject)
- [x] Right to erasure (archive then delete)
- [x] Data breach notification (Sentry monitors for anomalies)
- [ ] Data processing agreement with cloud provider
- [ ] Privacy impact assessment

---

## 11. Disaster Recovery

### Backup Strategy

| Frequency | Scope | Retention | Notes |
|-----------|-------|-----------|-------|
| **Continuous** | Railway PostgreSQL backups | Per plan | Automatic |
| **Daily** | Full database backup | 30 days | Railway managed |
| **Weekly** | Audit log archive to S3 | 7 years | Future implementation |
| **Monthly** | Cold storage snapshot | Permanent | Future implementation |

### Recovery Procedures

```bash
# Railway provides point-in-time recovery for PostgreSQL
# For S3 archives (when implemented):
aws s3 cp s3://ip2a-audit-archive/audit_logs/2026_01.json.gz .
gunzip 2026_01.json.gz
# Import back to PostgreSQL via application import script
```

---

## 12. Implementation Timeline

### Phase 1: Foundation — ✅ Complete

- [x] Audit log table created
- [x] Basic indexing (table_name, record_id)
- [x] Middleware for context capture (IP, user-agent, session)
- [x] Audit service functions (all CRUD operations)
- [x] Sentry integration for monitoring ([ADR-007](../decisions/ADR-007-monitoring-strategy.md))

### Phase 2: Optimization — 🔜 When Needed

- [ ] Add recommended indexes (composite, GIN for JSONB)
- [ ] Implement table partitioning (when > ~10M rows)
- [ ] Set up S3 bucket for archives
- [ ] Create maintenance scripts

### Phase 3: Automation — 🔜 When Needed

- [ ] Automated archival (Railway scheduled job or cron)
- [ ] Audit-specific alerting via Sentry
- [ ] Dashboard for audit log viewing (may be part of admin UI)
- [ ] Retention policy enforcement

### Phase 4: Compliance — 🔜 Ongoing

- [ ] Document retention policies formally
- [ ] Implement database-level access controls
- [ ] Annual audit trail review process
- [ ] NLRA compliance attestation

---

## References

- **NIST SP 800-92:** Guide to Computer Security Log Management
- **ISO 27001:** Information Security Management
- **PCI DSS 3.2.1:** Requirement 10 (Track and monitor all access)
- **GDPR Article 30:** Records of processing activities
- **SOC 2:** Trust Services Criteria (Security)
- **NLRA:** National Labor Relations Act (7-year record retention)

---

> **End-of-Session Rule:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

---

| Cross-Reference | Location |
|----------------|----------|
| ADR-007: Monitoring Strategy (Sentry) | `/docs/decisions/ADR-007-monitoring-strategy.md` |
| ADR-012: Audit Logging | `/docs/decisions/ADR-012-audit-logging.md` |
| Coding Standards | `/docs/standards/coding-standards.md` |
| End-of-Session Documentation | `/docs/guides/END_OF_SESSION_DOCUMENTATION.md` |

---

*Document Version: 1.1*
*Last Updated: February 3, 2026*
