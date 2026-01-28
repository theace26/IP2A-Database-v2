# Testing Strategy - Stress Test vs Load Test

## Overview

Your database has two complementary testing systems:

1. **Stress Test** ([STRESS_TEST.md](STRESS_TEST.md)) - Tests database with LARGE DATA VOLUMES
2. **Load Test** ([LOAD_TEST.md](LOAD_TEST.md)) - Tests database with CONCURRENT USERS

Both are essential for production readiness.

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

**Duration:** 15-45 minutes

**Result:** Database filled with large-scale test data

---

## Load Test (Concurrent Users)

**Purpose:** Test database performance under concurrent user load

**What it does:**
- Simulates 10-500 concurrent users
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

**Duration:** 5-30 minutes

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

**Validates:**
- ✅ Database can store large datasets
- ✅ Queries perform well on large tables
- ✅ Indexes are effective
- ✅ Storage capacity is sufficient

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

**Validates:**
- ✅ Database handles concurrent operations
- ✅ Connection pool is sized correctly
- ✅ No deadlocks or race conditions
- ✅ System scales to target user count

### Phase 3: Combined Testing (Realistic)

```bash
# Step 1: Start with stress test data
python run_stress_test.py

# Step 2: Run load test on large dataset
python run_load_test.py --users 100 --ops 100

# Step 3: Monitor performance
# - Database CPU/memory
# - Query execution times
# - Connection pool usage
```

**Expected Time:** 1.5 hours

**Validates:**
- ✅ System performs well with both:
  - Large data volumes
  - Many concurrent users
- ✅ Production-ready performance

---

## Testing Matrix

| Scenario | Data Volume | Concurrent Users | Test Type | Command |
|----------|-------------|------------------|-----------|---------|
| **Development** | Small (500 records) | Low (1-5) | Unit tests | `pytest` |
| **Integration** | Medium (5k records) | Medium (10-20) | API tests | `pytest src/tests/` |
| **Performance** | Large (100k+ records) | N/A | Stress test | `run_stress_test.py` |
| **Load** | Any | High (50-200) | Load test | `run_load_test.py` |
| **Production Sim** | Large (100k+ records) | High (100-500) | Combined | Both |

---

## Performance Goals

### For 4000 Concurrent Users

**Database Requirements:**

| Metric | Target | Notes |
|--------|--------|-------|
| **Data Volume** | 50k+ members | Stress test validates |
| **Concurrent Users** | 4000 | Load test validates |
| **Avg Response Time** | < 500ms | Under load |
| **95th Percentile** | < 1000ms | Under load |
| **Throughput** | > 200 ops/sec | Per app server |
| **Success Rate** | > 99.9% | Critical operations |
| **Connection Pool** | 100-200 | Per app server |

**Infrastructure Recommendations:**

| Component | Minimum | Recommended | Optimal |
|-----------|---------|-------------|---------|
| **App Servers** | 2 | 4-6 | 10+ |
| **Database CPU** | 4 cores | 8 cores | 16+ cores |
| **Database RAM** | 8 GB | 16 GB | 32+ GB |
| **Database** | 1 primary | 1 primary + 2 replicas | Sharded |
| **Connection Pool** | 50/server | 100/server | 200/server |
| **Caching** | None | Redis (2 GB) | Redis cluster |

---

## Pre-Production Checklist

### Data Validation
- [ ] Run stress test to populate database
- [ ] Run integrity check (no critical issues)
- [ ] Verify all indexes exist
- [ ] Test complex queries perform well (< 100ms)
- [ ] Validate data relationships

### Performance Validation
- [ ] Run load test with 50 users (baseline)
- [ ] Run load test with 100 users (target)
- [ ] Run load test with 200 users (stress)
- [ ] Avg response time < 500ms
- [ ] Success rate > 99%

### Scalability Validation
- [ ] Test read replicas (if applicable)
- [ ] Test connection pool scaling
- [ ] Test caching layer (if applicable)
- [ ] Estimate capacity for 4000 users
- [ ] Document scaling plan

### Monitoring Setup
- [ ] Database CPU/memory alerts
- [ ] Slow query logging enabled
- [ ] Connection pool monitoring
- [ ] Response time tracking
- [ ] Error rate alerts

---

## Optimization Workflow

### Step 1: Identify Bottleneck

```bash
# Run combined test
python run_stress_test.py
python run_load_test.py --users 100

# Check results
# - Slow queries?
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

# Compare results
# - Response times improved?
# - Success rate increased?
# - Throughput higher?
```

### Step 4: Document & Repeat

- Document what was changed
- Save before/after metrics
- Repeat until goals met

---

## Weekly Maintenance

### Every Sunday (Low Traffic Time)

```bash
#!/bin/bash
# weekly_db_maintenance.sh

DATE=$(date +%Y%m%d)
LOGDIR="/var/log/db_tests"
mkdir -p $LOGDIR

echo "=== Weekly Database Maintenance - $DATE ===" | tee $LOGDIR/weekly_$DATE.log

# 1. Integrity Check
echo "Running integrity check..." | tee -a $LOGDIR/weekly_$DATE.log
python run_integrity_check.py --no-files --export $LOGDIR/integrity_$DATE.txt

# 2. Auto-repair if needed
CRITICAL=$(grep "Critical Issues:" $LOGDIR/integrity_$DATE.txt | awk '{print $4}')
if [ "$CRITICAL" -gt 0 ]; then
    echo "Found $CRITICAL critical issues - auto-repairing..." | tee -a $LOGDIR/weekly_$DATE.log
    python run_integrity_check.py --repair --no-files
fi

# 3. Performance Test
echo "Running performance test..." | tee -a $LOGDIR/weekly_$DATE.log
python run_load_test.py --users 50 --export $LOGDIR/performance_$DATE.txt

# 4. Check for performance degradation
AVG_RESPONSE=$(grep "Average:" $LOGDIR/performance_$DATE.txt | awk '{print $2}' | sed 's/ms//')
if (( $(echo "$AVG_RESPONSE > 500" | bc -l) )); then
    echo "⚠️  Performance degradation detected: ${AVG_RESPONSE}ms" | mail -s "DB Alert" devops@example.com
fi

echo "Weekly maintenance complete" | tee -a $LOGDIR/weekly_$DATE.log
```

---

## Troubleshooting Decision Tree

```
┌─────────────────────────────┐
│ Database Performance Issue  │
└─────────────┬───────────────┘
              │
              ▼
      ┌───────────────┐
      │ What's slow?  │
      └───┬───────┬───┘
          │       │
    Queries     Operations
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
                 - Error rate
```

### Decision Guide

**Symptom:** Slow API responses
→ **Run:** `python run_load_test.py`
→ **Check:** Response times, throughput
→ **Fix:** Indexes, caching, read replicas

**Symptom:** Database growing too fast
→ **Run:** `python run_stress_test.py`
→ **Check:** Record counts, file sizes
→ **Fix:** Archiving, partitioning, cleanup

**Symptom:** Errors under load
→ **Run:** `python run_integrity_check.py`
→ **Check:** Data integrity, foreign keys
→ **Fix:** Repair issues, improve validation

**Symptom:** Connection timeouts
→ **Run:** `python run_load_test.py --stress`
→ **Check:** Connection pool exhaustion
→ **Fix:** Increase pool size, add app servers

---

## Success Criteria

### Before Production Launch

✅ **Stress Test:**
- 10,000+ members loaded successfully
- 250,000+ employment records
- All integrity checks pass
- Complex queries < 100ms

✅ **Load Test:**
- 100 concurrent users supported
- Avg response time < 300ms
- Success rate > 99%
- Zero critical errors

✅ **Monitoring:**
- Dashboards set up
- Alerts configured
- Runbooks documented
- Backup/restore tested

---

## Quick Reference

| Test Type | Command | When | Duration |
|-----------|---------|------|----------|
| **Integrity** | `run_integrity_check.py` | Weekly | 5-10 min |
| **Stress** | `run_stress_test.py` | Before deploy | 15-45 min |
| **Load (Quick)** | `run_load_test.py --quick` | Development | 1-2 min |
| **Load (Standard)** | `run_load_test.py` | Weekly | 5-10 min |
| **Load (Stress)** | `run_load_test.py --stress` | Monthly | 20-30 min |

---

*Last Updated: January 27, 2026*
*Version: 1.0*
