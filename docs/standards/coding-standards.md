# IP2A Coding Standards

This document defines coding conventions for the IP2A Database project.

## Python Style

### General
- **Python version:** 3.12+
- **Formatter:** ruff (run before every commit)
- **Line length:** 88 characters (ruff default)
- **Imports:** Sorted by ruff, grouped (stdlib, third-party, local)

### Formatting Commands
```bash
# Check and fix issues
ruff check . --fix

# Format code
ruff format .

# Both in one line
ruff check . --fix && ruff format .
```

## Naming Conventions

See [naming-conventions.md](naming-conventions.md) for detailed patterns.

### Quick Reference
| Item | Convention | Example |
|------|------------|---------|
| Files | snake_case | `member_service.py` |
| Classes | PascalCase | `MemberService` |
| Functions | snake_case | `get_member_by_id()` |
| Variables | snake_case | `member_count` |
| Constants | UPPER_SNAKE | `MAX_PAGE_SIZE` |
| Database tables | snake_case (plural) | `members`, `audit_logs` |
| Database columns | snake_case | `created_at`, `member_id` |

## Code Organization

### Service Layer Pattern

All business logic goes through services, not directly in routes.

```python
# src/services/member_service.py

def create_member(db: Session, data: MemberCreate) -> Member:
    """Create a new member."""
    member = Member(**data.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

def get_member(db: Session, member_id: int) -> Optional[Member]:
    """Get member by ID, or None if not found."""
    return db.query(Member).filter(Member.id == member_id).first()

def list_members(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[Member]:
    """List members with pagination."""
    return db.query(Member).offset(skip).limit(limit).all()

def update_member(
    db: Session,
    member_id: int,
    data: MemberUpdate
) -> Optional[Member]:
    """Update member, return updated member or None if not found."""
    member = get_member(db, member_id)
    if not member:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    return member

def delete_member(db: Session, member_id: int) -> bool:
    """Delete member, return True if deleted, False if not found."""
    member = get_member(db, member_id)
    if not member:
        return False
    db.delete(member)
    db.commit()
    return True
```

### Router Pattern

```python
# src/routers/members.py (plural filename)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/members", tags=["Members"])

@router.post("/", response_model=MemberRead, status_code=201)
def create_member(data: MemberCreate, db: Session = Depends(get_db)):
    return member_service.create_member(db, data)

@router.get("/{member_id}", response_model=MemberRead)
def get_member(member_id: int, db: Session = Depends(get_db)):
    member = member_service.get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member
```

### Enum Imports

```python
# ✅ CORRECT - use consolidated enums
from src.db.enums import CohortStatus, MemberStatus

# ❌ WRONG - old location (deprecated)
from src.models.enums import CohortStatus
```

## Documentation

### Docstrings
Use Google-style docstrings for functions with non-obvious behavior:

```python
def calculate_seniority(hire_date: date, as_of: date = None) -> int:
    """Calculate member seniority in years.

    Args:
        hire_date: The member's original hire date.
        as_of: Date to calculate seniority as of. Defaults to today.

    Returns:
        Number of complete years of seniority.

    Raises:
        ValueError: If hire_date is in the future.
    """
```

### Comments
- Explain *why*, not *what*
- Comment non-obvious business logic
- Keep comments up to date with code changes

## Testing

### Test File Location
Tests go in `src/tests/` mirroring the source structure:
- `src/services/member_service.py` → `src/tests/test_member_service.py`

### Test Naming
```python
def test_create_member_with_valid_data():
    """Should create member and return with ID."""

def test_create_member_with_duplicate_email_fails():
    """Should raise error when email already exists."""
```

### Test Structure (Arrange-Act-Assert)
```python
def test_get_member_returns_none_for_missing_id(db_session):
    # Arrange
    non_existent_id = 99999

    # Act
    result = member_service.get_member(db_session, non_existent_id)

    # Assert
    assert result is None
```

## Git Workflow

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation only
- `refactor/description` - Code refactoring

### Commit Messages
Use conventional commits:
```
type(scope): description

[optional body explaining why]
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

---

*When in doubt, follow existing patterns in the codebase.*
