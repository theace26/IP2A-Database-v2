# CLAUDE.md - IP2A-Database-v2

> This file provides context for Claude Code. Place in your repository root.

---

## ⚠️ COORDINATION REMINDER

**Claude Code:** After completing work, remind the user:
> "Don't forget to update Claude.ai with our progress! Share a summary of what we accomplished."

**Claude.ai:** After planning sessions, remind the user:
> "Update CLAUDE.md with any decisions made here so Claude Code has the context."

This bidirectional sync keeps both Claudes aligned on project state.

---

## Project Overview

**IP2A-Database-v2** is a production-grade data platform for managing pre-apprenticeship program data, expanding into workplace organization member management.

**Repository:** https://github.com/theace26/IP2A-Database-v2
**Local Path:** `~/Projects/IP2A-Database-v2` (alias: `$IP2A`)
**Owner:** Xerxes
**Status:** v0.2.0 Released - Phase 1 Complete, Phase 2 Planned

---

## Git Workflow

### Current State (January 27, 2026 - Updated)
```
main (v0.2.0) ─── ✅ Phase 1 MERGED & TAGGED
    │
    └── feature/phase1-services ─── Merged to main

Next: feature/phase2-operations ─── SALTing, Benevolence, Grievances
```

### Tags
| Tag | Description | Status |
|-----|-------------|--------|
| `v0.2.0` | Phase 1 Complete: Services + DB Tools | ✅ Current |
| `v0.1.1` | Stabilized src layout and project structure | Released |
| `v0.1.0` | Backend stabilization complete | Released |

### Commands
```bash
# Set project shortcut (add to ~/.zshrc)
export IP2A=~/Projects/IP2A-Database-v2

# Current branch (main at v0.2.0)
cd $IP2A && git status

# Start Phase 2
git checkout -b feature/phase2-operations
git push -u origin feature/phase2-operations

# After completing Phase 2, merge to main
git checkout main
git merge feature/phase2-operations -m "Complete Phase 2: SALTing, Benevolence, Grievances"
git tag -a v0.3.0 -m "v0.3.0 - Phase 2 complete"
git push origin main --tags
```

---

## Architecture

### Tech Stack
- **Backend:** Python 3.12, FastAPI
- **Database:** PostgreSQL 16, SQLAlchemy (sync)
- **Schemas:** Pydantic v2
- **Testing:** pytest, httpx
- **Code Quality:** Ruff, pre-commit hooks
- **Environment:** Docker + Devcontainer

### Project Structure
```
IP2A-Database-v2/
├── src/
│   ├── config/              # Configuration
│   ├── db/
│   │   ├── enums/           # ALL enums consolidated here
│   │   │   ├── __init__.py  # Exports all enums
│   │   │   ├── base_enums.py        # Education/training enums
│   │   │   └── organization_enums.py # Union operations enums
│   │   ├── migrations/      # Alembic migrations
│   │   ├── base.py
│   │   ├── mixins.py        # TimestampMixin, SoftDeleteMixin
│   │   └── session.py
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic (CRUD)
│   ├── routers/             # FastAPI endpoints
│   ├── seed/                # Seed data
│   └── tests/               # pytest tests
├── .devcontainer/
│   └── devcontainer.json
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── alembic.ini
└── CLAUDE.md                # This file
```

---

## Current State

### Verified Working ✅
| Component | Status |
|-----------|--------|
| Python 3.12.12 | ✅ |
| PostgreSQL 16.11 | ✅ Connected |
| File Sync (container ↔ local) | ✅ |
| All 12 models import | ✅ |
| All enums import | ✅ (after fix) |
| Migrations at head | ✅ |
| Seed data | ✅ 510 students, 54 instructors |
| Existing schemas | ✅ |

### Phase 1 Services Layer - ✅ COMPLETE (v0.2.0)

| Component | Organization | OrgContact | Member | MemberEmployment | AuditLog |
|-----------|:------------:|:----------:|:------:|:----------------:|:--------:|
| Model     | ✅           | ✅         | ✅     | ✅               | ✅       |
| Schema    | ✅           | ✅         | ✅     | ✅               | ✅       |
| Service   | ✅           | ✅         | ✅     | ✅               | ✅*      |
| Router    | ✅           | ✅         | ✅     | ✅               | ✅*      |
| Tests     | ✅ (7 tests) | ✅ (7 tests)| ✅ (9 tests) | ✅ (7 tests) | ✅ (5 tests) |

*AuditLog is immutable - read-only endpoints, no update/delete.
**Total: 51 tests passing** (35 Phase 1 + 16 Phase 0)
**Released:** January 27, 2026 as v0.2.0

---

## Implementation Patterns

### Enum Import (IMPORTANT)
```python
# ✅ CORRECT - Import from src.db.enums
from src.db.enums import CohortStatus, MemberStatus, OrganizationType

# ❌ WRONG - Don't import from src.models.enums (deprecated)
from src.models.enums import CohortStatus  # Will show deprecation warning
```

### Schema Pattern
```python
# src/schemas/{model}.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ModelBase(BaseModel):
    name: str
    description: Optional[str] = None

class ModelCreate(ModelBase):
    pass

class ModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ModelRead(ModelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

### Service Pattern
```python
# src/services/{model}_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
from src.models import Model
from src.schemas.model import ModelCreate, ModelUpdate

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
# src/routers/{models}.py (plural filename)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.schemas.model import ModelCreate, ModelUpdate, ModelRead
from src.services.model_service import (
    create_model, get_model, list_models, update_model, delete_model
)

router = APIRouter(prefix="/models", tags=["Models"])

@router.post("/", response_model=ModelRead)
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

@router.delete("/{model_id}")
def delete(model_id: int, db: Session = Depends(get_db)):
    if not delete_model(db, model_id):
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Deleted"}
```

### Naming Conventions
| Component | Pattern | Example |
|-----------|---------|---------|
| Model | Singular, PascalCase | `Organization` |
| Schema | Singular + Suffix | `OrganizationCreate` |
| Service | `{model}_service.py` | `organization_service.py` |
| Router | Plural | `organizations.py` |
| Test | `test_{models}.py` | `test_organizations.py` |

---

## Development Commands

### Testing & Quality
```bash
# Run all tests
cd $IP2A && pytest -v

# Run specific test
pytest src/tests/test_students.py -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Lint and format
ruff check . --fix && ruff format .
```

### Database Management (via ip2adb) ⭐ RECOMMENDED
```bash
# Seed database
./ip2adb seed                      # Normal seed (500 students)
./ip2adb seed --stress             # Stress test (10k members, 250k employments)
./ip2adb seed --quick              # Quick seed (minimal data)

# Check database health
./ip2adb integrity                 # Check data quality
./ip2adb integrity --repair        # Auto-fix issues
./ip2adb integrity --no-files      # Fast check (skip file checks)

# Test performance
./ip2adb load                      # Load test (50 users)
./ip2adb load --quick              # Quick test (10 users)
./ip2adb load --stress             # Stress test (200 users)
./ip2adb load --users 100          # Custom user count

# Complete test suite
./ip2adb all                       # Run everything
./ip2adb all --stress              # Full suite with stress volumes

# Emergency
./ip2adb reset                     # Delete all data (dangerous!)
```

### Database Management (Legacy Scripts)
```bash
# Normal seed
python -m src.seed.run_seed

# Stress test
python run_stress_test.py

# Integrity check
python run_integrity_check.py --repair

# Load test
python run_load_test.py --quick
```

### Migrations
```bash
# Run migrations
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "description"
```

### Verification
```bash
# Verify models
python -c "from src.models import Organization, Member, FileAttachment; print('✅ OK')"

# Verify enums
python -c "from src.db.enums import MemberStatus, OrganizationType; print('✅ OK')"
```

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Enum location | `src/db/enums/` only | Prevents circular imports |
| Member vs Student | Separate tables, linked FK | Different lifecycles |
| Salting Score | 1-5 integer scale | Simple, clear criteria |
| AuditLog | Immutable, insert-only | Legal compliance |
| File sync | Full project mount | All files sync bidirectionally |

---

## Troubleshooting

### Circular Import Error
If you see `ImportError: cannot import name 'X' from partially initialized module`:
- Ensure all imports use `from src.db.enums import ...`
- Never import from `src.models.enums`

### Container Not Syncing Files
```bash
# Verify mount
docker exec ip2a-api ls -la /app

# Restart container
cd $IP2A && docker-compose down && docker-compose up -d
```

### Tests Won't Run
```bash
# Install missing deps
pip install httpx pytest-cov
```

---

## Roadmap

### Phase 1: Services Layer - ✅ COMPLETE (v0.2.0 - January 27, 2026)
- [x] Fix circular import (enum consolidation)
- [x] Update requirements.txt (add httpx)
- [x] Schemas for Phase 1 models (5 models)
- [x] Services for Phase 1 models (CRUD operations)
- [x] Routers for Phase 1 models (FastAPI endpoints)
- [x] Tests for Phase 1 models (35 tests, all passing)
- [x] Database management tools (ip2adb CLI)
- [x] Stress test system (10k members, 250k employments, 150k files)
- [x] Integrity check system (validation + auto-repair)
- [x] Load test system (concurrent user simulation)
- [x] Complete documentation (10+ guides, 5000+ lines)
- [x] **Merged to main, tagged v0.2.0, pushed to remote**

### Phase 2: Union Operations - 📋 PLANNED (Next)
**Target:** SALTing activities, Benevolence Fund, Grievance management
**Plan Location:** `/root/.claude/plans/sharded-cuddling-cherny.md`

**Models to Build:**
- [ ] SALTingActivity - Track organizing efforts at non-union employers
- [ ] BenevolenceApplication - Financial assistance requests
- [ ] BenevolenceReview - Multi-level approval workflow (VP/Admin/Manager/President)
- [ ] Grievance - Formal complaint tracking through arbitration

**Scope:**
- [ ] 4 new models with enums
- [ ] 27+ API endpoints
- [ ] 28+ tests
- [ ] Seed data for all models
- [ ] Migration: `alembic revision --autogenerate -m "Add Phase 2"`
- [ ] Target: v0.3.0 release

### Future Phases
- Phase 3: Document management, S3 (file storage)
- Phase 4: Dues tracking (financial)
- Phase 5: TradeSchool integration (external system)
- Phase 6: Web portal, deployment (production launch)

---

## Session Handoff Checklist

When switching between Claude.ai and Claude Code:

**From Claude.ai → Claude Code:**
- [ ] CLAUDE.md updated with decisions
- [ ] Git branch correct
- [ ] Any blockers documented

**From Claude Code → Claude.ai:**
- [ ] Summary of changes made
- [ ] Tests passing? (yes/no)
- [ ] Any issues encountered
- [ ] Next steps identified

---

## Session Summary (January 27, 2026)

### ✅ Completed Today
1. **Claude Code Persistence** - Configured and verified
   - VSCode server data persists across container rebuilds
   - Extension auto-installs on rebuild
   - Workspace settings tracked in git

2. **Phase 1 → Main** - Successfully merged and released
   - Merged `feature/phase1-services` → `main`
   - Tagged as **v0.2.0**
   - Pushed to remote repository

3. **Database Tools Tested**
   - `./ip2adb seed --quick` - ✅ Working (500 students, 50 members, 20 orgs)
   - `./ip2adb integrity --no-files` - ✅ Working (1 minor warning found)
   - `./ip2adb load --quick --users 5` - ✅ Working (10ms avg response)

4. **Phase 2 Planned**
   - Comprehensive implementation plan created
   - 4 models: SALTingActivity, BenevolenceApplication, BenevolenceReview, Grievance
   - 27 endpoints, 28 tests planned
   - Ready to begin implementation

### 📊 Current State
- **Branch:** main
- **Tag:** v0.2.0
- **Tests:** 51 passing
- **Next:** Begin Phase 2 implementation

---

*Last Updated: January 27, 2026 (Evening)*
*Working Branch: main (at v0.2.0)*
*Next Task: Create feature/phase2-operations branch and begin Phase 2 implementation*

---

## Cross-Platform Setup

### Required on Each New Machine

**.env.compose** - Not in git (contains credentials). Create from template:
```bash
# Mac/Linux
cp .env.compose.example .env.compose

# Windows PowerShell
Copy-Item .env.compose.example .env.compose
```

### Path Shortcuts

| OS | Command | Path |
|----|---------|------|
| Mac | `` | `~/Projects/IP2A-Database-v2` |
| Windows | `C:\Users\Xerxes\Projects\IP2A-Database-v2` | `~\Projects\IP2A-Database-v2` |

Add to shell profile:
- **Mac** (~/.zshrc): `export IP2A=~/Projects/IP2A-Database-v2`
- **Windows** (D:\OneDrive\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1): `C:\Users\Xerxes\Projects\IP2A-Database-v2 = "C:\Users\Xerxes\Projects\IP2A-Database-v2"`

### Switching Machines Workflow
```bash
# Before leaving current machine
git add -A && git commit -m "WIP: current state" && git push

# On new machine
git pull
# Ensure .env.compose exists (copy from .env.compose.example if needed)
docker-compose up -d
# VS Code: Ctrl/Cmd+Shift+P → "Dev Containers: Reopen in Container"
```
