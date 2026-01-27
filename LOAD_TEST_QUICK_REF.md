# Load Testing - Quick Reference

## Common Commands

### Quick Tests

```bash
# Quick test - 10 users, 20 ops (1-2 minutes)
python run_load_test.py --quick

# Mini test - 5 users, 10 ops (30 seconds)
python run_load_test.py --users 5 --ops 10

# Standard test - 50 users, 50 ops (5-10 minutes)
python run_load_test.py

# Stress test - 200 users, 100 ops (20-30 minutes)
python run_load_test.py --stress
```

### Custom Configurations

```bash
# 100 concurrent users
python run_load_test.py --users 100 --ops 50

# All users read-heavy (fast)
python run_load_test.py --pattern read_heavy

# All users write-heavy (slower)
python run_load_test.py --pattern write_heavy

# Export report to file
python run_load_test.py --export report_$(date +%Y%m%d).txt
```

## Performance Targets

| Metric | Excellent | Good | Fair | Poor |
|--------|-----------|------|------|------|
| **Avg Response** | < 100ms | < 500ms | < 1000ms | > 1000ms |
| **Throughput** | > 100 ops/s | > 50 ops/s | > 20 ops/s | < 20 ops/s |
| **Success Rate** | > 99% | > 95% | > 90% | < 90% |

## User Patterns

| Pattern | % Reads | % Writes | Typical User |
|---------|---------|----------|--------------|
| `read_heavy` | 90% | 10% | Viewers, searchers |
| `write_heavy` | 30% | 70% | Data entry staff |
| `mixed` | 60% | 40% | Regular users |
| `file_operations` | 50% | 50% | Document processors |

## Typical Workflow

### 1. Baseline Test
```bash
# Ensure database has data first
python -m src.seed.run_seed

# Run baseline test
python run_load_test.py --quick
```

### 2. Standard Load Test
```bash
# Test with 50 concurrent users
python run_load_test.py

# Review results
# If avg response < 500ms and success > 95%, system is healthy
```

### 3. Stress Test
```bash
# Push system to limits
python run_load_test.py --stress

# Identify bottlenecks
# - Slow queries
# - Connection pool exhaustion
# - Database locks
```

### 4. Optimize & Retest
```bash
# After optimizations (indexes, caching, etc.)
python run_load_test.py --export after_optimization.txt

# Compare with baseline
```

## Interpreting Results

### Good Performance Example
```
⏱️  Response Times (ms):
   Average: 85.34ms          ✅ Excellent
   95th Percentile: 250.15ms ✅ Good

📈 Overall Results:
   Throughput: 125.26 ops/sec  ✅ High
   Successful: 99.8%           ✅ Excellent
```
**Action:** System ready for production

### Poor Performance Example
```
⏱️  Response Times (ms):
   Average: 1,234.56ms       ❌ Poor
   95th Percentile: 5,123.45ms ❌ Very Poor

📈 Overall Results:
   Throughput: 15.26 ops/sec   ⚠️ Low
   Successful: 87.5%           ❌ Poor
```
**Action:** Optimization required before production

## Troubleshooting

### High Failure Rate (> 5%)

**Check:**
- Database connection pool size
- Missing indexes
- Data integrity issues
- Foreign key violations

**Fix:**
```python
# Increase connection pool (src/db/session.py)
SQLALCHEMY_POOL_SIZE = 40
SQLALCHEMY_MAX_OVERFLOW = 60
```

### Slow Response Times (> 500ms avg)

**Check:**
- Slow queries (use EXPLAIN ANALYZE)
- Missing indexes
- Database locks
- Connection pool exhaustion

**Fix:**
```sql
-- Add indexes for common queries
CREATE INDEX idx_members_status ON members(status);
CREATE INDEX idx_members_last_name ON members(last_name);
CREATE INDEX idx_employments_member ON member_employments(member_id);
```

### Low Throughput (< 50 ops/sec)

**Check:**
- Database CPU/memory
- Network latency
- Application bottlenecks

**Fix:**
- Scale database (more CPU/RAM)
- Add read replicas
- Implement caching

## Scaling Estimates

| Current Users | Avg Response | Estimated Capacity |
|---------------|--------------|-------------------|
| 50 | 100ms | 500 users |
| 50 | 200ms | 250 users |
| 50 | 500ms | 100 users |
| 100 | 200ms | 500 users |
| 100 | 500ms | 200 users |

**To reach 4000 users:**
- Current: 50 users @ 200ms avg
- Target: 4000 users @ <500ms avg
- Need: 80x capacity increase
- Solutions: Read replicas, caching, horizontal scaling

## Quick Optimization Checklist

Performance improvement priority order:

1. ✅ **Add Database Indexes** (10-100x improvement)
   ```sql
   CREATE INDEX idx_members_status ON members(status);
   CREATE INDEX idx_employments_member_current ON member_employments(member_id, is_current);
   ```

2. ✅ **Increase Connection Pool** (2-5x improvement)
   ```python
   SQLALCHEMY_POOL_SIZE = 40
   SQLALCHEMY_MAX_OVERFLOW = 60
   ```

3. ✅ **Add Caching Layer** (3-10x improvement)
   - Redis for session data
   - Application-level caching

4. ✅ **Read Replicas** (2-3x improvement)
   - Route reads to replicas
   - Writes to primary

5. ✅ **Horizontal Scaling** (3-5x improvement)
   - Multiple app servers
   - Load balancer

## Scheduled Testing

### Weekly Performance Test
```bash
#!/bin/bash
# Run every Sunday at 2 AM
0 2 * * 0 cd /app && python run_load_test.py --export /var/log/perf_$(date +\%Y\%m\%d).txt
```

### Pre-Deployment Test
```bash
# Before each deployment
python run_load_test.py --quick

# Ensure:
# - Avg response < 200ms
# - Success rate > 99%
# - No regressions vs. baseline
```

### Monthly Stress Test
```bash
# First Sunday of each month
python run_load_test.py --stress --export stress_$(date +%Y%m%d).txt
```

## Need Help?

- Full documentation: [LOAD_TEST.md](LOAD_TEST.md)
- Help text: `python run_load_test.py --help`
- Report issues: GitHub Issues

## Progressive Load Testing

Test at increasing scales to identify breaking point:

```bash
# Phase 1: Baseline (light load)
python run_load_test.py --users 25

# Phase 2: Normal load
python run_load_test.py --users 50

# Phase 3: Peak load
python run_load_test.py --users 100

# Phase 4: Heavy load
python run_load_test.py --users 150

# Phase 5: Stress test
python run_load_test.py --users 200

# Phase 6: Breaking point
python run_load_test.py --users 300
```

After each phase:
1. Review metrics
2. Identify bottlenecks
3. Optimize if needed
4. Continue to next phase

**Goal:** Find the point where performance degrades, then optimize to push that limit higher.
