# IP2A-Database-v2 Continuity Document

**Purpose:** Copy and paste this document into a new Claude Code thread to provide full project context.

**Last Updated:** 2026-01-27

---

## Project Overview

**Repository:** IP2A-Database-v2
**Location:** `/app` (Docker container) or `~/Projects/IP2A-Database-v2` (local)
**Purpose:** Production-grade data platform for pre-apprenticeship program data + union member management
**Status:** Phase 1 complete - Building services layer
**Current Branch:** `feature/phase1-services`
**Main Branch:** `main`
**Latest Tag:** `v0.1.1`

### Tech Stack
- **Backend:** Python 3.12, FastAPI
- **Database:** PostgreSQL 16, SQLAlchemy (sync)
- **Schemas:** Pydantic v2
- **Testing:** pytest, httpx
- **Code Quality:** Ruff, pre-commit hooks
- **Environment:** Docker + Devcontainer

---

## Current State

### ✅ Phase 1 Models Complete (All Working)

| Model | Status | Location |
|-------|--------|----------|
| Organization | ✅ | `src/models/organization.py` |
| OrganizationContact | ✅ | `src/models/organization_contact.py` |
| Member | ✅ | `src/models/member.py` |
| MemberEmployment | ✅ | `src/models/member_employment.py` |
| AuditLog | ✅ | `src/models/audit_log.py` |
| FileAttachment | ✅ | `src/models/file_attachment.py` |

### ✅ Phase 1 Services/Routers Complete

All Phase 1 models have:
- ✅ Pydantic schemas (Create, Update, Read)
- ✅ Service layer (CRUD operations)
- ✅ FastAPI routers
- ✅ Tests (51 tests passing)

### ✅ Complete Testing Suite Created

**Three major testing systems:**
1. **Stress Test** - Large data volumes (10k members, 250k employments)
2. **Integrity Check** - Data quality validation and repair
3. **Load Test** - Concurrent user simulation (up to 500 users)

### ✅ Unified CLI Tool Created

**ip2adb** - One tool for all database operations

---

## Database Structure

### Enum Location (CRITICAL)
**Always import from:** `from src.db.enums import ...`
**Never import from:** `src.models.enums` (deprecated, causes circular imports)

```python
# ✅ CORRECT
from src.db.enums import (
    MemberStatus, MemberClassification, OrganizationType,
    SaltingScore, CohortStatus, EnrollmentStatus
)

# ❌ WRONG
from src.models.enums import MemberStatus  # Will fail
```

### Enum Files
- `src/db/enums/base_enums.py` - Education/training enums
- `src/db/enums/organization_enums.py` - Union operations enums
- `src/db/enums/__init__.py` - Consolidated exports

### Key Enum Values (Lowercase in Database)
```python
# MemberStatus
MemberStatus.ACTIVE.value = "active"
MemberStatus.INACTIVE.value = "inactive"

# OrganizationType
OrganizationType.EMPLOYER.value = "employer"
OrganizationType.UNION.value = "union"

# MemberClassification
MemberClassification.JOURNEYMAN.value = "journeyman"
MemberClassification.APPRENTICE_1.value = "apprentice_1"

# SaltingScore (1-5 scale)
SaltingScore.HOSTILE.value = 1
SaltingScore.NEUTRAL.value = 3
SaltingScore.FRIENDLY.value = 5
```

### Database Session
```python
from src.db.session import get_db_session

db = get_db_session()
# Use db for queries
db.close()
```

### Connection Pool Settings
```python
# src/db/session.py
SQLALCHEMY_POOL_SIZE = 20  # Can increase for load testing
SQLALCHEMY_MAX_OVERFLOW = 40
```

---

## Testing Tools

### 1. ip2adb - Unified CLI Tool ⭐ PRIMARY TOOL

**Location:** `/app/ip2adb` (executable)

**Commands:**
```bash
./ip2adb seed                      # Normal seed (500 students)
./ip2adb seed --stress             # Stress test (10k members, 250k employments)
./ip2adb seed --quick              # Quick seed (minimal data)

./ip2adb integrity                 # Check data quality
./ip2adb integrity --repair        # Auto-fix issues
./ip2adb integrity --no-files      # Fast check (skip files)

./ip2adb load                      # Load test (50 users)
./ip2adb load --quick              # Quick test (10 users)
./ip2adb load --stress             # Stress test (200 users)
./ip2adb load --users 100          # Custom user count

./ip2adb all                       # Run everything (seed + integrity + load)
./ip2adb all --stress              # Full suite with stress volumes

./ip2adb reset                     # Delete all data (dangerous!)
```

**Documentation:**
- [IP2ADB.md](IP2ADB.md) - Complete guide
- [IP2ADB_QUICK_REF.md](IP2ADB_QUICK_REF.md) - Quick reference

### 2. Stress Test System

**Purpose:** Test database with large data volumes

**Generates:**
- 10,000 members
- ~250,000 member employments (1-100 jobs per member, 20% repeat rate)
- ~150,000 file attachments (~30 GB simulated)
- 1,000 students
- 500 instructors
- 250 locations
- 200 organizations (150 employers, 50 others)

**Files:**
- `run_stress_test.py` - Main runner
- `src/seed/stress_test_seed.py` - Orchestrator
- `src/seed/stress_test_*.py` - Individual generators
- [STRESS_TEST.md](STRESS_TEST.md) - Documentation

**Usage:**
```bash
python run_stress_test.py
# Or: ./ip2adb seed --stress
```

**Duration:** 15-45 minutes

### 3. Integrity Check System

**Purpose:** Validate data quality and repair issues

**Checks:**
- ✅ Foreign key integrity (orphaned records)
- ✅ Required fields
- ✅ Enum values
- ✅ Date logic (end_date >= start_date, etc.)
- ✅ Business rules (multiple current jobs, etc.)
- ✅ Duplicates
- ✅ File attachments

**Auto-Fixable Issues:**
- Orphaned records (deleted)
- Invalid enums (set to default)
- Date logic errors (corrected)
- Multiple primary contacts (keep most recent)

**Requires Manual Fix:**
- Duplicates
- Missing required fields
- Missing files (interactive mode)

**Files:**
- `run_integrity_check.py` - Main runner
- `src/db/integrity_check.py` - Checker
- `src/db/integrity_repair.py` - Repairer
- [INTEGRITY_CHECK.md](INTEGRITY_CHECK.md) - Documentation
- [INTEGRITY_QUICK_REF.md](INTEGRITY_QUICK_REF.md) - Quick reference

**Usage:**
```bash
python run_integrity_check.py --repair
# Or: ./ip2adb integrity --repair
```

**Duration:** 5-30 minutes (depending on --no-files flag)

### 4. Load Test System

**Purpose:** Simulate concurrent users for performance testing

**Simulates:**
- 10-500 concurrent users
- Realistic read/write operations
- Multiple user patterns:
  - **Read-heavy** (90% reads) - Viewers, searchers
  - **Write-heavy** (70% writes) - Data entry
  - **Mixed** (60% reads, 40% writes) - Typical users
  - **File operations** - Document processing

**Measures:**
- Response times (avg, median, p95, p99)
- Throughput (operations per second)
- Success rate
- Per-operation performance

**Files:**
- `run_load_test.py` - Main runner
- `src/tests/load_test.py` - Implementation
- [LOAD_TEST.md](LOAD_TEST.md) - Documentation
- [LOAD_TEST_QUICK_REF.md](LOAD_TEST_QUICK_REF.md) - Quick reference

**Usage:**
```bash
python run_load_test.py --quick
# Or: ./ip2adb load --quick
```

**Duration:** 1-30 minutes (depending on configuration)

**Recent Test Results:**
- 10 users: 19ms avg response, 17 ops/sec, 82% success rate
- Current capacity: ~50 concurrent users
- Target: 4000 concurrent users (need 80x improvement)

---

## Key Files and Locations

### Models
```
src/models/
├── organization.py          # Organizations (employers, unions, etc.)
├── organization_contact.py  # Contacts at organizations
├── member.py                # Union members
├── member_employment.py     # Member job history
├── audit_log.py             # Immutable audit trail
├── file_attachment.py       # File attachments (polymorphic)
├── student.py               # Pre-apprentice students
├── instructor.py            # Instructors
├── location.py              # Training locations
└── __init__.py              # Must include FileAttachment
```

### Schemas
```
src/schemas/
├── organization.py          # OrganizationCreate, Update, Read
├── organization_contact.py
├── member.py
├── member_employment.py
├── audit_log.py
└── file_attachment.py
```

### Services
```
src/services/
├── organization_service.py  # CRUD operations
├── organization_contact_service.py
├── member_service.py
├── member_employment_service.py
└── audit_log_service.py     # Read-only (no update/delete)
```

### Routers
```
src/routers/
├── organizations.py         # /organizations endpoints
├── organization_contacts.py # /organization-contacts endpoints
├── members.py               # /members endpoints
├── member_employments.py    # /member-employments endpoints
└── audit_logs.py            # /audit-logs endpoints (read-only)
```

### Database
```
src/db/
├── enums/
│   ├── __init__.py          # Consolidated enum exports
│   ├── base_enums.py        # Education/training enums
│   └── organization_enums.py # Union operations enums
├── migrations/              # Alembic migrations
├── base.py                  # SQLAlchemy Base
├── mixins.py                # TimestampMixin, SoftDeleteMixin
├── session.py               # Database session
├── integrity_check.py       # Integrity checker
└── integrity_repair.py      # Integrity repairer
```

### Seeding
```
src/seed/
├── run_seed.py                      # Normal seed orchestrator
├── stress_test_seed.py              # Stress test orchestrator
├── stress_test_members.py           # 10k members
├── stress_test_member_employments.py # 250k employments
├── stress_test_file_attachments.py  # 150k files
├── stress_test_students.py          # 1k students
├── stress_test_instructors.py       # 500 instructors
├── stress_test_locations.py         # 250 locations
├── stress_test_organizations.py     # 200 orgs
└── stress_test_organization_contacts.py
```

### Tests
```
src/tests/
├── test_organizations.py    # Organization tests (7 tests)
├── test_members.py           # Member tests (7 tests)
├── test_member_employments.py # Employment tests (7 tests)
├── test_organization_contacts.py # Contact tests (7 tests)
├── test_audit_logs.py        # Audit log tests (7 tests)
├── load_test.py              # Load testing implementation
└── ... (existing tests)
```

### Root Scripts
```
/app/
├── ip2adb                   # ⭐ Unified CLI tool
├── run_stress_test.py       # Stress test runner
├── run_integrity_check.py   # Integrity check runner
├── run_load_test.py         # Load test runner
└── main.py                  # FastAPI application
```

---

## Common Operations

### Running Tests
```bash
# All tests
pytest -v

# Specific test file
pytest src/tests/test_organizations.py -v

# With coverage
pytest --cov=src --cov-report=term-missing
```

### Database Operations
```bash
# Run migrations
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "description"

# Normal seed
python -m src.seed.run_seed

# Stress test seed
python run_stress_test.py
# Or: ./ip2adb seed --stress
```

### Starting FastAPI Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Swagger UI:** http://localhost:8000/docs
**ReDoc:** http://localhost:8000/redoc

### Checking Imports
```bash
# Verify all models import
python -c "from src.models import Organization, Member, FileAttachment; print('✅ OK')"

# Verify all enums import
python -c "from src.db.enums import MemberStatus, OrganizationType; print('✅ OK')"
```

---

## Important Patterns

### Schema Pattern
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ModelBase(BaseModel):
    """Base fields for create and read."""
    name: str = Field(..., max_length=255)

class ModelCreate(ModelBase):
    """Fields for creating."""
    pass

class ModelUpdate(BaseModel):
    """Fields for updating (all optional)."""
    name: Optional[str] = Field(None, max_length=255)

class ModelRead(ModelBase):
    """Fields for reading (includes DB fields)."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

### Service Pattern
```python
from sqlalchemy.orm import Session
from typing import List, Optional

def create_model(db: Session, data: ModelCreate) -> Model:
    obj = Model(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_model(db: Session, model_id: int) -> Optional[Model]:
    return db.query(Model).filter(Model.id == model_id).first()

def list_models(db: Session, skip: int = 0, limit: int = 100) -> List[Model]:
    return db.query(Model).offset(skip).limit(limit).all()

def update_model(db: Session, model_id: int, data: ModelUpdate) -> Optional[Model]:
    obj = get_model(db, model_id)
    if not obj:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj

def delete_model(db: Session, model_id: int) -> bool:
    obj = get_model(db, model_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
```

### Router Pattern
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.schemas.model import ModelCreate, ModelUpdate, ModelRead
from src.services.model_service import (
    create_model, get_model, list_models, update_model, delete_model
)

router = APIRouter(prefix="/models", tags=["Models"])

@router.post("/", response_model=ModelRead, status_code=201)
def create(data: ModelCreate, db: Session = Depends(get_db)):
    return create_model(db, data)

@router.get("/{model_id}", response_model=ModelRead)
def read(model_id: int, db: Session = Depends(get_db)):
    obj = get_model(db, model_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return obj

@router.get("/", response_model=list[ModelRead])
def list_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return list_models(db, skip, limit)

@router.put("/{model_id}", response_model=ModelRead)
def update(model_id: int, data: ModelUpdate, db: Session = Depends(get_db)):
    obj = update_model(db, model_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return obj

@router.delete("/{model_id}", status_code=204)
def delete(model_id: int, db: Session = Depends(get_db)):
    if not delete_model(db, model_id):
        raise HTTPException(status_code=404, detail="Not found")
    return None
```

### Naming Conventions
- **Model:** Singular, PascalCase (`Organization`)
- **Schema:** Singular + Suffix (`OrganizationCreate`)
- **Service:** `{model}_service.py` (`organization_service.py`)
- **Router:** Plural (`organizations.py`)
- **Test:** `test_{models}.py` (`test_organizations.py`)

---

## Known Issues and Solutions

### Issue: Enum Import Error
**Symptom:** `ImportError: cannot import name 'X' from partially initialized module`

**Solution:**
```python
# ✅ Use this
from src.db.enums import MemberStatus

# ❌ Not this
from src.models.enums import MemberStatus
```

### Issue: Enum Value Mismatch
**Symptom:** `invalid input value for enum: "ACTIVE"`

**Solution:** Database stores lowercase values:
```python
# Query with lowercase
db.query(Member).filter(Member.status == "active")  # ✅

# Or use enum .value
db.query(Member).filter(Member.status == MemberStatus.ACTIVE.value)  # ✅
```

### Issue: FileAttachment Import Error
**Symptom:** `cannot import name 'FileAttachment' from 'src.models'`

**Solution:** Ensure `src/models/__init__.py` includes:
```python
from src.models.file_attachment import FileAttachment

__all__ = [
    # ... other models ...
    "FileAttachment",
]
```

### Issue: Connection Pool Exhausted
**Symptom:** `QueuePool limit of size X overflow Y reached`

**Solution:** Increase pool size in `src/db/session.py`:
```python
SQLALCHEMY_POOL_SIZE = 40
SQLALCHEMY_MAX_OVERFLOW = 60
```

---

## Performance Baselines

### Current Performance (10 users)
- **Avg Response Time:** 19ms (Excellent)
- **95th Percentile:** 35ms
- **Throughput:** 17 ops/sec
- **Success Rate:** 82% (needs improvement)

### Target Performance (4000 users)
- **Avg Response Time:** <500ms
- **Throughput:** >200 ops/sec
- **Success Rate:** >99%

### Scaling Strategy
1. **Database Optimization** (2-5x) - Indexes, query optimization
2. **Connection Pooling** (2-3x) - Increase pool size
3. **Read Replicas** (2-3x) - Route reads to replicas
4. **Caching Layer** (3-5x) - Redis for sessions/static data
5. **Horizontal Scaling** (3-5x) - Multiple app servers

**Total Estimated:** 96x improvement (sufficient for 4000 users)

---

## Documentation Index

### Primary Documentation
- [CLAUDE.md](CLAUDE.md) - Project context (read first!)
- [DATABASE_TOOLS_OVERVIEW.md](DATABASE_TOOLS_OVERVIEW.md) - All tools overview
- [IP2ADB.md](IP2ADB.md) - Unified CLI tool guide
- [TESTING_STRATEGY.md](TESTING_STRATEGY.md) - Testing approach

### Quick References
- [IP2ADB_QUICK_REF.md](IP2ADB_QUICK_REF.md) - Quick commands
- [INTEGRITY_QUICK_REF.md](INTEGRITY_QUICK_REF.md) - Integrity commands
- [LOAD_TEST_QUICK_REF.md](LOAD_TEST_QUICK_REF.md) - Load test commands

### Specialized Guides
- [STRESS_TEST.md](STRESS_TEST.md) - Large data volumes
- [INTEGRITY_CHECK.md](INTEGRITY_CHECK.md) - Data quality
- [LOAD_TEST.md](LOAD_TEST.md) - Performance testing

### Setup Guides
- [README.md](README.md) - Project README
- [.devcontainer/README.md](.devcontainer/README.md) - Dev container setup

---

## Environment Setup

### Required Environment Variables
```bash
IP2A_ENV=dev              # dev/staging/production
DATABASE_URL=postgresql://user:pass@host:5432/db
```

### Docker Compose
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Rebuild
docker-compose down && docker-compose up -d --build
```

### Devcontainer
```bash
# VS Code: Reopen in Container
# Ctrl/Cmd+Shift+P → "Dev Containers: Reopen in Container"
```

---

## Next Steps / TODO

### Immediate Tasks
- [ ] Run integrity check to identify any issues
- [ ] Run load test to establish performance baseline
- [ ] Add database indexes for performance
- [ ] Implement caching for frequently accessed data

### Future Phases
- [ ] Phase 2: SALTing activities
- [ ] Phase 3: Benevolence, Grievances
- [ ] Phase 4: Document management, S3
- [ ] Phase 5: Dues tracking
- [ ] Phase 6: TradeSchool integration
- [ ] Phase 7: Web portal, deployment

---

## Quick Command Reference

```bash
# Setup
./ip2adb seed --quick                  # Fast dev setup
./ip2adb seed --stress                 # Production-like data

# Daily
./ip2adb integrity --no-files          # Health check
pytest -v                              # Run tests

# Weekly
./ip2adb integrity --repair            # Fix issues
./ip2adb load --users 50               # Performance test

# Pre-Deploy
./ip2adb all --stress                  # Full validation

# Development
uvicorn main:app --reload              # Start API server
alembic upgrade head                   # Run migrations
pytest --cov=src                       # Test with coverage
```

---

## Contact / Support

- **GitHub Issues:** https://github.com/theace26/IP2A-Database-v2/issues
- **Documentation:** All *.md files in `/app`
- **Help:** `./ip2adb --help` or `./ip2adb <command> --help`

---

## Version Info

- **Project Version:** v0.1.1
- **Python:** 3.12.12
- **PostgreSQL:** 16.11
- **FastAPI:** Latest
- **SQLAlchemy:** 2.x (sync)
- **Pydantic:** v2

---

**End of Continuity Document**

**To use:** Copy this entire document and paste it into a new Claude Code thread with the message:
"Here's the current state of the project. Please read this continuity document to understand the codebase."

Then Claude Code will have full context to continue working on your project!
