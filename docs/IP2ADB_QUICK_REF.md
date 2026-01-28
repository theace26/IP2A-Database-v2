# ip2adb - Quick Reference Guide

## One Command For Everything

```bash
./ip2adb <command> [options]
```

---

## Commands at a Glance

| Command | What It Does | Common Usage |
|---------|--------------|--------------|
| `seed` | Populate database | `./ip2adb seed` |
| `integrity` | Check data quality | `./ip2adb integrity --repair` |
| `load` | Test performance | `./ip2adb load --users 50` |
| `all` | Run everything | `./ip2adb all --stress` |
| `reset` | Delete all data | `./ip2adb reset` |

---

## Most Common Commands

```bash
# Daily Development
./ip2adb seed                          # Setup dev data
./ip2adb integrity --no-files          # Quick health check

# Weekly Testing
./ip2adb all --quick                   # Fast validation
./ip2adb integrity --repair            # Fix issues

# Pre-Deployment
./ip2adb all --stress                  # Full test suite
./ip2adb load --stress                 # Performance test

# Performance Testing
./ip2adb seed --stress                 # Large dataset
./ip2adb load --users 100              # 100 concurrent users

# Emergency
./ip2adb reset                         # Delete all data
./ip2adb seed --quick                  # Fast recovery
```

---

## Seed Command

### Basic

```bash
./ip2adb seed                          # Normal data (~500 students)
./ip2adb seed --stress                 # Large data (10k members)
./ip2adb seed --quick                  # Minimal data (fast)
./ip2adb seed --no-truncate            # Append, don't delete
```

### Time

| Mode | Duration |
|------|----------|
| Quick | 30 seconds |
| Normal | 2-5 minutes |
| Stress | 15-45 minutes |

---

## Integrity Command

### Basic

```bash
./ip2adb integrity                     # Check only
./ip2adb integrity --repair            # Check and fix
./ip2adb integrity --no-files          # Fast check (skip files)
./ip2adb integrity --repair --dry-run  # Preview fixes
./ip2adb integrity --interactive       # Handle missing files
```

### Export

```bash
./ip2adb integrity --export report.txt
./ip2adb integrity --export report_$(date +%Y%m%d).txt
```

### Time

| Mode | Duration |
|------|----------|
| No files | 2-5 minutes |
| With files | 10-30 minutes |

---

## Load Command

### Basic

```bash
./ip2adb load                          # 50 users (standard)
./ip2adb load --quick                  # 10 users (fast)
./ip2adb load --stress                 # 200 users (heavy)
./ip2adb load --users 100              # Custom user count
```

### Patterns

```bash
./ip2adb load --pattern read_heavy     # 90% reads
./ip2adb load --pattern write_heavy    # 70% writes
./ip2adb load --pattern mixed          # 60% reads, 40% writes
```

### Time

| Mode | Duration |
|------|----------|
| Quick (10 users) | 1-2 minutes |
| Standard (50 users) | 5-10 minutes |
| Stress (200 users) | 20-30 minutes |

---

## All Command

### Basic

```bash
./ip2adb all                           # Full suite (standard)
./ip2adb all --stress                  # Full suite (stress)
./ip2adb all --quick                   # Full suite (fast)
```

### Time

| Mode | Duration |
|------|----------|
| Quick | 5-10 minutes |
| Standard | 15-30 minutes |
| Stress | 45-90 minutes |

---

## Reset Command

### Basic

```bash
./ip2adb reset                         # Delete all (requires confirm)
```

**⚠️ DANGER:** Cannot be undone!

---

## Option Reference

### Global Options

| Option | What It Does |
|--------|--------------|
| `--help` | Show help for command |
| `--force` | Force run in production |

### Seed Options

| Option | Example | Description |
|--------|---------|-------------|
| `--stress` | `seed --stress` | Large volumes |
| `--quick` | `seed --quick` | Minimal data |
| `--no-truncate` | `seed --no-truncate` | Append data |
| `--members N` | `seed --members 5000` | Custom count (planned) |
| `--students N` | `seed --students 1000` | Custom count (planned) |

### Integrity Options

| Option | Example | Description |
|--------|---------|-------------|
| `--repair` | `integrity --repair` | Auto-fix issues |
| `--interactive` | `integrity --interactive` | Manual fixes |
| `--dry-run` | `integrity --dry-run` | Preview only |
| `--no-files` | `integrity --no-files` | Skip file checks |
| `--export FILE` | `integrity --export r.txt` | Save report |

### Load Options

| Option | Example | Description |
|--------|---------|-------------|
| `--users N` | `load --users 100` | Concurrent users |
| `--ops N` | `load --ops 50` | Operations per user |
| `--quick` | `load --quick` | 10 users, 20 ops |
| `--stress` | `load --stress` | 200 users, 100 ops |
| `--pattern TYPE` | `load --pattern read_heavy` | User behavior |
| `--export FILE` | `load --export perf.txt` | Save report |

---

## Workflows

### Development Setup

```bash
# 1. Fresh start
./ip2adb reset

# 2. Seed dev data
./ip2adb seed

# 3. Verify
./ip2adb integrity --no-files
```

### Weekly Maintenance

```bash
# 1. Health check
./ip2adb integrity --repair --no-files

# 2. Performance test
./ip2adb load --users 50

# 3. If issues, re-seed
./ip2adb seed --stress
```

### Pre-Deployment

```bash
# 1. Full validation
./ip2adb all --stress

# 2. Export reports
./ip2adb integrity --export integrity_$(date +%Y%m%d).txt
./ip2adb load --stress --export load_$(date +%Y%m%d).txt
```

### Performance Testing

```bash
# 1. Large dataset
./ip2adb seed --stress

# 2. Progressive load
./ip2adb load --users 25
./ip2adb load --users 50
./ip2adb load --users 100
./ip2adb load --users 200
```

---

## Cheat Sheet

```bash
# Setup
./ip2adb seed                          # Dev data
./ip2adb seed --stress                 # Production-like data
./ip2adb seed --quick                  # Fast data

# Check
./ip2adb integrity                     # Health check
./ip2adb integrity --repair            # Fix issues
./ip2adb integrity --no-files          # Fast check

# Test
./ip2adb load                          # Performance test
./ip2adb load --quick                  # Fast test
./ip2adb load --stress                 # Heavy test

# All-in-One
./ip2adb all                           # Everything (standard)
./ip2adb all --stress                  # Everything (production-ready)
./ip2adb all --quick                   # Everything (fast)

# Emergency
./ip2adb reset                         # Delete all data
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Failed |
| 130 | Cancelled (Ctrl+C) |

Use in scripts:

```bash
if ./ip2adb seed --stress; then
    echo "Success!"
    ./ip2adb load --users 100
else
    echo "Failed!"
    exit 1
fi
```

---

## Tips

### Speed Up Development

```bash
# Fast iteration
./ip2adb seed --quick
./ip2adb integrity --no-files
./ip2adb load --quick
```

### Save Time

```bash
# Skip confirmation
yes | ./ip2adb reset

# Chain commands
./ip2adb reset && ./ip2adb seed --stress
```

### Debugging

```bash
# Dry run repairs
./ip2adb integrity --repair --dry-run

# Export for analysis
./ip2adb integrity --export debug.txt
./ip2adb load --export perf.txt
```

---

## Common Errors

### "Permission denied"

```bash
chmod +x /app/ip2adb
```

### "Blocked in production"

```bash
# If you really need to (dangerous!)
./ip2adb seed --force
```

### "Connection timeout"

```bash
# Reduce load
./ip2adb load --users 25
```

### "Out of memory"

```bash
# Use normal seed instead
./ip2adb seed
```

---

## Get More Help

```bash
# General help
./ip2adb --help

# Command help
./ip2adb seed --help
./ip2adb integrity --help
./ip2adb load --help
./ip2adb all --help
```

**Full Documentation:** [IP2ADB.md](IP2ADB.md)

---

## Quick Comparison

### Old Way (Multiple Scripts)

```bash
python run_stress_test.py
python run_integrity_check.py --repair
python run_load_test.py --users 50
```

### New Way (One Tool)

```bash
./ip2adb seed --stress
./ip2adb integrity --repair
./ip2adb load --users 50

# Or just:
./ip2adb all --stress
```

✅ **Easier to remember**
✅ **One consistent interface**
✅ **Built-in help**
✅ **Production protection**

---

*Quick Reference v1.0*
