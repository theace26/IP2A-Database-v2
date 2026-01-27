# CLAUDE.md - IP2A-Database-v2

> This file provides context for Claude Code. Place in your repository root.

---

## ⚠️ COORDINATION REMINDER

**Claude Code:** After completing work, remind the user:
> "Don't forget to update Claude.ai with our progress! Share a summary of what we accomplished."

**Claude.ai:** After planning sessions, remind the user:
> "Update CLAUDE.md with any decisions made here so Claude Code has the context."

This bidirectional sync keeps both Claudes aligned on project state.

### 📝 CHANGELOG REQUIREMENT

**IMPORTANT:** Both Claude.ai and Claude Code MUST add a timestamped entry to the Changelog section at the bottom of this file whenever making updates. Format:

```
| YYYY-MM-DD HH:MM | [Claude.ai/Claude Code] | Brief description of changes |
```

This creates an audit trail of all project decisions and changes.

---

## Project Overview

**IP2A-Database-v2** is a production-grade data platform for managing pre-apprenticeship program data, expanding into workplace organization member management.

**Repository:** https://github.com/theace26/IP2A-Database-v2
**Local Path (Mac):** `~/Projects/IP2A-Database-v2` (alias: `$IP2A`)
**Local Path (Windows):** `~\Projects\IP2A-Database-v2` (alias: `$env:IP2A`)
**Owner:** Xerxes
**Status:** Phase 1 Models Complete, Building Services Layer

---

## Git Workflow

### Current State (January 2026)
```
main (v0.1.1) ─── Stable baseline
    │
    └── feature/phase1-services ─── ACTIVE BRANCH
        └── Phase 1 models + devcontainer fixes
```

### Tags
| Tag | Description |
|-----|-------------|
| `v0.1.1` | Stabilized src layout and project structure |
| `v0.1.0` | Backend stabilization complete |

### Commands
```bash
# Set project shortcut
# Mac (~/.zshrc):
export IP2A=~/Projects/IP2A-Database-v2

# Windows (PowerShell $PROFILE):
$env:IP2A = "$HOME\Projects\IP2A-Database-v2"

# Switch to working branch
cd $IP2A  # or cd $env:IP2A on Windows
git checkout feature/phase1-services

# After completing phase, merge to main
git checkout main
git merge feature/phase1-services -m "Complete Phase 1 services layer"
git tag -a v0.2.0 -m "v0.2.0 - Phase 1 complete"
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
├── .env.compose             # NOT in git - create from .env.compose.example
├── .env.compose.example     # Template for .env.compose
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
| All enums import | ✅ |
| Migrations at head | ✅ |
| Seed data | ✅ 510 students, 54 instructors |
| Existing schemas | ✅ |
| Tests passing | ✅ 16 tests |

### Phase 1 Services Layer - IN PROGRESS

| Component | Organization | OrgContact | Member | MemberEmployment | AuditLog |
|-----------|:------------:|:----------:|:------:|:----------------:|:--------:|
| Model     | ✅           | ✅         | ✅     | ✅               | ✅       |
| Schema    | ⬜ TODO      | ⬜ TODO    | ⬜ TODO | ⬜ TODO         | ⬜ TODO  |
| Service   | ⬜ TODO      | ⬜ TODO    | ⬜ TODO | ⬜ TODO         | ⬜ TODO* |
| Router    | ⬜ TODO      | ⬜ TODO    | ⬜ TODO | ⬜ TODO         | ⬜ TODO* |
| Tests     | ⬜ TODO      | ⬜ TODO    | ⬜ TODO | ⬜ TODO         | ⬜ TODO  |

*AuditLog is immutable - read-only endpoints, no update/delete.

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
from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)
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

```bash
# Run all tests
pytest -v

# Run specific test
pytest src/tests/test_students.py -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Lint and format
ruff check . --fix && ruff format .

# Run migrations
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "description"

# Run seed
python -m src.seed.run_seed

# Verify models
python -c "from src.models import Organization, Member; print('✅ OK')"

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
| Mac | `$IP2A` | `~/Projects/IP2A-Database-v2` |
| Windows | `$env:IP2A` | `~\Projects\IP2A-Database-v2` |

Add to shell profile:
- **Mac** (~/.zshrc): `export IP2A=~/Projects/IP2A-Database-v2`
- **Windows** ($PROFILE): `$env:IP2A = "$HOME\Projects\IP2A-Database-v2"`

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

### Windows-Specific Setup

1. **Enable PowerShell scripts:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Install prerequisites:**
   ```powershell
   winget install Git.Git
   winget install Docker.DockerDesktop
   winget install Microsoft.VisualStudioCode
   code --install-extension ms-vscode-remote.remote-containers
   ```

3. **Configure Git (same identity as Mac):**
   ```powershell
   git config --global user.name "Xerxes"
   git config --global user.email "your-email@example.com"
   git config --global core.autocrlf input
   ```

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
docker-compose down && docker-compose up -d
```

### Tests Won't Run
```bash
# Install missing deps
pip install httpx pytest-cov
```

### Windows: .env.compose Not Found
```powershell
# Create from template
Copy-Item .env.compose.example .env.compose
```

### Windows: Devcontainer Won't Start
1. Ensure Docker Desktop is running
2. Check WSL 2 is enabled: `wsl --status`
3. Verify Docker is in Linux mode: `docker info | Select-String "OSType"`

---

## Roadmap

### Current: Phase 1 Services (feature/phase1-services)
- [x] Fix circular import (enum consolidation)
- [x] Update requirements.txt (add httpx)
- [x] Rebuild devcontainer
- [x] Cross-platform setup (Mac + Windows)
- [ ] Schemas for new models
- [ ] Services for new models
- [ ] Routers for new models
- [ ] Tests for new models
- [ ] Merge to main, tag v0.2.0

### Future Phases
- Phase 2: SALTing activities
- Phase 3: Benevolence, Grievances
- Phase 4: Document management, S3
- Phase 5: Dues tracking
- Phase 6: TradeSchool integration
- Phase 7: Web portal, deployment

---

## Session Handoff Checklist

When switching between Claude.ai and Claude Code:

**From Claude.ai → Claude Code:**
- [ ] CLAUDE.md updated with decisions
- [ ] Changelog entry added
- [ ] Git branch correct
- [ ] Any blockers documented

**From Claude Code → Claude.ai:**
- [ ] Summary of changes made
- [ ] Changelog entry added
- [ ] Tests passing? (yes/no)
- [ ] Any issues encountered
- [ ] Next steps identified

---

## Changelog

> **INSTRUCTIONS FOR CLAUDE.AI AND CLAUDE CODE:**
> Add a new row to this table every time you make changes to this file or the project.
> Use UTC timezone. Format: `YYYY-MM-DD HH:MM UTC`

| Timestamp | Source | Description |
|-----------|--------|-------------|
| 2026-01-26 06:00 UTC | Claude.ai | Initial CLAUDE.md created with project context |
| 2026-01-26 08:30 UTC | Claude.ai | Fixed circular imports, consolidated enums to src/db/enums/ |
| 2026-01-26 09:00 UTC | Claude.ai | Added devcontainer fixes, updated Dockerfile and docker-compose.yml |
| 2026-01-27 06:30 UTC | Claude.ai | Added cross-platform setup (Windows), .env.compose.example template |
| 2026-01-27 07:00 UTC | Claude.ai | Added changelog requirement and audit trail instructions |

---

*Working Branch: feature/phase1-services*
*Next Task: Build schemas, services, routers for Phase 1 models*
