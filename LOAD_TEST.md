## Load Testing Documentation

## Overview

The load testing system simulates concurrent users performing realistic database operations to test performance, throughput, and scalability under load. Designed to validate system readiness for 4000 concurrent users.

## Key Features

### 🎭 Realistic User Patterns

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

### 📊 Comprehensive Metrics

- **Response Times**: Average, median, 95th/99th percentile, min/max
- **Throughput**: Operations per second
- **Success Rate**: Percentage of successful operations
- **Error Tracking**: Failed operations with error messages
- **Operation Breakdown**: Per-operation performance stats
- **User Metrics**: Individual user performance data

### 🎯 Scalability Testing

- Concurrent user simulation (10-500+ users)
- Configurable operations per user
- Realistic think time between operations
- Gradual ramp-up to simulate realistic load
- Capacity estimation for 4000 users

---

## Quick Start

### Basic Load Test (50 users)

```bash
python run_load_test.py
```

### Quick Test (10 users, 20 ops)

```bash
python run_load_test.py --quick
```

### Stress Test (200 users, 100 ops)

```bash
python run_load_test.py --stress
```

### Custom Configuration

```bash
# 100 concurrent users, 50 operations each
python run_load_test.py --users 100 --ops 50

# All users read-heavy pattern
python run_load_test.py --pattern read_heavy

# Export report to file
python run_load_test.py --export load_test_report.txt
```

---

## Usage

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

### User Patterns

| Pattern | Description | Operations |
|---------|-------------|------------|
| `read_heavy` | 90% reads, 10% writes | Search, list, view details |
| `write_heavy` | 70% writes, 30% reads | Create, update records |
| `mixed` | 60% reads, 40% writes | Balanced usage |
| `file_operations` | File attachments | List, create, read files |
| `distributed` | Mixed patterns | Realistic distribution |

---

## Test Scenarios

### Scenario 1: Normal Load Test

**Goal:** Test typical weekday load with 50 concurrent users

```bash
python run_load_test.py --users 50 --ops 50
```

**Expected Results:**
- Average response time: < 200ms
- Throughput: > 50 ops/sec
- Success rate: > 99%

### Scenario 2: Peak Load Test

**Goal:** Test peak hours with 150 concurrent users

```bash
python run_load_test.py --users 150 --ops 75
```

**Expected Results:**
- Average response time: < 500ms
- Throughput: > 100 ops/sec
- Success rate: > 98%

### Scenario 3: Stress Test

**Goal:** Push system to limits with 200+ concurrent users

```bash
python run_load_test.py --stress
# Or: python run_load_test.py --users 200 --ops 100
```

**Expected Results:**
- Average response time: < 1000ms
- System remains stable (no crashes)
- Identify bottlenecks

### Scenario 4: Read-Heavy Load

**Goal:** Test reporting/dashboard usage (all reads)

```bash
python run_load_test.py --users 100 --pattern read_heavy
```

**Expected Results:**
- Very fast response times (< 100ms)
- High throughput (> 150 ops/sec)
- Minimal database contention

### Scenario 5: Write-Heavy Load

**Goal:** Test data entry operations (bulk writes)

```bash
python run_load_test.py --users 30 --pattern write_heavy --ops 100
```

**Expected Results:**
- Moderate response times (< 300ms)
- Lower throughput than reads
- Test transaction handling

### Scenario 6: Sustained Load

**Goal:** Test system stability over time

```bash
python run_load_test.py --users 50 --ops 500 --think-time 500
```

**Expected Results:**
- Consistent performance over time
- No memory leaks
- Stable connection pool

---

## Understanding Results

### Sample Report

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

### Interpreting Metrics

#### Response Times

| Average | Assessment | Action |
|---------|------------|--------|
| < 100ms | Excellent | System performing optimally |
| 100-500ms | Good | Acceptable for production |
| 500-1000ms | Fair | Consider optimization |
| > 1000ms | Poor | Optimization required |

#### Throughput

| Ops/Sec | Assessment | Capacity |
|---------|------------|----------|
| > 100 | High | Can handle many users |
| 50-100 | Good | Suitable for medium load |
| 20-50 | Fair | May struggle under high load |
| < 20 | Poor | Capacity issues |

#### Success Rate

| Rate | Assessment | Action |
|------|------------|--------|
| > 99% | Excellent | System stable |
| 95-99% | Good | Monitor errors |
| 90-95% | Fair | Investigate failures |
| < 90% | Poor | Critical issues |

---

## Scaling to 4000 Users

### Current Baseline

After running load tests, you'll understand:
- **Current Capacity**: How many concurrent users system can handle
- **Response Time Degradation**: How performance degrades with load
- **Bottlenecks**: Database, connections, queries, etc.

### Estimation Formula

```
Capacity = (Target Response Time / Current Avg Response Time) × Current Users
```

Example:
- Current: 50 users, 200ms avg response
- Target: 500ms response time
- Capacity = (500 / 200) × 50 = 125 concurrent users

### Scaling Strategies

#### 1. Database Optimization

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

#### 2. Read Replicas

For read-heavy workloads (60%+ reads):
- Primary database: Handles writes
- Read replicas: Handle reads
- Expected improvement: 2-3x capacity

#### 3. Caching Layer

Cache frequently accessed data:
- Redis/Memcached for session data
- Application-level caching for static data
- Expected improvement: 3-5x capacity for cached queries

#### 4. Horizontal Scaling

Multiple application servers:
- Load balancer (nginx/HAProxy)
- 3-5 app servers behind load balancer
- Shared database or connection pooling
- Expected improvement: 3-5x capacity

#### 5. Database Sharding (Advanced)

For very large scale (10k+ users):
- Shard by organization or geographic region
- Complex but scales linearly
- Expected improvement: 10x+ capacity

### Progressive Testing

Test at increasing scales:

```bash
# Step 1: Baseline (50 users)
python run_load_test.py --users 50

# Step 2: Double (100 users)
python run_load_test.py --users 100

# Step 3: Peak load (200 users)
python run_load_test.py --users 200

# Step 4: Stress (300+ users)
python run_load_test.py --users 300
```

After each test:
1. Review performance metrics
2. Identify bottlenecks
3. Implement optimizations
4. Re-test

---

## Best Practices

### Before Testing

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

### During Testing

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

### After Testing

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

---

## Troubleshooting

### Issue: Tests fail immediately

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

### Issue: Very high response times

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

### Issue: High failure rate

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

### Issue: Inconsistent results

**Symptoms:** Test results vary widely between runs

**Cause:** External load, caching effects, or database warm-up

**Solution:**
1. Run warmup test first
2. Isolate test environment
3. Run multiple tests and average
4. Test at same time of day

---

## Production Considerations

### Safety Checklist

- [ ] Never run in production without `--force` flag
- [ ] Test in staging environment first
- [ ] Schedule during maintenance windows
- [ ] Monitor production metrics closely
- [ ] Have rollback plan ready
- [ ] Notify team before testing
- [ ] Set up alerts for issues

### Staging Environment

Recommended staging setup:
- Mirror production database schema
- Use stress test data (10k+ members)
- Same application configuration
- Isolated from production users
- Monitor same metrics as production

### Gradual Load Testing

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

---

## Integration with CI/CD

### Automated Performance Testing

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

### Performance Monitoring

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

---

## Advanced Scenarios

### Custom User Pattern

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

### Multi-Stage Load Test

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

### Geographic Distribution Simulation

Test from multiple regions:

```bash
# Region 1: US East
python run_load_test.py --users 25 --think-time 100

# Region 2: US West
python run_load_test.py --users 15 --think-time 150

# Region 3: Europe
python run_load_test.py --users 10 --think-time 300
```

---

## File Reference

| File | Purpose |
|------|---------|
| `run_load_test.py` | CLI runner (root level) |
| `src/tests/load_test.py` | Load test implementation |
| `LOAD_TEST.md` | This documentation |

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

*Last Updated: January 27, 2026*
*Version: 1.0*
*Status: Production Ready*
