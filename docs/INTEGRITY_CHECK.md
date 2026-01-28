# Database Integrity Check & Repair System

## Overview

The integrity check system validates database consistency, detects issues, and provides automated or interactive repair capabilities. Designed for multi-user production environments where data integrity is critical.

## Key Features

### 🔍 Comprehensive Checks

1. **Structural Integrity**
   - Foreign key validation (orphaned records)
   - Required field verification
   - Enum value validation

2. **Logical Consistency**
   - Date logic (end_date > start_date, etc.)
   - Employment logic (multiple current jobs, rate ranges)
   - Contact logic (multiple primary contacts)

3. **Data Quality**
   - Duplicate detection (member numbers, emails)
   - Data anomalies (active members with no jobs)
   - Outlier detection

4. **File System Integrity**
   - File path validation
   - File existence verification
   - File size validation
   - Missing file detection

### 🔧 Repair Capabilities

| Issue Type | Auto-Repair | Interactive | Manual |
|------------|-------------|-------------|--------|
| Orphaned records | ✅ | - | - |
| Invalid enums | ✅ | - | - |
| Date logic errors | ✅ | - | - |
| Multiple primary contacts | ✅ | - | - |
| Missing files | - | ✅ | - |
| Duplicates | - | - | ✅ |
| Missing required fields | - | - | ✅ |

### 🛡️ Safety Features

- ✅ **Dry run mode** - Preview changes before committing
- ✅ **Production protection** - Requires --force flag in production
- ✅ **Transaction rollback** - All changes rolled back on error
- ✅ **Detailed logging** - Full audit trail of all changes
- ✅ **Interactive prompts** - User confirmation for destructive actions

---

## Usage

### Basic Integrity Check (Read-Only)

```bash
# Run all checks, no repairs
python run_integrity_check.py

# Skip file system checks (faster)
python run_integrity_check.py --no-files

# Export report to file
python run_integrity_check.py --export integrity_report.txt
```

**Output:**
```
🔍 Running Database Integrity Checks
============================================================

📋 Category 1: Structural Integrity
   Checking foreign key integrity...
      ✓ Foreign key check complete
   Checking required fields...
      ✓ Required field check complete
   ...

============================================================
📊 INTEGRITY CHECK REPORT
============================================================

🔴 Critical Issues: 5
🟡 Warnings: 12
🔵 Info: 8
   Total Issues: 25

🔧 Auto-fixable: 15/25
```

### Automatic Repair

```bash
# Dry run - preview repairs without making changes
python run_integrity_check.py --repair --dry-run

# Execute auto-repairs
python run_integrity_check.py --repair
```

**Auto-repairs include:**
- Deleting orphaned records
- Fixing invalid enum values
- Correcting date logic issues
- Fixing multiple primary contacts
- Removing file attachments with no path

### Interactive Repair

```bash
# Interactively handle complex issues
python run_integrity_check.py --interactive
```

**Example interactive session:**
```
📎 Interactive File Repair
============================================================
Found 3 file attachment issues requiring manual review

📄 File Attachment #1234
   Type: member
   Record ID: 567
   Original Name: license_scan.pdf
   Path: uploads/member/2024/03/abc123def456.pdf
   Size: 2,450,000 bytes
   Description: Scanned license

Options:
  1) Delete this attachment record
  2) Keep record (maybe file will be restored later)
  3) Skip (decide later)
  4) Delete ALL remaining file attachment issues
  5) Keep ALL remaining records
  6) Abort repair

Choice (1-6): 2
   ℹ️  Kept record
```

### Combined Approach

```bash
# Auto-repair fixable issues, then interactive for complex ones
python run_integrity_check.py --repair --interactive

# Dry run both
python run_integrity_check.py --repair --interactive --dry-run
```

---

## Check Categories

### 1. Structural Integrity

#### Foreign Key Integrity
Detects orphaned records that reference non-existent parent records.

**Checks:**
- Member employments → Members
- Member employments → Organizations
- Organization contacts → Organizations
- File attachments → Parent records (members, students, organizations)

**Auto-fix:** Delete orphaned records

**Example Issue:**
```
🔴 Employment record 12345 references non-existent member
   → Auto-fix: delete
```

#### Required Fields
Ensures all mandatory fields are populated.

**Checks:**
- Members: member_number, first_name, last_name
- Organizations: name, org_type
- Students: first_name, last_name, email

**Auto-fix:** ❌ Requires manual data entry

**Example Issue:**
```
🔴 Member 789 missing required field(s)
```

#### Enum Values
Validates that enum fields contain only valid values.

**Checks:**
- Member status (active, inactive, suspended, etc.)
- Member classification (journeyman, apprentice_1, etc.)
- Organization type (employer, union, training_partner, jatc)
- Salting score (1-5)

**Auto-fix:** Set to default value (e.g., ACTIVE for status)

**Example Issue:**
```
🔴 Member 456 has invalid status: ACTVE (typo)
   → Auto-fix: set to 'active'
```

### 2. Logical Consistency

#### Date Logic
Validates date relationships and ranges.

**Checks:**
- Employment end_date >= start_date
- is_current=True must have end_date=NULL
- hire_date not in future
- Reasonable date ranges

**Auto-fix:** Set end_date to NULL or is_current to False

**Example Issue:**
```
🔴 Employment 999 has end_date before start_date
   → Auto-fix: set end_date to NULL
```

#### Employment Logic
Validates employment-specific business rules.

**Checks:**
- Members should have 0 or 1 current employment (not multiple)
- Hourly rates in reasonable range ($10-$150)
- Employment history makes sense

**Auto-fix:** ❌ Requires manual review

**Example Issue:**
```
🟡 Member 123 has 3 current employments (should be 0 or 1)
```

#### Contact Logic
Validates organization contact relationships.

**Checks:**
- Organizations should have 0 or 1 primary contact (not multiple)
- Organizations should have at least 1 contact (info only)

**Auto-fix:** Keep most recent as primary, set others to non-primary

**Example Issue:**
```
🟡 Organization 50 has 2 primary contacts (should be 0 or 1)
   → Auto-fix: keep most recent as primary
```

### 3. Data Quality

#### Duplicates
Detects duplicate records that should be unique.

**Checks:**
- Duplicate member numbers
- Duplicate student emails
- Duplicate organization names (info only)

**Auto-fix:** ❌ Requires manual deduplication

**Example Issue:**
```
🔴 Duplicate member_number: 7001234 (3 records)
```

#### Data Anomalies
Identifies unusual patterns that may indicate issues.

**Checks:**
- Active members with no employment history
- Unusually high/low hourly rates
- Missing optional data that's usually present

**Auto-fix:** ❌ Info only

**Example Issue:**
```
🔵 250 active members have no employment history
```

### 4. File System Integrity

#### File Attachments
Validates file attachment records and file system.

**Checks:**
- File path exists and is not NULL
- Referenced files exist on disk (local storage)
- File sizes are reasonable (<100 MB)
- File extensions match MIME types

**Auto-fix:**
- ✅ Delete records with no file_path
- ⚠️ Interactive for missing files (user decides: delete, keep, or reattach)

**Example Issue:**
```
🟡 Attachment 5678 file not found: uploads/member/2024/03/missing.pdf
   → Requires interactive repair (user decision)
```

**Note:** File system checks can be slow for large datasets (100k+ attachments). Use `--no-files` to skip.

---

## Repair Process

### Auto-Repair Flow

1. **Identify Issues** - Run all integrity checks
2. **Filter Auto-Fixable** - Select issues with automated fixes
3. **Group by Category** - Organize repairs logically
4. **Execute Repairs** - Apply fixes in order
5. **Commit Changes** - Save all changes in single transaction
6. **Generate Report** - Summarize actions taken

### Interactive Repair Flow

1. **Identify Complex Issues** - Filter issues requiring user input
2. **Present Options** - Show details and available actions
3. **User Decides** - Choose: delete, keep, skip, or batch action
4. **Execute Action** - Apply user's choice
5. **Repeat** - Continue until all issues resolved or user aborts
6. **Commit Changes** - Save all interactive decisions

### Dry Run Mode

Dry run mode allows you to preview repairs without making changes:

```bash
python run_integrity_check.py --repair --dry-run
```

**Behavior:**
- All checks run normally
- Repair logic executes
- Changes are **NOT** committed to database
- Session is rolled back at end
- Report shows what **would** be done

**Output:**
```
⚠️  DRY RUN MODE - No changes will be made

🔧 Starting Auto-Repair Process
...
✅ Fixed: Employment record 12345 references non-existent member
   → Would delete orphaned record

⚠️  Dry run complete - no changes made
```

---

## Scheduled Maintenance

### Recommended Schedule

For multi-user production environments:

```bash
# Daily integrity check (read-only, no repairs)
0 2 * * * cd /app && python run_integrity_check.py --export /var/log/integrity_daily.txt

# Weekly auto-repair during maintenance window
0 3 * * 0 cd /app && python run_integrity_check.py --repair --no-files

# Monthly full check with file system (slower)
0 4 1 * * cd /app && python run_integrity_check.py --repair
```

### Pre-Deployment Checklist

Before deploying to production:

1. ✅ Run integrity check on staging data
2. ✅ Review and fix all critical issues
3. ✅ Test auto-repair with --dry-run
4. ✅ Document any manual fixes needed
5. ✅ Schedule downtime for repairs if needed

### Post-Import Validation

After importing large datasets:

```bash
# Check data quality immediately
python run_integrity_check.py

# Auto-repair common import issues
python run_integrity_check.py --repair --dry-run
python run_integrity_check.py --repair
```

---

## Multi-User Considerations

### Concurrent Access

The integrity checker is designed for multi-user environments:

- **Read operations** - Safe to run while users are active
- **Repair operations** - Require exclusive access or maintenance window
- **Interactive repairs** - Best during low-activity periods

### Locking Strategy

During repairs:
- Uses row-level locks (not table locks)
- Commits in single transaction (all or nothing)
- Minimal disruption to other users
- Fast repair operations (< 1 second per fix)

### Best Practices

1. **Run checks frequently** (daily read-only)
2. **Schedule repairs during maintenance** (weekly/monthly)
3. **Monitor critical issues** (alert if count increases)
4. **Keep audit logs** (export reports to files)
5. **Test repairs on staging** (before production)

---

## Examples

### Example 1: Daily Health Check

```bash
#!/bin/bash
# daily_health_check.sh

DATE=$(date +%Y%m%d)
REPORT_DIR="/var/log/integrity_reports"

# Run check and export report
python run_integrity_check.py \
    --no-files \
    --export "$REPORT_DIR/integrity_$DATE.txt"

# Count critical issues
CRITICAL=$(grep "🔴 Critical Issues:" "$REPORT_DIR/integrity_$DATE.txt" | awk '{print $4}')

# Alert if critical issues found
if [ "$CRITICAL" -gt 0 ]; then
    echo "⚠️  Found $CRITICAL critical integrity issues"
    # Send alert (email, Slack, etc.)
fi
```

### Example 2: Weekly Auto-Repair

```bash
#!/bin/bash
# weekly_repair.sh

# Test repairs first
python run_integrity_check.py --repair --dry-run --no-files

# If dry run looks good, execute
read -p "Execute repairs? (yes/no): " CONFIRM

if [ "$CONFIRM" = "yes" ]; then
    python run_integrity_check.py --repair --no-files
    echo "✅ Weekly repair complete"
else
    echo "❌ Repair cancelled"
fi
```

### Example 3: Post-Import Validation

```bash
#!/bin/bash
# validate_import.sh

# After data import, check integrity
python run_integrity_check.py --export import_validation.txt

# Review report
cat import_validation.txt

# Fix auto-fixable issues
python run_integrity_check.py --repair

# Check again to confirm
python run_integrity_check.py
```

---

## Troubleshooting

### Issue: Check is too slow

**Cause:** File system checks on large datasets (100k+ attachments)

**Solution:**
```bash
# Skip file checks
python run_integrity_check.py --no-files
```

### Issue: Too many orphaned records

**Cause:** Data import without proper foreign key validation

**Solution:**
```bash
# Auto-delete orphaned records
python run_integrity_check.py --repair
```

### Issue: Repairs fail with database locked

**Cause:** Other users have locks on records being repaired

**Solution:**
- Schedule repairs during maintenance window
- Ask users to log out temporarily
- Check `pg_stat_activity` for blocking queries

### Issue: Duplicate member numbers

**Cause:** Import process allowed duplicates

**Solution:**
Manual deduplication required:
1. Export duplicates to CSV
2. Review with business team
3. Merge or delete duplicates manually
4. Re-run integrity check

---

## API Integration

### Python Integration

```python
from src.db.session import get_db_session
from src.db.integrity_check import IntegrityChecker
from src.db.integrity_repair import IntegrityRepairer

# Run checks programmatically
db = get_db_session()
checker = IntegrityChecker(db)
issues = checker.run_all_checks(check_files=False)

# Auto-repair
if issues:
    repairer = IntegrityRepairer(db, dry_run=False)
    actions = repairer.repair_all_auto_fixable(issues)

# Get report
report = checker.generate_report()
print(report)
```

### Monitoring Integration

```python
from src.db.integrity_check import IntegrityChecker

def check_database_health():
    """Check database health and return metrics."""
    db = get_db_session()
    checker = IntegrityChecker(db)
    issues = checker.run_all_checks(check_files=False)

    critical = len([i for i in issues if i.severity == "critical"])
    warnings = len([i for i in issues if i.severity == "warning"])

    return {
        "status": "healthy" if critical == 0 else "degraded",
        "critical_issues": critical,
        "warning_issues": warnings,
        "total_issues": len(issues)
    }
```

---

## Safety Checklist

Before running repairs in production:

- [ ] Backup database first
- [ ] Run with --dry-run to preview changes
- [ ] Review all auto-fix actions
- [ ] Schedule during maintenance window
- [ ] Notify users of downtime (if needed)
- [ ] Monitor database logs during repair
- [ ] Verify repair results with follow-up check
- [ ] Keep repair reports for audit trail

---

## File Reference

| File | Purpose |
|------|---------|
| `run_integrity_check.py` | CLI runner (root level) |
| `src/db/integrity_check.py` | Checker implementation |
| `src/db/integrity_repair.py` | Repair implementation |
| `INTEGRITY_CHECK.md` | This documentation |

---

*Last Updated: January 27, 2026*
*Version: 1.0*
*Status: Production Ready*
