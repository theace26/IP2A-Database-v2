# IP2A Coding Standards

> **Document Created:** January 27, 2026
> **Last Updated:** February 3, 2026
> **Version:** 1.1
> **Status:** Active — Mandatory Standard
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)

---

This document defines coding conventions for the IP2A Database v2 (UnionCore) project.

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

---

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

---

## Code Organization

### Service Layer Pattern

All business logic goes through services, not directly in routes.

```python
# src/services/member_service.py

def create_member(db: Session, data: dict) -> Member:
    """Create a new member."""
    member = Member(**data)
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
    data: dict
) -> Optional[Member]:
    """Update member, return updated member or None if not found."""
    member = get_member(db, member_id)
    if not member:
        return None
    for field, value in data.items():
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

### Blueprint Pattern (Routes)

UnionCore uses Flask Blueprints for route organization. Each module has its own Blueprint file.

```python
# src/api/members.py (plural filename)

from flask import Blueprint, request, jsonify, abort
from src.db.session import get_db
from src.services import member_service

members_bp = Blueprint("members", __name__, url_prefix="/members")

@members_bp.route("/", methods=["POST"])
def create_member():
    """Create a new member."""
    db = get_db()
    data = request.get_json()
    member = member_service.create_member(db, data)
    return jsonify(member.to_dict()), 201

@members_bp.route("/<int:member_id>", methods=["GET"])
def get_member(member_id):
    """Get member by ID."""
    db = get_db()
    member = member_service.get_member(db, member_id)
    if not member:
        abort(404, description="Member not found")
    return jsonify(member.to_dict())
```

For routes that render HTML (the majority of UnionCore's interface), use Jinja2 templates:

```python
# src/api/members.py (template-rendering routes)

from flask import Blueprint, render_template, redirect, url_for, flash

members_bp = Blueprint("members", __name__, url_prefix="/members")

@members_bp.route("/")
def list_members():
    """List all members."""
    db = get_db()
    members = member_service.list_members(db)
    return render_template("members/list.html", members=members)

@members_bp.route("/<int:member_id>")
def view_member(member_id):
    """View member detail."""
    db = get_db()
    member = member_service.get_member(db, member_id)
    if not member:
        abort(404)
    return render_template("members/detail.html", member=member)
```

### Enum Imports

```python
# ✅ CORRECT — use consolidated enums
from src.db.enums import CohortStatus, MemberStatus, DuesPaymentStatus

# ❌ WRONG — old location (deprecated)
from src.models.enums import CohortStatus
```

---

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

---

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

### Running Tests

```bash
# All tests (~470)
pytest -v

# With coverage
pytest --cov=src --cov-report=term-missing

# Specific module
pytest src/tests/test_dues.py -v

# By keyword
pytest -k "test_create" -v
```

---

## Frontend Conventions

UnionCore uses Jinja2 templates with HTMX + Alpine.js + DaisyUI. See [ADR-010](../decisions/ADR-010-frontend-architecture.md) and [ADR-011](../decisions/ADR-011-dues-frontend-patterns.md) for architecture decisions.

### Template Organization

Templates are organized by module under `src/templates/`:

```
src/templates/
├── base.html              # Base layout (DaisyUI + HTMX + Alpine.js)
├── components/            # Reusable partial templates
│   ├── _pagination.html
│   ├── _modal.html
│   └── _flash_messages.html
├── members/
│   ├── list.html
│   ├── detail.html
│   └── form.html
├── dues/
│   ├── index.html
│   ├── rates.html
│   ├── payments.html
│   └── adjustments.html
└── auth/
    ├── login.html
    └── setup.html
```

### HTMX Patterns

Use HTMX for partial page updates instead of full page reloads:

```html
<!-- Trigger server request, swap response into target -->
<button hx-get="/members/search?q=smith"
        hx-target="#results"
        hx-swap="innerHTML">
    Search
</button>
```

### Alpine.js Patterns

Use Alpine.js for client-side interactivity:

```html
<!-- Toggle visibility -->
<div x-data="{ open: false }">
    <button @click="open = !open">Toggle</button>
    <div x-show="open">Content</div>
</div>
```

---

## Git Workflow

### Branch Naming

- `feature/description` — New features
- `fix/description` — Bug fixes
- `docs/description` — Documentation only
- `refactor/description` — Code refactoring

### Commit Messages

Use conventional commits:

```
type(scope): description

[optional body explaining why]
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### Branch Strategy

- **`develop`** — Active development (Railway deploys from here)
- **`main`** — Production-ready (needs merge from `develop`)
- **Feature branches** — Created from `develop`

---

> **End-of-Session Rule:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

---

| Cross-Reference | Location |
|----------------|----------|
| Naming Conventions | `/docs/standards/naming-conventions.md` |
| ADR-010: Frontend Architecture | `/docs/decisions/ADR-010-frontend-architecture.md` |
| ADR-011: Dues Frontend Patterns | `/docs/decisions/ADR-011-dues-frontend-patterns.md` |
| Getting Started | `/docs/guides/getting-started.md` |
| Testing Strategy | `/docs/guides/testing-strategy.md` |
| End-of-Session Documentation | `/docs/guides/END_OF_SESSION_DOCUMENTATION.md` |

---

*When in doubt, follow existing patterns in the codebase.*

*Document Version: 1.1*
*Last Updated: February 3, 2026*
