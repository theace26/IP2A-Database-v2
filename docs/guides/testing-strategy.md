# Testing Strategy — Stress Test vs Load Test

> **Document Created:** January 27, 2026
> **Last Updated:** February 3, 2026
> **Version:** 1.1
> **Status:** Active — Reference Guide
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)

---

## Overview

UnionCore has a multi-layered testing strategy:

1. **Unit/Integration Tests** — ~470 pytest tests covering models, services, routes, and workflows
2. **Stress Test** ([stress-testing.md](../reference/stress-testing.md)) — Tests database with LARGE DATA VOLUMES
3. **Load Test** ([load-testing.md](../reference/load-testing.md)) — Tests database with CONCURRENT USERS

All three layers are essential for production readiness.

### Current Test Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **pytest tests** | ~470 | Covering 26 models, ~150 endpoints |
| **Stress test data** | 515K+ records | 10.5 min, 818 records/sec |
| **Load test baseline** | 50 concurrent users | Validated |
| **Test framework** | pytest | With coverage reporting |

---

## Unit & Integration Tests (pytest)

Run the full test suite:

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific module tests
pytest src/tests/test_dues.py -v
pytest src/tests/test_members.py -v

# Run with keyword filter
pytest -k "test_create" -v
```

Test files follow the pattern `src/tests/test_{module}.py` and use the Arrange-Act-Assert structure. See [Coding Standards](../standards/coding-standards.md) for test naming conventions.

---

## Stress Test (Data Volume)

**Purpose:** Test database performance with large-scale realistic data

**What it does:**

- Populates database with massive datasets
- 10,000 members, 250,000 employments, 150,000 file attachments
- Tests: query performance, indexing, storage, data integrity

**When to run:**

- Before deploying to production
- After major schema changes
- To validate query performance
- To test data migration scripts

**Command:**

```bash
python run_stress_test.py
```

**Duration:** 15–45 minutes

**Result:** Database filled with large-scale test data

---

## Load Test (Concurrent Users)

**Purpose:** Test database performance under concurrent user load

**What it does:**

- Simulates 10–500 concurrent users
- Realistic read/write operations
- Tests: throughput, response times, connection pooling

**When to run:**

- Before deploying to production
- After performance optimizations
- To validate scalability
- Weekly performance monitoring

**Command:**

```bash
python run_load_test.py
```

**Duration:** 5–30 minutes

**Result:** Performance metrics and capacity estimates

---

## Combined Testing Strategy

### Phase 1: Data Volume Testing

```bash
# Step 1: Seed stress test data
python run_stress_test.py

# Step 2: Run integrity check
python run_integrity_check.py

# Step 3: Verify data quality
# - Check record counts
# - Validate relationships
# - Test complex queries
```

**Expected Time:** 1 hour

**Validates:** Database can store large datasets, queries perform well on large tables, indexes are effective, storage capacity is sufficient.

### Phase 2: Concurrent Load Testing

```bash
# Step 1: Baseline test (10 users)
python run_load_test.py --quick

# Step 2: Standard test (50 users)
python run_load_test.py

# Step 3: Stress test (200 users)
python run_load_test.py --stress

# Step 4: Compare results
# - Response times
# - Throughput
# - Success rates
```

**Expected Time:** 1 hour

**Validates:** Database handles concurrent operations, connection pool is sized correctly, no deadlocks or race conditions, system scales to target user count.

### Phase 3: Combined Testing (Realistic)

```bash
# Step 1: Start with stress test data
python run_stress_test.py

# Step 2: Run load test on large dataset
python run_load_test.py --users 100 --ops 100

# Step 3: Monitor performance via Sentry
# - Database CPU/memory
# - Query execution times
# - Connection pool usage
```

**Expected Time:** 1.5 hours

**Validates:** System performs well with both large data volumes and many concurrent users — production-ready performance.

---

## Testing Matrix

| Scenario | Data Volume | Concurrent Users | Test Type | Command |
|----------|-------------|------------------|-----------|---------|
| **Development** | Small (500 records) | Low (1–5) | Unit tests | `pytest` |
| **Integration** | Medium (5k records) | Medium (10–20) | API tests | `pytest src/tests/` |
| **Performance** | Large (100k+ records) | N/A | Stress test | `run_stress_test.py` |
| **Load** | Any | High (50–200) | Load test | `run_load_test.py` |
| **Production Sim** | Large (100k+ records) | High (100–500) | Combined | Both |

---

## Performance Goals

### For ~40 Staff + ~4,000 Members (Current User Base)

**Database Requirements:**

| Metric | Target | Notes |
|--------|--------|-------|
| **Data Volume** | 50k+ records | Stress test validates |
| **Concurrent Users** | 40–100 | Load test validates |
| **Avg Response Time** | < 500ms | Under load |
| **95th Percentile** | < 1000ms | Under load |
| **Throughput** | > 200 ops/sec | Per app server |
| **Success Rate** | > 99.9% | Critical operations |
| **Connection Pool** | 50–100 | Per app server |

### Scaling Path (Future Growth)

| Component | Current (Railway) | Scaled | Optimal |
|-----------|-------------------|--------|---------|
| **App Servers** | 1 (Railway) | 2–4 | 10+ |
| **Database CPU** | Railway managed | 4–8 cores | 16+ cores |
| **Database RAM** | Railway managed | 8–16 GB | 32+ GB |
| **Database** | 1 primary | 1 primary + replicas | Sharded |
| **Connection Pool** | Default | 100/server | 200/server |
| **Caching** | None | Redis (2 GB) | Redis cluster |

> **Note:** UnionCore deploys on Railway. Scaling is handled through Railway's infrastructure. Monitor via Sentry ([ADR-007](../decisions/ADR-007-monitoring-strategy.md)) and scale when metrics indicate the need.

---

## Pre-Production Checklist

### Data Validation

- [x] Run stress test to populate database
- [x] Run integrity check (no critical issues)
- [x] Verify all indexes exist
- [x] Test complex queries perform well (< 100ms)
- [x] Validate data relationships

### Performance Validation

- [x] Run load test with 50 users (baseline)
- [ ] Run load test with 100 users (target)
- [ ] Run load test with 200 users (stress)
- [x] Avg response time < 500ms
- [x] Success rate > 99%

### Monitoring Setup

- [x] Sentry error tracking configured ([ADR-007](../decisions/ADR-007-monitoring-strategy.md))
- [x] Sentry performance monitoring enabled
- [ ] Slow query logging enabled (PostgreSQL level)
- [ ] Connection pool monitoring
- [ ] Response time tracking dashboards

---

## Optimization Workflow

### Step 1: Identify Bottleneck

```bash
# Run combined test
python run_stress_test.py
python run_load_test.py --users 100

# Check results
# - Slow queries? → Check Sentry performance traces
# - Connection pool exhausted?
# - High failure rate?
```

### Step 2: Implement Fix

**If slow queries:**

```sql
-- Add indexes
CREATE INDEX idx_members_status ON members(status);
CREATE INDEX idx_employments_member_current ON member_employments(member_id, is_current);

-- Analyze query plans
EXPLAIN ANALYZE SELECT ...;
```

**If connection pool issues:**

```python
# Increase pool size (src/db/session.py)
SQLALCHEMY_POOL_SIZE = 60
SQLALCHEMY_MAX_OVERFLOW = 100
```

**If high failure rate:**

```bash
# Run integrity check
python run_integrity_check.py --repair
```

### Step 3: Validate Fix

```bash
# Re-run load test
python run_load_test.py --users 100

# Compare results — response times improved? Success rate increased? Throughput higher?
```

### Step 4: Document & Repeat

- Document what was changed
- Save before/after metrics
- Repeat until goals met
- Update relevant documentation per end-of-session rules

---

## Weekly Maintenance

### Recommended Schedule (Low Traffic Time)

```bash
#!/bin/bash
# weekly_db_maintenance.sh

DATE=$(date +%Y%m%d)
LOGDIR="/var/log/db_tests"
mkdir -p $LOGDIR

echo "=== Weekly Database Maintenance - $DATE ==="

# 1. Integrity Check
python run_integrity_check.py --no-files --export $LOGDIR/integrity_$DATE.txt

# 2. Auto-repair if needed
CRITICAL=$(grep "Critical Issues:" $LOGDIR/integrity_$DATE.txt | awk '{print $4}')
if [ "$CRITICAL" -gt 0 ]; then
    echo "Found $CRITICAL critical issues - auto-repairing..."
    python run_integrity_check.py --repair --no-files
fi

# 3. Performance Test
python run_load_test.py --users 50 --export $LOGDIR/performance_$DATE.txt

# 4. Check for performance degradation
AVG_RESPONSE=$(grep "Average:" $LOGDIR/performance_$DATE.txt | awk '{print $2}' | sed 's/ms//')
if (( $(echo "$AVG_RESPONSE > 500" | bc -l) )); then
    echo "⚠️  Performance degradation detected: ${AVG_RESPONSE}ms"
    # Alert via Sentry or email
fi

echo "Weekly maintenance complete"
```

---

## Troubleshooting Decision Tree

```
┌─────────────────────────────────┐
│  Database Performance Issue     │
└──────────────┬──────────────────┘
               │
               ▼
       ┌───────────────┐
       │ What's slow?  │
       └───┬───────┬───┘
           │       │
     Queries    Operations
           │       │
           ▼       ▼
     ┌─────────┐ ┌──────────────┐
     │ Run:    │ │ Run:         │
     │ EXPLAIN │ │ Load Test    │
     │ ANALYZE │ │ --stress     │
     └─────────┘ └──────────────┘
           │           │
           ▼           ▼
     Add Indexes   Check:
     Optimize     - Connection pool
     Queries      - Locks/deadlocks
                  - Error rate (Sentry)
```

### Quick Decision Guide

| Symptom | Action | Fix |
|---------|--------|-----|
| Slow API responses | Run `load_test.py` | Indexes, caching, read replicas |
| Database growing too fast | Run `stress_test.py` | Archiving, partitioning, cleanup |
| Errors under load | Run `integrity_check.py` | Repair issues, improve validation |
| Connection timeouts | Run `load_test.py --stress` | Increase pool size, scale on Railway |

---

## Success Criteria

### Before Production Launch — ✅ Achieved

- ✅ 10,000+ members loaded successfully (stress test)
- ✅ 250,000+ employment records (stress test)
- ✅ All integrity checks pass
- ✅ Complex queries < 100ms
- ✅ 50 concurrent users supported (load test)
- ✅ Avg response time < 300ms
- ✅ Success rate > 99%
- ✅ Zero critical errors
- ✅ Sentry monitoring configured
- ✅ Railway deployment operational

### Next Targets

- [ ] 100 concurrent users validated
- [ ] 200 concurrent users validated
- [ ] Automated weekly maintenance running
- [ ] Performance regression alerts in Sentry

---

## Quick Reference

| Test Type | Command | When | Duration |
|-----------|---------|------|----------|
| **Unit/Integration** | `pytest -v` | Every commit | 2–5 min |
| **Integrity** | `run_integrity_check.py` | Weekly | 5–10 min |
| **Stress** | `run_stress_test.py` | Before deploy | 15–45 min |
| **Load (Quick)** | `run_load_test.py --quick` | Development | 1–2 min |
| **Load (Standard)** | `run_load_test.py` | Weekly | 5–10 min |
| **Load (Stress)** | `run_load_test.py --stress` | Monthly | 20–30 min |

---

> **End-of-Session Rule:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

---

| Cross-Reference | Location |
|----------------|----------|
| ADR-007: Monitoring Strategy (Sentry) | `/docs/decisions/ADR-007-monitoring-strategy.md` |
| Coding Standards (test patterns) | `/docs/standards/coding-standards.md` |
| Stress Testing Reference | `/docs/reference/stress-testing.md` |
| Load Testing Reference | `/docs/reference/load-testing.md` |
| End-of-Session Documentation | `/docs/guides/END_OF_SESSION_DOCUMENTATION.md` |

---

*Document Version: 1.1*
*Last Updated: February 3, 2026*
