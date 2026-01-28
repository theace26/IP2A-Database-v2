# ip2adb - IP2A Database Management Tool

## Overview

`ip2adb` is a unified command-line tool for all IP2A database operations. It consolidates seeding, integrity checking, load testing, and data management into a single, easy-to-use interface.

**One tool to rule them all** - instead of remembering multiple scripts, just use `ip2adb`.

---

## Quick Start

```bash
# Normal development setup
./ip2adb seed

# Health check
./ip2adb integrity

# Performance test
./ip2adb load --quick

# Complete test suite
./ip2adb all

# Get help
./ip2adb --help
./ip2adb seed --help
```

---

## Installation

The tool is ready to use at `/app/ip2adb`.

### Add to PATH (Optional)

```bash
# Make it available system-wide
sudo ln -s /app/ip2adb /usr/local/bin/ip2adb

# Or add alias to ~/.bashrc or ~/.zshrc
echo 'alias ip2adb="/app/ip2adb"' >> ~/.bashrc
source ~/.bashrc
```

### Windows

```bash
# Use full path or add to PATH
python /app/ip2adb seed
```

---

## Commands

### Overview

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `seed` | Populate database | Development, testing |
| `integrity` | Check data quality | Weekly, after imports |
| `load` | Test performance | Before deploy, weekly |
| `all` | Complete test suite | Pre-production validation |
| `reset` | Delete all data | Fresh start (dangerous!) |

---

## Command: seed

**Purpose:** Populate the database with test data

### Basic Usage

```bash
# Normal seed (standard development data)
./ip2adb seed

# Stress test seed (large-scale data)
./ip2adb seed --stress

# Quick seed (minimal data for fast setup)
./ip2adb seed --quick

# Append data (don't truncate existing)
./ip2adb seed --no-truncate
```

### Data Volumes

| Mode | Members | Students | Instructors | Locations | Organizations | Employments | Files |
|------|---------|----------|-------------|-----------|---------------|-------------|-------|
| **Normal** | 50 | 510 | 54 | 20 | 20 | ~150 | - |
| **Quick** | 10 | 100 | 10 | 5 | 5 | ~30 | - |
| **Stress** | 10,000 | 1,000 | 500 | 250 | 200 | 250,000+ | 150,000+ |

### Custom Volumes (Planned)

```bash
# Custom member count (future feature)
./ip2adb seed --members 5000 --students 1000

# Custom organization count (future feature)
./ip2adb seed --organizations 500
```

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--stress` | Use stress test volumes | `ip2adb seed --stress` |
| `--quick` | Minimal data for fast setup | `ip2adb seed --quick` |
| `--no-truncate` | Append data (don't delete existing) | `ip2adb seed --no-truncate` |
| `--members N` | Number of members (planned) | `ip2adb seed --members 5000` |
| `--students N` | Number of students (planned) | `ip2adb seed --students 2000` |
| `--instructors N` | Number of instructors (planned) | `ip2adb seed --instructors 100` |
| `--locations N` | Number of locations (planned) | `ip2adb seed --locations 50` |
| `--organizations N` | Number of organizations (planned) | `ip2adb seed --organizations 100` |

### Examples

```bash
# Development setup
./ip2adb seed

# Production-like data
./ip2adb seed --stress

# Quick test
./ip2adb seed --quick

# Add more data without deleting existing
./ip2adb seed --no-truncate --students 500
```

### Time Estimates

| Mode | Duration | Use Case |
|------|----------|----------|
| Quick | 30 seconds | Fast iteration |
| Normal | 2-5 minutes | Daily development |
| Stress | 15-45 minutes | Performance testing |

---

## Command: integrity

**Purpose:** Check database integrity and repair issues

### Basic Usage

```bash
# Check only (read-only)
./ip2adb integrity

# Check and auto-repair
./ip2adb integrity --repair

# Interactive repair (for complex issues)
./ip2adb integrity --interactive

# Preview repairs (dry run)
./ip2adb integrity --repair --dry-run

# Skip file checks (faster)
./ip2adb integrity --no-files

# Export report
./ip2adb integrity --export report.txt
```

### What It Checks

| Category | Checks | Auto-Fix |
|----------|--------|----------|
| **Structural** | Foreign keys, required fields, enums | ✅ |
| **Logical** | Date logic, business rules | ✅ |
| **Quality** | Duplicates, anomalies | ❌ |
| **Files** | Missing files, corrupt data | ⚠️ Interactive |

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--repair` | Auto-fix repairable issues | `ip2adb integrity --repair` |
| `--interactive` | Interactive repair for complex issues | `ip2adb integrity --interactive` |
| `--dry-run` | Preview repairs without committing | `ip2adb integrity --repair --dry-run` |
| `--no-files` | Skip file system checks (faster) | `ip2adb integrity --no-files` |
| `--export FILE` | Export report to file | `ip2adb integrity --export report.txt` |
| `--force` | Force run in production | `ip2adb integrity --force` |

### Examples

```bash
# Daily health check (fast)
./ip2adb integrity --no-files

# Weekly maintenance
./ip2adb integrity --repair

# Deep check with files
./ip2adb integrity --repair --interactive

# Test repairs safely
./ip2adb integrity --repair --dry-run

# Production check (requires --force)
./ip2adb integrity --force --export production_check.txt
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - no critical issues |
| 1 | Critical issues found |
| 130 | Interrupted by user |

---

## Command: load

**Purpose:** Test database performance with concurrent users

### Basic Usage

```bash
# Standard load test (50 users)
./ip2adb load

# Quick test (10 users, fast)
./ip2adb load --quick

# Stress test (200 users)
./ip2adb load --stress

# Custom configuration
./ip2adb load --users 100 --ops 50

# Specific user pattern
./ip2adb load --pattern read_heavy

# Export results
./ip2adb load --export performance.txt
```

### User Patterns

| Pattern | Reads | Writes | Typical User |
|---------|-------|--------|--------------|
| `read_heavy` | 90% | 10% | Viewers, managers, searchers |
| `write_heavy` | 30% | 70% | Data entry staff |
| `mixed` | 60% | 40% | Regular everyday users |
| `file_operations` | 50% | 50% | Document processors |
| `distributed` | Mixed | Mixed | Realistic distribution (default) |

### Options

| Option | Default | Description | Example |
|--------|---------|-------------|---------|
| `--users N` | 50 | Number of concurrent users | `--users 100` |
| `--ops N` | 50 | Operations per user | `--ops 75` |
| `--think-time MS` | 100 | Delay between operations (ms) | `--think-time 200` |
| `--ramp-up SEC` | 10 | Ramp-up time (seconds) | `--ramp-up 20` |
| `--pattern TYPE` | distributed | User behavior pattern | `--pattern read_heavy` |
| `--quick` | - | Quick test: 10 users, 20 ops | `--quick` |
| `--stress` | - | Stress test: 200 users, 100 ops | `--stress` |
| `--export FILE` | - | Export report to file | `--export report.txt` |
| `--force` | - | Force run in production | `--force` |

### Examples

```bash
# Baseline test
./ip2adb load --quick

# Standard test
./ip2adb load --users 50 --ops 50

# Peak load test
./ip2adb load --users 100 --ops 75

# Stress test
./ip2adb load --stress

# Read-only workload
./ip2adb load --users 100 --pattern read_heavy

# Write-heavy workload
./ip2adb load --users 30 --pattern write_heavy

# Sustained load
./ip2adb load --users 50 --ops 500 --think-time 500
```

### Time Estimates

| Configuration | Duration | Use Case |
|---------------|----------|----------|
| Quick (10 users, 20 ops) | 1-2 minutes | Development testing |
| Standard (50 users, 50 ops) | 5-10 minutes | Weekly monitoring |
| Stress (200 users, 100 ops) | 20-30 minutes | Capacity planning |

### Performance Targets

| Metric | Excellent | Good | Fair | Poor |
|--------|-----------|------|------|------|
| Avg Response | < 100ms | < 500ms | < 1000ms | > 1000ms |
| Throughput | > 100 ops/s | > 50 ops/s | > 20 ops/s | < 20 ops/s |
| Success Rate | > 99% | > 95% | > 90% | < 90% |

---

## Command: all

**Purpose:** Run complete test suite (seed + integrity + load)

### Basic Usage

```bash
# Standard test suite
./ip2adb all

# Stress test suite
./ip2adb all --stress

# Quick test suite
./ip2adb all --quick

# Custom configuration
./ip2adb all --stress --users 100 --no-files
```

### What It Does

The `all` command runs three operations in sequence:

1. **Seed** - Populate database with test data
2. **Integrity** - Check data quality and auto-repair
3. **Load** - Test performance under concurrent load

If any step fails, the suite stops and reports the failure.

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--stress` | Use stress test volumes for all | `ip2adb all --stress` |
| `--quick` | Quick mode for all tests | `ip2adb all --quick` |
| `--no-truncate` | Don't truncate in seed step | `ip2adb all --no-truncate` |
| `--no-files` | Skip file checks in integrity | `ip2adb all --no-files` |
| `--users N` | Load test users | `ip2adb all --users 100` |
| `--ops N` | Load test operations | `ip2adb all --ops 75` |
| `--think-time MS` | Load test think time | `ip2adb all --think-time 200` |
| `--ramp-up SEC` | Load test ramp-up | `ip2adb all --ramp-up 15` |
| `--pattern TYPE` | Load test pattern | `ip2adb all --pattern mixed` |
| `--force` | Force run in production | `ip2adb all --force` |

### Examples

```bash
# Pre-deployment validation
./ip2adb all --stress

# Quick validation
./ip2adb all --quick

# Custom suite
./ip2adb all --stress --users 150 --no-files

# Development workflow
./ip2adb all --quick --no-truncate
```

### Time Estimates

| Mode | Duration | Use Case |
|------|----------|----------|
| Quick | 5-10 minutes | Development validation |
| Standard | 15-30 minutes | Weekly testing |
| Stress | 45-90 minutes | Pre-production validation |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All tests passed |
| 1 | One or more tests failed |
| 130 | Interrupted by user |

---

## Command: reset

**Purpose:** Delete all data from database

**⚠️ DANGER: This operation cannot be undone!**

### Basic Usage

```bash
# Reset database (requires confirmation)
./ip2adb reset

# Force reset in production (very dangerous!)
./ip2adb reset --force
```

### What It Does

- Truncates all tables
- Resets auto-increment counters
- Removes all data permanently
- **Does NOT** drop tables or modify schema

### Safety Features

- ✅ Blocked in production (requires `--force`)
- ✅ Requires explicit confirmation
- ✅ User must type "DELETE ALL DATA" to confirm
- ✅ Non-interactive mode skips confirmation (CI/CD)

### When to Use

- Starting fresh after failed migrations
- Cleaning up after testing
- Preparing for new seed data
- Resetting development environment

### Examples

```bash
# Reset and re-seed
./ip2adb reset
./ip2adb seed --stress

# Clean slate for testing
./ip2adb reset && ./ip2adb all --quick
```

---

## Common Workflows

### Daily Development

```bash
# Morning: Fresh start
./ip2adb seed --quick

# After changes: Validate
./ip2adb integrity --no-files
```

### Weekly Maintenance

```bash
# Check database health
./ip2adb integrity --repair --no-files

# Performance test
./ip2adb load --users 50

# If issues found, re-seed
./ip2adb seed --stress
```

### Pre-Deployment

```bash
# Complete validation
./ip2adb all --stress

# Export reports for review
./ip2adb integrity --export integrity_$(date +%Y%m%d).txt
./ip2adb load --stress --export load_$(date +%Y%m%d).txt
```

### Performance Testing

```bash
# Baseline
./ip2adb seed --stress
./ip2adb load --quick

# Progressive load testing
./ip2adb load --users 25
./ip2adb load --users 50
./ip2adb load --users 100
./ip2adb load --users 200
```

### After Data Import

```bash
# Validate imported data
./ip2adb integrity --repair

# Test performance
./ip2adb load --users 50

# Full validation if needed
./ip2adb all --no-truncate --no-files
```

---

## Advanced Usage

### Chaining Commands

```bash
# Reset, seed, and test
./ip2adb reset && ./ip2adb seed --stress && ./ip2adb load --stress

# Quick iteration
./ip2adb seed --quick && ./ip2adb integrity --no-files
```

### Scripting

```bash
#!/bin/bash
# weekly_maintenance.sh

DATE=$(date +%Y%m%d)
LOGDIR="/var/log/ip2adb"
mkdir -p $LOGDIR

# Integrity check
./ip2adb integrity --repair --export $LOGDIR/integrity_$DATE.txt

# Performance test
./ip2adb load --users 50 --export $LOGDIR/load_$DATE.txt

# Alert if issues
if [ $? -ne 0 ]; then
    echo "Database issues detected!" | mail -s "DB Alert" admin@example.com
fi
```

### CI/CD Integration

```yaml
# .github/workflows/database-test.yml
- name: Database Test Suite
  run: |
    ./ip2adb all --quick
```

### Cron Jobs

```bash
# Daily integrity check at 2 AM
0 2 * * * cd /app && ./ip2adb integrity --no-files

# Weekly stress test on Sunday at 3 AM
0 3 * * 0 cd /app && ./ip2adb all --stress

# Monthly performance report on 1st at 4 AM
0 4 1 * * cd /app && ./ip2adb load --stress --export /var/log/perf_$(date +\%Y\%m\%d).txt
```

---

## Troubleshooting

### Command not found

**Problem:**
```bash
./ip2adb seed
bash: ./ip2adb: Permission denied
```

**Solution:**
```bash
chmod +x /app/ip2adb
```

### Import errors

**Problem:**
```bash
ModuleNotFoundError: No module named 'src'
```

**Solution:**
```bash
# Ensure you're in the right directory
cd /app

# Or use full path
/app/ip2adb seed
```

### Production blocked

**Problem:**
```bash
🚨 ERROR: Blocked in production environment
```

**Solution:**
```bash
# If you really need to run in production (dangerous!)
./ip2adb seed --force

# Better: Run in staging first
IP2A_ENV=staging ./ip2adb seed --stress
```

### Out of memory

**Problem:**
```bash
# During stress test
MemoryError: Unable to allocate...
```

**Solution:**
```bash
# Use smaller batches or reduce counts
# Or increase available RAM

# For now, use normal seed instead
./ip2adb seed
```

### Connection timeout

**Problem:**
```bash
# During load test
sqlalchemy.exc.TimeoutError: QueuePool limit...
```

**Solution:**
```bash
# Reduce concurrent users
./ip2adb load --users 25

# Or increase connection pool (src/db/session.py)
SQLALCHEMY_POOL_SIZE = 100
```

---

## Environment Variables

### Supported Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `IP2A_ENV` | Environment (dev/staging/production) | `IP2A_ENV=staging` |
| `DATABASE_URL` | Database connection string | `DATABASE_URL=postgresql://...` |

### Examples

```bash
# Run in staging environment
IP2A_ENV=staging ./ip2adb seed --stress

# Use different database
DATABASE_URL=postgresql://user:pass@host:5432/db ./ip2adb integrity
```

---

## Exit Codes

All commands return standard exit codes:

| Code | Meaning | Example |
|------|---------|---------|
| 0 | Success | Operation completed successfully |
| 1 | Failure | Errors occurred, check output |
| 130 | Interrupted | User pressed Ctrl+C |

Use in scripts:

```bash
./ip2adb seed --stress
if [ $? -eq 0 ]; then
    echo "Seed successful"
    ./ip2adb load --users 100
else
    echo "Seed failed!"
    exit 1
fi
```

---

## Configuration Files

### Current Configuration

All configuration is done through:
- Command-line arguments
- Environment variables
- `src/config/settings.py`

### Planned: Config File (Future)

```yaml
# ip2adb.yml (planned feature)
seed:
  default:
    members: 50
    students: 500
  stress:
    members: 10000
    students: 1000

load:
  default:
    users: 50
    ops: 50
  stress:
    users: 200
    ops: 100
```

---

## Getting Help

### Command Help

```bash
# General help
./ip2adb --help

# Command-specific help
./ip2adb seed --help
./ip2adb integrity --help
./ip2adb load --help
./ip2adb all --help
```

### Documentation

- **This file:** [IP2ADB.md](IP2ADB.md) - Complete reference
- **Stress Test:** [STRESS_TEST.md](STRESS_TEST.md) - Large data volumes
- **Integrity Check:** [INTEGRITY_CHECK.md](INTEGRITY_CHECK.md) - Data quality
- **Load Testing:** [LOAD_TEST.md](LOAD_TEST.md) - Performance testing
- **Testing Strategy:** [TESTING_STRATEGY.md](TESTING_STRATEGY.md) - Overall approach

### Quick Reference

- **[INTEGRITY_QUICK_REF.md](INTEGRITY_QUICK_REF.md)** - Integrity check commands
- **[LOAD_TEST_QUICK_REF.md](LOAD_TEST_QUICK_REF.md)** - Load test commands

### Report Issues

GitHub Issues: https://github.com/theace26/IP2A-Database-v2/issues

---

## Comparison with Old Scripts

### Before (Multiple Scripts)

```bash
# Old way - multiple scripts to remember
python run_stress_test.py
python run_integrity_check.py --repair
python run_load_test.py --users 50
```

### Now (One Tool)

```bash
# New way - one tool, clear commands
./ip2adb seed --stress
./ip2adb integrity --repair
./ip2adb load --users 50

# Or run everything
./ip2adb all --stress
```

### Benefits

✅ **Easier to remember** - One command for everything
✅ **Consistent interface** - All commands work the same way
✅ **Better help** - Built-in documentation
✅ **Safer** - Production protections built-in
✅ **Faster** - Optimized workflows
✅ **Scriptable** - Clean exit codes

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-27 | Initial release |

---

## Future Enhancements

Planned features:

- [ ] Custom data volumes for all entities
- [ ] Configuration file support (YAML)
- [ ] Progress bars for long operations
- [ ] JSON output for parsing
- [ ] Parallel execution for faster tests
- [ ] Docker-compose integration
- [ ] Web interface for results
- [ ] Historical trend tracking
- [ ] Slack/email notifications
- [ ] Cost estimation for cloud databases

---

*Last Updated: January 27, 2026*
*Version: 1.0*
*Status: Production Ready*
