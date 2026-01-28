# Load Testing Reference

Comprehensive guide for load testing the IP2A Database system, including quick commands, performance benchmarks, and scaling strategies.

---

## Quick Reference

### Common Commands

#### Quick Tests

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

#### Custom Configurations

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

### Performance Targets

| Metric | Excellent | Good | Fair | Poor |
|--------|-----------|------|------|------|
| **Avg Response** | < 100ms | < 500ms | < 1000ms | > 1000ms |
| **Throughput** | > 100 ops/s | > 50 ops/s | > 20 ops/s | < 20 ops/s |
| **Success Rate** | > 99% | > 95% | > 90% | < 90% |

### User Patterns

| Pattern | % Reads | % Writes | Typical User |
|---------|---------|----------|--------------|
| `read_heavy` | 90% | 10% | Viewers, searchers, managers |
| `write_heavy` | 30% | 70% | Data entry staff, HR users |
| `mixed` | 60% | 40% | Regular users |
| `file_operations` | 50% | 50% | Document processors |

### Typical Workflow

#### 1. Baseline Test

```bash
# Ensure database has data first
python -m src.seed.run_seed

# Run baseline test
python run_load_test.py --quick
```

#### 2. Standard Load Test

```bash
# Test with 50 concurrent users
python run_load_test.py

# Review results
# If avg response < 500ms and success > 95%, system is healthy
```

#### 3. Stress Test

```bash
# Push system to limits
python run_load_test.py --stress

# Identify bottlenecks
# - Slow queries
# - Connection pool exhaustion
# - Database locks
```

#### 4. Optimize & Retest

```bash
# After optimizations (indexes, caching, etc.)
python run_load_test.py --export after_optimization.txt

# Compare with baseline
```

### Interpreting Results

#### Good Performance Example

```
⏱️  Response Times (ms):
   Average: 85.34ms          ✅ Excellent
   95th Percentile: 250.15ms ✅ Good

📈 Overall Results:
   Throughput: 125.26 ops/sec  ✅ High
   Successful: 99.8%           ✅ Excellent
```

**Action:** System ready for production

#### Poor Performance Example

```
⏱️  Response Times (ms):
   Average: 1,234.56ms       ❌ Poor
   95th Percentile: 5,123.45ms ❌ Very Poor

📈 Overall Results:
   Throughput: 15.26 ops/sec   ⚠️ Low
   Successful: 87.5%           ❌ Poor
```

**Action:** Optimization required before production

### Quick Troubleshooting

#### High Failure Rate (> 5%)

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

#### Slow Response Times (> 500ms avg)

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

#### Low Throughput (< 50 ops/sec)

**Check:**
- Database CPU/memory
- Network latency
- Application bottlenecks

**Fix:**
- Scale database (more CPU/RAM)
- Add read replicas
- Implement caching

### Scaling Estimates

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

### Quick Optimization Checklist

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

### Progressive Load Testing

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

---

## Detailed Documentation

### Overview

The load testing system simulates concurrent users performing realistic database operations to test performance, throughput, and scalability under load. Designed to validate system readiness for 4000 concurrent users.

### Key Features

#### Realistic User Patterns

1. **Read-Heavy Users** (50% of users)
   - List members with pagination
   - View member details with employments
   - Search by status, classification, name
   - List organizations and students
   - Typical: viewers, searchers, managers

2. **Write-Heavy Users** (20% of users)
   - Create new members
   - Update member information
   - Create employment records
   - Update employment status
   - Create organization contacts
   - Typical: data entry staff, HR users

3. **Mixed Users** (25% of users)
   - Balanced read/write operations
   - Typical: everyday users

4. **File Operations Users** (5% of users)
   - List file attachments
   - Create file attachment records
   - Read file metadata
   - Typical: document processors

#### Comprehensive Metrics

- **Response Times**: Average, median, 95th/99th percentile, min/max
- **Throughput**: Operations per second
- **Success Rate**: Percentage of successful operations
- **Error Tracking**: Failed operations with error messages
- **Operation Breakdown**: Per-operation performance stats
- **User Metrics**: Individual user performance data

#### Scalability Testing

- Concurrent user simulation (10-500+ users)
- Configurable operations per user
- Realistic think time between operations
- Gradual ramp-up to simulate realistic load
- Capacity estimation for 4000 users

### Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--users N` | 50 | Number of concurrent users |
| `--ops N` | 50 | Operations per user |
| `--think-time MS` | 100 | Delay between operations (ms) |
| `--ramp-up SEC` | 10 | Ramp-up time (seconds) |
| `--pattern TYPE` | distributed | User pattern distribution |
| `--quick` | - | Quick test: 10 users, 20 ops |
| `--stress` | - | Stress test: 200 users, 100 ops |
| `--export FILE` | - | Export report to file |
| `--force` | - | Force run in production |

### Test Scenarios

#### Scenario 1: Normal Load Test

**Goal:** Test typical weekday load with 50 concurrent users

```bash
python run_load_test.py --users 50 --ops 50
```

**Expected Results:**
- Average response time: < 200ms
- Throughput: > 50 ops/sec
- Success rate: > 99%

#### Scenario 2: Peak Load Test

**Goal:** Test peak hours with 150 concurrent users

```bash
python run_load_test.py --users 150 --ops 75
```

**Expected Results:**
- Average response time: < 500ms
- Throughput: > 100 ops/sec
- Success rate: > 98%

#### Scenario 3: Stress Test

**Goal:** Push system to limits with 200+ concurrent users

```bash
python run_load_test.py --stress
# Or: python run_load_test.py --users 200 --ops 100
```

**Expected Results:**
- Average response time: < 1000ms
- System remains stable (no crashes)
- Identify bottlenecks

#### Scenario 4: Read-Heavy Load

**Goal:** Test reporting/dashboard usage (all reads)

```bash
python run_load_test.py --users 100 --pattern read_heavy
```

**Expected Results:**
- Very fast response times (< 100ms)
- High throughput (> 150 ops/sec)
- Minimal database contention

#### Scenario 5: Write-Heavy Load

**Goal:** Test data entry operations (bulk writes)

```bash
python run_load_test.py --users 30 --pattern write_heavy --ops 100
```

**Expected Results:**
- Moderate response times (< 300ms)
- Lower throughput than reads
- Test transaction handling

#### Scenario 6: Sustained Load

**Goal:** Test system stability over time

```bash
python run_load_test.py --users 50 --ops 500 --think-time 500
```

**Expected Results:**
- Consistent performance over time
- No memory leaks
- Stable connection pool

### Understanding Results

#### Sample Report

```
======================================================================
📊 LOAD TEST REPORT
======================================================================

⚙️  Test Configuration:
   Concurrent Users: 50
   Operations per User: 50
   Think Time: 100ms
   Ramp-up Time: 10s
   Test Duration: 45.23s

👥 User Pattern Distribution:
   read_heavy: 25 users (50.0%)
   write_heavy: 10 users (20.0%)
   mixed: 12 users (24.0%)
   file_operations: 3 users (6.0%)

📈 Overall Results:
   Total Operations: 2,500
   Successful: 2,495 (99.80%)
   Failed: 5 (0.20%)
   Throughput: 55.26 ops/sec

⏱️  Response Times (ms):
   Average: 185.34ms
   Median: 142.15ms
   95th Percentile: 412.50ms
   99th Percentile: 589.23ms
   Min: 12.45ms
   Max: 1,245.67ms

🔍 Operation Breakdown:
   read_member_list: 520 ops, avg 98.45ms
   read_member_detail: 485 ops, avg 215.67ms
   search_members: 445 ops, avg 125.34ms
   create_member: 198 ops, avg 245.78ms
   update_member: 187 ops, avg 198.23ms
   ...

🎯 Performance Assessment:
   ✅ Good: Average response time < 500ms
   ✅ No failed operations
   ✅ Good throughput: 55.26 ops/sec

📊 Scaling to 4000 Users:
   Current capacity: ~250 concurrent users
   Estimated response time at 4000 users: 2960ms
   ⚠️  System may handle 4000 users with degraded performance
   💡 Recommendation: Add read replicas, optimize queries

======================================================================
```

### Scaling to 4000 Users

#### Current Baseline

After running load tests, you'll understand:
- **Current Capacity**: How many concurrent users system can handle
- **Response Time Degradation**: How performance degrades with load
- **Bottlenecks**: Database, connections, queries, etc.

#### Estimation Formula

```
Capacity = (Target Response Time / Current Avg Response Time) × Current Users
```

Example:
- Current: 50 users, 200ms avg response
- Target: 500ms response time
- Capacity = (500 / 200) × 50 = 125 concurrent users

#### Scaling Strategies

##### 1. Database Optimization

**Query Optimization:**
```sql
-- Add indexes for common queries
CREATE INDEX idx_members_status ON members(status);
CREATE INDEX idx_members_classification ON members(classification);
CREATE INDEX idx_members_last_name ON members(last_name);
CREATE INDEX idx_employments_member_current ON member_employments(member_id, is_current);
```

**Connection Pooling:**
```python
# src/db/session.py
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 40
SQLALCHEMY_POOL_RECYCLE = 3600
```

##### 2. Read Replicas

For read-heavy workloads (60%+ reads):
- Primary database: Handles writes
- Read replicas: Handle reads
- Expected improvement: 2-3x capacity

##### 3. Caching Layer

Cache frequently accessed data:
- Redis/Memcached for session data
- Application-level caching for static data
- Expected improvement: 3-5x capacity for cached queries

##### 4. Horizontal Scaling

Multiple application servers:
- Load balancer (nginx/HAProxy)
- 3-5 app servers behind load balancer
- Shared database or connection pooling
- Expected improvement: 3-5x capacity

##### 5. Database Sharding (Advanced)

For very large scale (10k+ users):
- Shard by organization or geographic region
- Complex but scales linearly
- Expected improvement: 10x+ capacity

### Best Practices

#### Before Testing

1. ✅ **Seed Database** with realistic data
   ```bash
   python run_stress_test.py
   ```

2. ✅ **Warm Up Database** (optional)
   ```bash
   python run_load_test.py --quick
   ```

3. ✅ **Monitor Resources**
   - Database CPU/memory
   - Connection pool usage
   - Disk I/O

4. ✅ **Baseline Metrics**
   - Run test with minimal load first
   - Record baseline performance

#### During Testing

1. ✅ **Monitor in Real-Time**
   - Database connections
   - Query execution times
   - Error logs

2. ✅ **Don't Interrupt**
   - Let tests complete fully
   - Partial results are less useful

3. ✅ **Run Multiple Times**
   - Results can vary
   - Average 3+ test runs

#### After Testing

1. ✅ **Analyze Reports**
   - Identify slow operations
   - Find error patterns
   - Look for bottlenecks

2. ✅ **Compare Runs**
   - Track improvements
   - Validate optimizations
   - Detect regressions

3. ✅ **Document Findings**
   - Save reports with timestamps
   - Note infrastructure changes
   - Track optimization history

### Troubleshooting

#### Issue: Tests fail immediately

**Symptoms:**
```
❌ ERROR: (psycopg2.OperationalError) too many connections
```

**Cause:** Connection pool exhausted

**Solution:**
```python
# Increase pool size in src/db/session.py
SQLALCHEMY_POOL_SIZE = 40
SQLALCHEMY_MAX_OVERFLOW = 60
```

Or reduce concurrent users:
```bash
python run_load_test.py --users 25
```

#### Issue: Very high response times

**Symptoms:**
```
⏱️  Response Times (ms):
   Average: 5,234.56ms
```

**Cause:** Database overloaded, missing indexes, or slow queries

**Solution:**
1. Check for missing indexes
2. Analyze slow query log
3. Reduce concurrent load
4. Add read replicas

#### Issue: High failure rate

**Symptoms:**
```
❌ High failure rate: 15.23%
```

**Cause:** Deadlocks, connection timeouts, or data integrity issues

**Solution:**
1. Review error logs
2. Check for database locks
3. Increase connection timeout
4. Fix data issues

#### Issue: Inconsistent results

**Symptoms:** Test results vary widely between runs

**Cause:** External load, caching effects, or database warm-up

**Solution:**
1. Run warmup test first
2. Isolate test environment
3. Run multiple tests and average
4. Test at same time of day

### Production Considerations

#### Safety Checklist

- [ ] Never run in production without `--force` flag
- [ ] Test in staging environment first
- [ ] Schedule during maintenance windows
- [ ] Monitor production metrics closely
- [ ] Have rollback plan ready
- [ ] Notify team before testing
- [ ] Set up alerts for issues

#### Staging Environment

Recommended staging setup:
- Mirror production database schema
- Use stress test data (10k+ members)
- Same application configuration
- Isolated from production users
- Monitor same metrics as production

#### Gradual Load Testing

Start small and scale up:

```bash
# Week 1: Baseline
python run_load_test.py --users 10

# Week 2: Small load
python run_load_test.py --users 25

# Week 3: Medium load
python run_load_test.py --users 50

# Week 4: Large load
python run_load_test.py --users 100

# Week 5: Stress test
python run_load_test.py --stress
```

### Integration with CI/CD

#### Automated Performance Testing

```yaml
# .github/workflows/performance-test.yml
name: Performance Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  performance:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Seed database
        run: python -m src.seed.run_seed

      - name: Run load test
        run: python run_load_test.py --quick --export performance_report.txt

      - name: Check performance thresholds
        run: |
          # Fail if average response time > 500ms
          grep "Average:" performance_report.txt | \
            awk '{if ($2 > 500) exit 1}'

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: performance_report.txt
```

#### Performance Monitoring

Track performance over time:

```bash
#!/bin/bash
# weekly_performance_test.sh

DATE=$(date +%Y%m%d)
REPORT_DIR="/var/log/performance_reports"
mkdir -p $REPORT_DIR

# Run standard load test
python run_load_test.py --users 50 --ops 50 --export "$REPORT_DIR/perf_$DATE.txt"

# Extract key metrics
AVG_RESPONSE=$(grep "Average:" "$REPORT_DIR/perf_$DATE.txt" | awk '{print $2}')
THROUGHPUT=$(grep "Throughput:" "$REPORT_DIR/perf_$DATE.txt" | awk '{print $2}')

# Log to monitoring system
echo "performance,type=avg_response value=$AVG_RESPONSE" | telegraf
echo "performance,type=throughput value=$THROUGHPUT" | telegraf

# Alert if degradation
if (( $(echo "$AVG_RESPONSE > 500" | bc -l) )); then
    echo "⚠️  Performance degradation detected!" | mail -s "Performance Alert" devops@example.com
fi
```

### Advanced Scenarios

#### Custom User Pattern

Create custom user behavior:

```python
from src.tests.load_test import LoadTestUser

class CustomUser(LoadTestUser):
    def _select_operation(self):
        # Your custom logic
        return self.custom_operation

    def custom_operation(self):
        # Your custom database operation
        pass
```

#### Multi-Stage Load Test

Test realistic daily patterns:

```bash
#!/bin/bash
# daily_pattern_test.sh

echo "Morning: Light load (20 users)"
python run_load_test.py --users 20 --ops 30

sleep 60

echo "Midday: Peak load (100 users)"
python run_load_test.py --users 100 --ops 50

sleep 60

echo "Afternoon: Moderate load (50 users)"
python run_load_test.py --users 50 --ops 40

sleep 60

echo "Evening: Light load (15 users)"
python run_load_test.py --users 15 --ops 25
```

#### Geographic Distribution Simulation

Test from multiple regions:

```bash
# Region 1: US East
python run_load_test.py --users 25 --think-time 100

# Region 2: US West
python run_load_test.py --users 15 --think-time 150

# Region 3: Europe
python run_load_test.py --users 10 --think-time 300
```

### Scheduled Testing

#### Weekly Performance Test

```bash
#!/bin/bash
# Run every Sunday at 2 AM
0 2 * * 0 cd /app && python run_load_test.py --export /var/log/perf_$(date +\%Y\%m\%d).txt
```

#### Pre-Deployment Test

```bash
# Before each deployment
python run_load_test.py --quick

# Ensure:
# - Avg response < 200ms
# - Success rate > 99%
# - No regressions vs. baseline
```

#### Monthly Stress Test

```bash
# First Sunday of each month
python run_load_test.py --stress --export stress_$(date +%Y%m%d).txt
```

---

## File Reference

| File | Purpose |
|------|---------|
| `run_load_test.py` | CLI runner (root level) |
| `src/tests/load_test.py` | Load test implementation |
| `docs/reference/load-testing.md` | This documentation |

---

## Next Steps

1. **Run Baseline Test**
   ```bash
   python run_load_test.py --quick
   ```

2. **Run Standard Test**
   ```bash
   python run_load_test.py
   ```

3. **Analyze Results**
   - Review response times
   - Check throughput
   - Identify bottlenecks

4. **Optimize**
   - Add indexes
   - Tune connection pool
   - Cache frequently accessed data

5. **Re-Test**
   - Validate improvements
   - Test at higher loads
   - Document progress

6. **Scale Up**
   - Gradually increase load
   - Test towards 4000 user goal
   - Plan infrastructure scaling

---

## Need Help?

- Help text: `python run_load_test.py --help`
- Report issues: GitHub Issues
- Scaling architecture: [docs/Architecture/SCALABILITY_ARCHITECTURE.md](../Architecture/SCALABILITY_ARCHITECTURE.md)

---

*Last Updated: January 28, 2026*
*Version: 2.0 (Consolidated)*
*Status: Production Ready*
