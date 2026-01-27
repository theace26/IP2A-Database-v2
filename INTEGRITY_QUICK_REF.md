# Database Integrity Check - Quick Reference

## Common Commands

### Daily Operations

```bash
# Quick health check (2-5 minutes)
python run_integrity_check.py --no-files

# Full check with files (10-30 minutes)
python run_integrity_check.py

# Export report
python run_integrity_check.py --export report_$(date +%Y%m%d).txt
```

### Repair Operations

```bash
# Preview repairs (safe)
python run_integrity_check.py --repair --dry-run

# Auto-repair (commits changes)
python run_integrity_check.py --repair

# Interactive repair for complex issues
python run_integrity_check.py --interactive

# Combined: auto + interactive
python run_integrity_check.py --repair --interactive
```

### Production

```bash
# Force run in production (use with caution)
python run_integrity_check.py --force

# Dry run in production (safe)
python run_integrity_check.py --force --repair --dry-run
```

## What Gets Checked

| Category | Check | Severity | Auto-Fix |
|----------|-------|----------|----------|
| **Structural** | Orphaned records | 🔴 Critical | ✅ Yes |
| **Structural** | Missing required fields | 🔴 Critical | ❌ No |
| **Structural** | Invalid enum values | 🔴 Critical | ✅ Yes |
| **Logical** | Date logic errors | 🔴 Critical | ✅ Yes |
| **Logical** | Multiple current jobs | 🟡 Warning | ❌ No |
| **Logical** | Multiple primary contacts | 🟡 Warning | ✅ Yes |
| **Quality** | Duplicate records | 🔴 Critical | ❌ No |
| **Quality** | Data anomalies | 🔵 Info | ❌ No |
| **Files** | Missing file path | 🔴 Critical | ✅ Yes |
| **Files** | File not found | 🟡 Warning | ⚠️ Interactive |

## Quick Fixes

### Fix All Auto-Fixable Issues
```bash
python run_integrity_check.py --repair
```

### Fix Orphaned Records Only
```bash
# Check first
python run_integrity_check.py | grep "orphaned"

# Auto-fix
python run_integrity_check.py --repair
```

### Handle Missing Files
```bash
# Interactive mode lets you decide per file
python run_integrity_check.py --interactive
```

### Fix Duplicate Primary Contacts
```bash
python run_integrity_check.py --repair
# Keeps most recent contact as primary
```

## Typical Workflow

### Weekly Maintenance
```bash
# 1. Check current state
python run_integrity_check.py --no-files

# 2. Preview repairs
python run_integrity_check.py --repair --dry-run

# 3. Execute repairs
python run_integrity_check.py --repair

# 4. Verify
python run_integrity_check.py --no-files
```

### After Data Import
```bash
# 1. Full check with files
python run_integrity_check.py

# 2. Auto-fix common issues
python run_integrity_check.py --repair

# 3. Handle duplicates manually
# Review report for duplicates, deduplicate manually

# 4. Final check
python run_integrity_check.py
```

### Emergency Fix
```bash
# Production database has issues
# 1. Check severity
python run_integrity_check.py --force --no-files

# 2. Test fix
python run_integrity_check.py --force --repair --dry-run

# 3. Execute if safe
python run_integrity_check.py --force --repair
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - no critical issues |
| 1 | Critical issues remain |
| 130 | Interrupted by user (Ctrl+C) |

## Time Estimates

| Operation | With Files | Without Files |
|-----------|------------|---------------|
| **Check only** | 10-30 min | 2-5 min |
| **Auto-repair** | 10-35 min | 3-7 min |
| **Interactive** | 15-60 min | N/A |

*Times based on 10k members, 250k employments, 150k file attachments*

## Scheduled Automation

### Cron Examples

```bash
# Daily health check at 2 AM
0 2 * * * cd /app && python run_integrity_check.py --no-files --export /var/log/integrity_daily.txt

# Weekly repair on Sunday at 3 AM
0 3 * * 0 cd /app && python run_integrity_check.py --repair --no-files

# Monthly full check on 1st at 4 AM
0 4 1 * * cd /app && python run_integrity_check.py --repair
```

### Bash Script

```bash
#!/bin/bash
# daily_check.sh

DATE=$(date +%Y%m%d)
LOGDIR="/var/log/integrity"
mkdir -p $LOGDIR

python run_integrity_check.py --no-files --export "$LOGDIR/check_$DATE.txt"

# Alert if critical issues
if grep -q "🔴 Critical Issues: [1-9]" "$LOGDIR/check_$DATE.txt"; then
    echo "Critical integrity issues found!" | mail -s "DB Alert" admin@example.com
fi
```

## Troubleshooting

### "Database is locked"
- Schedule during maintenance window
- Check for long-running queries: `SELECT * FROM pg_stat_activity;`

### "Check is too slow"
- Use `--no-files` to skip file system checks
- Run during off-peak hours

### "Permission denied"
- Make script executable: `chmod +x run_integrity_check.py`
- Check database permissions

### "Blocked in production"
- Add `--force` flag (use with caution)
- Consider running on staging first

## Need Help?

- Full documentation: `INTEGRITY_CHECK.md`
- Help text: `python run_integrity_check.py --help`
- Report issues: GitHub Issues
