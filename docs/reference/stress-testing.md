# Stress Test Documentation

## Overview

The stress test seed system populates the database with large-scale realistic data to test database performance, query optimization, and application scalability.

## Data Volumes

| Entity | Count | Notes |
|--------|-------|-------|
| **Members** | 10,000 | Union members with complete profiles |
| **Member Employments** | ~250,000+ | Each member: 1-100 jobs, 20% employer repeat |
| **File Attachments** | ~150,000+ | Photos, PDFs, documents (~30 GB total) |
| **Students** | 1,000 | Complete student records |
| **Instructors** | 500 | Full instructor profiles |
| **Locations** | 250 | Training locations across regions |
| **Organizations** | 200 | 150 employers, 50 unions/training partners |
| **Organization Contacts** | ~600 | 2-4 contacts per organization |

## Features

### Member Employment Records
- **1-100 jobs per member** (weighted distribution towards fewer jobs)
- **20% employer repeat rate** - Members return to previous employers realistically
- **Complete date ranges** - Start dates, end dates, current employment tracking
- **Varied hourly rates** - $18-$75/hr range with realistic cents
- **Job titles** - 11 different electrician job titles
- **20-year history** - Employment records span last 20 years

### File Attachments (~30 GB simulated storage)
- **Members: 10-25 files each** (minimum 10 required documents)
  - ID photos (12MP, 2.5-5.5 MB)
  - Scanned licenses and certifications (0.2-2 MB PDFs)
  - Training certificates and reports (0.5-5 MB PDFs)
  - Forms and applications (50-500 KB PDFs)
  - Resumes and documents (100 KB - 2 MB)
  - Work site photos (2-6 MB)
- **Students: 5-15 files each**
  - Application documents, forms, ID photos, certificates
- **Organizations: 2-10 files each**
  - Contracts, licenses, business documents
- **Grievances: 1-50 files each** (simulated, 50-200 grievances)
  - Statements, evidence photos, correspondence
  - Most have 5-15 files, some complex cases up to 50 files
- **Realistic file types**: JPEG photos, PDF documents, Word docs, Excel spreadsheets
- **Realistic file sizes**: Based on actual document/photo specifications

### Data Quality
- **Realistic distributions** - Most members are active journeymen
- **Optional fields populated** - 60-90% fill rates on optional data
- **Diverse member numbers** - Numeric, alphanumeric, letter-prefixed formats
- **Geographic diversity** - Locations and addresses across all US states
- **Contact information** - Emails, phones, addresses where appropriate

## Running the Stress Test

### Method 1: Direct Python Script (Recommended)

```bash
# Run with database truncation (starts fresh)
python run_stress_test.py

# Run without truncation (appends to existing data)
python run_stress_test.py --no-truncate
```

### Method 2: Python Module

```bash
# With truncation
python -m src.seed.stress_test_seed

# Without truncation
python -m src.seed.stress_test_seed --no-truncate
```

### Method 3: From Python Console

```python
from src.seed.stress_test_seed import run_stress_test

# With truncation
run_stress_test(truncate=True)

# Without truncation
run_stress_test(truncate=False)
```

## Execution Time

Expect **15-45 minutes** depending on hardware:
- Fast NVMe SSD: ~15-25 minutes
- Standard SSD: ~20-35 minutes
- HDD or remote DB: ~30-45 minutes

**Note:** File attachments add ~5-15 minutes to the total time.

### Progress Indicators

The script provides real-time progress:
```
📍 Phase 1: Locations and Instructors
   ✅ Seeded 250 locations
   ✅ Seeded 500 instructors

🏢 Phase 2: Organizations
   ✅ Seeded 200 organizations (150 employers)

👤 Phase 3: Organization Contacts
   ✅ Seeded 600 organization contacts

🎓 Phase 4: Students
   ✅ Seeded 1,000 students

👷 Phase 5: Members (This will take a while...)
   1000/10000 members generated...
   2000/10000 members generated...
   ...
   ✅ Seeded 10,000 members

💼 Phase 6: Member Employments (This will take even longer...)
   1000/10000 members processed (25,432 records generated)...
   2000/10000 members processed (52,891 records generated)...
   ...
   ✅ Seeded 247,583 member employment records

📎 Phase 7: File Attachments (This will take a while too...)
   Processing 10000 members (10+ files each)...
   1000/10000 members processed...
   ...
   ✅ Generated 120000+ files for members
   ✅ Generated ~10000 files for students
   ✅ Seeded 152,847 file attachments
   📊 Storage breakdown:
      • Members: 120,000 files (~29.5 GB)
      • Students: 10,000 files (~1.5 GB)
      • Organizations: 1,000 files
      • Grievances: ~15,000 files
      • Total size: 32.14 GB
```

## Testing Scenarios

### Performance Testing

```python
# Test query performance with large datasets
from sqlalchemy.orm import Session
from src.db.session import get_db_session
from src.models import Member, MemberEmployment

db = get_db_session()

# Query a member with many jobs
member = db.query(Member).first()
employments = db.query(MemberEmployment).filter(
    MemberEmployment.member_id == member.id
).all()
print(f"Member has {len(employments)} jobs")

# Test pagination
members_page1 = db.query(Member).limit(100).all()
members_page2 = db.query(Member).offset(100).limit(100).all()
```

### API Testing

```bash
# Test API with large result sets
curl "http://localhost:8000/members/?limit=100"
curl "http://localhost:8000/member-employments/by-member/1"

# Test pagination
curl "http://localhost:8000/organizations/?skip=0&limit=50"
curl "http://localhost:8000/organizations/?skip=50&limit=50"
```

### Database Query Analysis

```sql
-- Check record counts
SELECT
    'members' as table_name, COUNT(*) as count FROM members
UNION ALL
SELECT 'member_employments', COUNT(*) FROM member_employments
UNION ALL
SELECT 'students', COUNT(*) FROM students
UNION ALL
SELECT 'instructors', COUNT(*) FROM instructors
UNION ALL
SELECT 'locations', COUNT(*) FROM locations
UNION ALL
SELECT 'organizations', COUNT(*) FROM organizations;

-- Find members with most jobs
SELECT
    m.id,
    m.first_name,
    m.last_name,
    COUNT(me.id) as job_count
FROM members m
LEFT JOIN member_employments me ON m.id = me.member_id
GROUP BY m.id, m.first_name, m.last_name
ORDER BY job_count DESC
LIMIT 10;

-- Employer frequency (20% repeat rate verification)
SELECT
    o.name,
    COUNT(DISTINCT me.member_id) as unique_members,
    COUNT(me.id) as total_employments,
    ROUND(COUNT(me.id)::numeric / COUNT(DISTINCT me.member_id), 2) as avg_times_per_member
FROM member_employments me
JOIN organizations o ON me.organization_id = o.id
GROUP BY o.id, o.name
HAVING COUNT(me.id) > 100
ORDER BY total_employments DESC
LIMIT 20;
```

## Cleanup

To remove stress test data and return to normal seed:

```bash
# Run normal seed (this truncates and re-seeds with normal volumes)
python -m src.seed.run_seed
```

## Files

| File | Purpose |
|------|---------|
| `run_stress_test.py` | Main runner script (root level) |
| `src/seed/stress_test_seed.py` | Orchestrates the stress test |
| `src/seed/stress_test_members.py` | Generates 10,000 members |
| `src/seed/stress_test_member_employments.py` | Generates ~250k employments |
| `src/seed/stress_test_students.py` | Generates 1,000 students |
| `src/seed/stress_test_instructors.py` | Generates 500 instructors |
| `src/seed/stress_test_locations.py` | Generates 250 locations |
| `src/seed/stress_test_organizations.py` | Generates 200 organizations |
| `src/seed/stress_test_organization_contacts.py` | Generates org contacts |

## Safety Features

- ✅ **Production protection** - Blocked in production environment
- ✅ **Confirmation prompts** - Requires explicit "yes" for truncation
- ✅ **Progress indicators** - Real-time feedback during long operations
- ✅ **Batch processing** - Efficient bulk inserts in batches
- ✅ **Session management** - Proper commit/flush to prevent memory issues

## Notes

- The 20% employer repeat rate is probabilistic, not exact
- Job counts per member follow a triangular distribution (weighted towards fewer jobs)
- Most members (88%) are ACTIVE status
- Most members (65%) have a current job
- Journeymen represent 40% of classifications
- 70% of employers have salting score data
- All optional fields are filled 60-90% of the time for realism

## Troubleshooting

**Issue**: Script runs out of memory
- **Solution**: Reduce batch sizes in stress test files, or run with more RAM

**Issue**: Database connection timeout
- **Solution**: Increase connection timeout in database settings

**Issue**: Taking too long
- **Solution**: Normal for large datasets. Check progress indicators. Consider reducing counts in stress_test_seed.py.

**Issue**: Disk space full
- **Solution**: Ensure adequate disk space (recommend 10GB+ free)
