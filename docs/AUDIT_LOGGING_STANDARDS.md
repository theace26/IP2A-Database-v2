# Audit Logging Industry Standards & Best Practices

## Overview

This document outlines industry standards for audit logging and provides recommendations for the IP2A Database v2 implementation.

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
| **GDPR** | Varies | 1-7 years |
| **PCI DSS** | 3 months (1 year recommended) | 1 year |
| **SOC 2** | 1 year | 3-7 years |
| **General Best Practice** | 2 years | 3-5 years |

**Recommendation for IP2A:**
- **Hot storage:** 1 year (active PostgreSQL table)
- **Warm storage:** 2-6 years (compressed/partitioned)
- **Cold storage:** 7+ years (S3/Glacier archive)
- **Delete after:** 7 years (unless legal hold)

---

## 3. Compression & Archiving Strategies

### Tier 1: Hot Storage (0-12 months)

**Storage:** PostgreSQL with current schema
**Compression:** JSONB native compression (~50-70% compression ratio)
**Access:** Real-time queries (<100ms)
**Cost:** High (SSD storage)

**Implementation:**
```sql
-- Current implementation (no changes needed)
SELECT * FROM audit_logs
WHERE changed_at > NOW() - INTERVAL '1 year';
```

### Tier 2: Warm Storage (1-3 years)

**Storage:** Partitioned PostgreSQL tables
**Compression:** Table-level compression + JSONB
**Access:** Fast queries (<1s)
**Cost:** Medium (standard disk)

**Implementation:**
```sql
-- Create monthly partitions
CREATE TABLE audit_logs_2026_01 PARTITION OF audit_logs
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE audit_logs_2026_02 PARTITION OF audit_logs
FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Enable compression on old partitions
ALTER TABLE audit_logs_2025_01 SET (
    toast_tuple_target = 128,
    fillfactor = 50
);
```

### Tier 3: Cold Storage (3-7 years)

**Storage:** S3 Standard or Glacier
**Compression:** gzip or zstd (~80-90% compression ratio)
**Access:** Slow (minutes to hours)
**Cost:** Very low

**Implementation:**
```python
# Monthly archival job
import gzip
import boto3
from datetime import datetime, timedelta

def archive_old_logs():
    """Archive logs older than 3 years to S3."""
    cutoff_date = datetime.now() - timedelta(days=3*365)

    # Export logs to JSON
    logs = db.query(AuditLog).filter(
        AuditLog.changed_at < cutoff_date
    ).all()

    # Compress and upload to S3
    s3 = boto3.client('s3')
    data = json.dumps([log.to_dict() for log in logs])
    compressed = gzip.compress(data.encode())

    filename = f"audit_logs_{cutoff_date.strftime('%Y-%m')}.json.gz"
    s3.put_object(
        Bucket='ip2a-audit-archive',
        Key=f'audit_logs/{filename}',
        Body=compressed,
        StorageClass='GLACIER'  # or 'GLACIER_IR' for faster retrieval
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
| **Per Record** | ~2 KB | ~1 KB | ~200-400 bytes | ~150-300 bytes |
| **100K records** | 200 MB | 100 MB | 20-40 MB | 15-30 MB |
| **1M records** | 2 GB | 1 GB | 200-400 MB | 150-300 MB |
| **10M records** | 20 GB | 10 GB | 2-4 GB | 1.5-3 GB |

**Compression Ratio Summary:**
- **JSONB (PostgreSQL native):** 50-70% compression
- **gzip:** 80-90% compression
- **zstd:** 85-92% compression (faster than gzip)

### Storage Cost Estimates (AWS US-East-1)

| Tier | Storage Type | Cost/GB/Month | 10M Records/Month | Annual Cost |
|------|--------------|---------------|-------------------|-------------|
| Hot | RDS PostgreSQL (SSD) | $0.115 | $1.15 | $13.80 |
| Warm | RDS PostgreSQL (gp3) | $0.08 | $0.80 | $9.60 |
| Cold | S3 Standard | $0.023 | $0.05 | $0.60 |
| Archive | S3 Glacier Deep | $0.00099 | $0.002 | $0.02 |

**Total 7-Year Cost for 10M records/month:**
- Hot (1 year): $13.80
- Warm (2 years): $19.20
- Cold (4 years): $2.40
- **Total: ~$35/year** (or $245 for 7 years)

---

## 5. Performance Optimization

### Indexes (Already Implemented ✅)

```sql
-- Primary indexes (from migration)
CREATE INDEX ix_audit_logs_table_name ON audit_logs(table_name);
CREATE INDEX ix_audit_logs_record_id ON audit_logs(record_id);

-- Additional recommended indexes
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

### Partitioning Strategy

**Recommended: Monthly partitions by `changed_at`**

```sql
-- Convert to partitioned table (requires downtime)
-- 1. Rename existing table
ALTER TABLE audit_logs RENAME TO audit_logs_old;

-- 2. Create partitioned table
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

-- 3. Create partitions for each month
CREATE TABLE audit_logs_2026_01 PARTITION OF audit_logs
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE audit_logs_2026_02 PARTITION OF audit_logs
FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
-- ... create 12-24 months ahead

-- 4. Migrate data
INSERT INTO audit_logs SELECT * FROM audit_logs_old;

-- 5. Drop old table (after verification)
DROP TABLE audit_logs_old;
```

**Benefits:**
- ✅ Fast queries on recent data (partition pruning)
- ✅ Easy to drop/archive old partitions
- ✅ Better compression on old partitions
- ✅ Parallel query execution across partitions

---

## 6. Security & Access Control

### Industry Standards

| Requirement | Implementation |
|-------------|----------------|
| **Immutability** | Revoke UPDATE/DELETE permissions |
| **Access Control** | Read-only for most users |
| **Encryption at Rest** | Enable PostgreSQL encryption |
| **Encryption in Transit** | Require SSL connections |
| **Audit the Auditors** | Log access to audit logs |
| **Tamper Detection** | Cryptographic signatures (optional) |

### Implementation

```sql
-- Revoke write permissions
REVOKE UPDATE, DELETE ON audit_logs FROM app_user;
GRANT INSERT, SELECT ON audit_logs TO app_user;

-- Create read-only audit viewer role
CREATE ROLE audit_viewer;
GRANT SELECT ON audit_logs TO audit_viewer;

-- Create audit admin role (for retention/archival)
CREATE ROLE audit_admin;
GRANT SELECT, DELETE ON audit_logs TO audit_admin;

-- Enable row-level security (optional - restrict by user)
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY audit_logs_view_own
ON audit_logs FOR SELECT
TO app_user
USING (changed_by = current_user);

-- Admins can see all
CREATE POLICY audit_logs_view_all
ON audit_logs FOR SELECT
TO audit_admin
USING (true);
```

---

## 7. Automated Retention & Archival

### Recommended Automation Strategy

```python
# /app/scripts/audit_maintenance.py
"""
Automated audit log maintenance job.

Run via cron:
0 2 * * * cd /app && python scripts/audit_maintenance.py
"""

import sys
sys.path.insert(0, '/app')

from datetime import datetime, timedelta
from sqlalchemy import text
from src.db.session import get_db
import gzip
import json
import boto3

def archive_old_logs(db, days_old=1095):  # 3 years
    """Archive logs older than N days to S3."""
    cutoff = datetime.now() - timedelta(days=days_old)

    # Query old logs
    result = db.execute(text("""
        SELECT * FROM audit_logs
        WHERE changed_at < :cutoff
        ORDER BY changed_at
    """), {"cutoff": cutoff})

    logs = result.fetchall()

    if not logs:
        print("No logs to archive")
        return

    # Export to JSON
    data = [dict(row) for row in logs]
    json_data = json.dumps(data, default=str)

    # Compress
    compressed = gzip.compress(json_data.encode())

    # Upload to S3
    s3 = boto3.client('s3')
    filename = f"audit_logs_{cutoff.strftime('%Y%m')}.json.gz"
    s3.put_object(
        Bucket='ip2a-audit-archive',
        Key=f'audit_logs/{filename}',
        Body=compressed,
        StorageClass='GLACIER_IR'
    )

    # Delete from PostgreSQL
    db.execute(text("""
        DELETE FROM audit_logs
        WHERE changed_at < :cutoff
    """), {"cutoff": cutoff})
    db.commit()

    print(f"Archived {len(logs)} logs to {filename}")

def delete_expired_logs(db, days_old=2555):  # 7 years
    """Delete logs older than 7 years (past retention period)."""
    cutoff = datetime.now() - timedelta(days=days_old)

    result = db.execute(text("""
        DELETE FROM audit_logs
        WHERE changed_at < :cutoff
        RETURNING id
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

    # Archive logs older than 3 years
    archive_old_logs(db, days_old=1095)

    # Delete logs older than 7 years
    delete_expired_logs(db, days_old=2555)

    # Cleanup
    vacuum_and_analyze(db)

    print("Audit maintenance complete")
```

### Cron Schedule

```bash
# /etc/cron.d/audit-maintenance

# Archive old logs daily at 2 AM
0 2 * * * app cd /app && python scripts/audit_maintenance.py >> /var/log/audit_maintenance.log 2>&1

# Verify backup integrity weekly
0 3 * * 0 app cd /app && python scripts/verify_audit_backups.py >> /var/log/audit_verify.log 2>&1
```

---

## 8. Monitoring & Alerting

### Key Metrics to Monitor

| Metric | Threshold | Alert Level |
|--------|-----------|-------------|
| **Table size** | > 100 GB | Warning |
| **Growth rate** | > 10 GB/day | Warning |
| **Query time** | > 5 seconds | Critical |
| **Failed archival** | Any failure | Critical |
| **Suspicious patterns** | > 1000 reads/hour by user | Warning |
| **Bulk deletes** | > 100 deletes/hour | Critical |

### Implementation

```python
# /app/scripts/audit_monitoring.py

def check_audit_health(db):
    """Check audit log health metrics."""

    # Table size
    result = db.execute(text("""
        SELECT pg_size_pretty(pg_total_relation_size('audit_logs')) as size,
               pg_total_relation_size('audit_logs') as size_bytes
    """))
    size_pretty, size_bytes = result.fetchone()

    if size_bytes > 100_000_000_000:  # 100 GB
        send_alert(f"Audit logs table is large: {size_pretty}")

    # Growth rate (logs in last 24 hours)
    result = db.execute(text("""
        SELECT COUNT(*) FROM audit_logs
        WHERE changed_at > NOW() - INTERVAL '24 hours'
    """))
    daily_count = result.scalar()

    if daily_count > 1_000_000:
        send_alert(f"High audit log volume: {daily_count:,} logs in 24h")

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
        send_alert(f"Suspicious read pattern: {user} made {count} reads in 1 hour")

def send_alert(message):
    """Send alert via email/Slack/webhook."""
    # Implement your alerting here
    print(f"ALERT: {message}")
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

### Optimization: JSONB GIN Indexes

```sql
-- Add GIN indexes for JSONB queries
CREATE INDEX idx_audit_logs_old_values_gin
ON audit_logs USING GIN (old_values);

CREATE INDEX idx_audit_logs_new_values_gin
ON audit_logs USING GIN (new_values);

-- Now this query is fast:
SELECT * FROM audit_logs
WHERE new_values @> '{"status": "ACTIVE"}';
```

---

## 10. Compliance Checklists

### SOC 2 Type II Requirements

- [x] Log all access to sensitive data (READ tracking)
- [x] Log all modifications (CREATE, UPDATE, DELETE)
- [x] Immutable logs (no updates/deletes)
- [x] Retention for 1+ years
- [ ] Annual attestation report
- [ ] Log review procedures documented

### GDPR Requirements

- [x] Right to access (query audit logs for data subject)
- [x] Right to erasure (archive then delete)
- [x] Data breach notification (monitor for suspicious access)
- [ ] Data processing agreement with cloud provider
- [ ] Privacy impact assessment

### HIPAA Requirements

- [x] Log all PHI access
- [x] Audit trail for 6+ years
- [x] Automatic log-off (not applicable to API)
- [ ] Annual security risk assessment
- [ ] Business associate agreements

---

## 11. Disaster Recovery

### Backup Strategy

| Frequency | Scope | Retention |
|-----------|-------|-----------|
| **Real-time** | WAL archiving to S3 | 7 days |
| **Daily** | Full PostgreSQL backup | 30 days |
| **Weekly** | Audit log archive to S3 | 7 years |
| **Monthly** | Cold storage snapshot | Permanent |

### Recovery Procedures

```bash
# Restore audit logs from S3 archive
aws s3 cp s3://ip2a-audit-archive/audit_logs/2026_01.json.gz .
gunzip 2026_01.json.gz

# Import back to PostgreSQL
psql -d ip2a -c "COPY audit_logs FROM '/tmp/2026_01.json' WITH (FORMAT csv)"
```

---

## 12. Recommended Implementation Timeline

### Phase 1: Foundation (Done ✅)
- [x] Audit log table created
- [x] Basic indexing
- [x] Middleware for context capture
- [x] Audit service functions

### Phase 2: Optimization (2-4 weeks)
- [ ] Add recommended indexes (GIN for JSONB)
- [ ] Implement table partitioning
- [ ] Set up S3 bucket for archives
- [ ] Create maintenance scripts

### Phase 3: Automation (1 month)
- [ ] Automated archival cron job
- [ ] Monitoring and alerting
- [ ] Dashboard for audit log viewing
- [ ] Retention policy enforcement

### Phase 4: Compliance (Ongoing)
- [ ] Document retention policies
- [ ] Implement access controls
- [ ] Annual audit trail review
- [ ] Compliance attestation

---

## References

- **NIST SP 800-92:** Guide to Computer Security Log Management
- **ISO 27001:** Information Security Management
- **PCI DSS 3.2.1:** Requirement 10 (Track and monitor all access)
- **GDPR Article 30:** Records of processing activities
- **SOC 2:** Trust Services Criteria (Security)

---

**Last Updated:** 2026-01-27
**Version:** 1.0
**Owner:** IP2A Database Team
