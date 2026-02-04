# IP2A Naming Conventions

> **Document Created:** January 27, 2026
> **Last Updated:** February 3, 2026
> **Version:** 1.1
> **Status:** Active — Mandatory Standard
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)

---

Consistent naming makes code easier to read and maintain. Follow these conventions throughout the project.

## File Names

| Type | Convention | Example |
|------|------------|---------|
| Python modules | snake_case | `member_service.py` |
| Test files | test_*.py | `test_member_service.py` |
| Documentation | kebab-case.md | `getting-started.md` |
| Configuration | lowercase or UPPERCASE | `.env`, `Dockerfile` |
| Jinja2 templates | snake_case.html | `member_list.html` |
| Jinja2 partials | _partial_name.html | `_pagination.html`, `_modal.html` |
| Static assets | kebab-case | `main-styles.css`, `app-utils.js` |

## Python Code

### Classes

PascalCase for class names, suffixed with type for clarity:

```python
# Models (SQLAlchemy ORM — 26 models total)
class Member:
class MemberEmployment:
class DuesPayment:

# Schemas / Data Transfer
class MemberCreate:
class MemberUpdate:
class MemberRead:

# Services
class MemberService:  # or just functions in member_service.py

# Exceptions
class MemberNotFoundError:
```

### Functions and Methods

snake_case, verb-first for actions. Prefix with `get_`, `list_`, `create_`, `update_`, `delete_` for CRUD:

```python
def get_member(db, member_id):
def list_members(db, skip, limit):
def create_member(db, data):
def update_member(db, member_id, data):
def delete_member(db, member_id):

# Other patterns
def calculate_seniority(member):
def validate_email(email):
def send_notification(member, message):
```

### Variables

snake_case, descriptive. Avoid abbreviations except common ones like `id`, `db`:

```python
# ✅ Good
member_count = 42
active_members = get_active_members()
employment_history = member.employments

# ❌ Avoid
mc = 42
actMems = get_active_members()
emp_hist = member.employments
```

### Constants

UPPER_SNAKE_CASE, defined at module level:

```python
MAX_PAGE_SIZE = 100
DEFAULT_TOKEN_EXPIRY_HOURS = 24
VALID_STATUS_TRANSITIONS = {"pending": ["active", "rejected"]}
```

---

## Database

### Tables

snake_case, plural. Match the entity being stored:

```sql
members
member_employments
organizations
org_contacts
audit_logs
dues_payments
dues_rates
dues_periods
dues_adjustments
```

### Columns

snake_case with common suffixes:

- `_id` for foreign keys: `member_id`, `organization_id`
- `_at` for timestamps: `created_at`, `updated_at`, `deleted_at`
- `_by` for actor references: `changed_by`, `approved_by`
- `is_` for booleans: `is_active`, `is_deleted`

```sql
-- Example table
CREATE TABLE members (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    changed_by INTEGER REFERENCES users(id)
);
```

> **Known convention:** The `locked_until` field (not `is_locked`) is used for time-based account locking. This is intentional — see existing codebase for pattern.

### Indexes

- `ix_{table}_{column}` for single column
- `ix_{table}_{col1}_{col2}` for composite

```sql
CREATE INDEX ix_members_email ON members(email);
CREATE INDEX ix_member_employments_member_id_org_id
    ON member_employments(member_id, organization_id);
```

### Constraints

- `pk_{table}` for primary key (usually automatic)
- `fk_{table}_{referenced_table}` for foreign keys
- `uq_{table}_{column}` for unique constraints
- `ck_{table}_{description}` for check constraints

---

## API Endpoints

Plural nouns for resources, lowercase with hyphens for multi-word, nested for relationships:

```
GET    /members              # List members
POST   /members              # Create member
GET    /members/{id}         # Get member
PUT    /members/{id}         # Update member
DELETE /members/{id}         # Delete member

GET    /members/{id}/employments  # List member's employments
POST   /members/{id}/employments  # Add employment to member

GET    /audit-logs           # Multi-word resource with hyphen
GET    /dues-rates           # Multi-word resource with hyphen
POST   /dues-payments/{id}/record  # Action on resource
```

---

## Flask Blueprints

Blueprint names are singular, lowercase. URL prefixes match the resource:

```python
# src/api/members.py
members_bp = Blueprint("members", __name__, url_prefix="/members")

# src/api/dues.py
dues_bp = Blueprint("dues", __name__, url_prefix="/dues")

# src/api/auth.py
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
```

---

## Jinja2 Templates

Templates are organized by module under `src/templates/`:

```
src/templates/
├── base.html                    # Base layout
├── components/                  # Reusable partials (prefixed with _)
│   ├── _pagination.html
│   ├── _modal.html
│   └── _flash_messages.html
├── members/                     # Module-specific templates
│   ├── list.html
│   ├── detail.html
│   └── form.html
├── dues/
│   ├── index.html
│   ├── rates.html
│   └── payments.html
└── auth/
    ├── login.html
    └── setup.html
```

Naming rules:

- Module directories: lowercase, matching Blueprint name
- Template files: snake_case.html
- Partial templates: prefixed with underscore (`_modal.html`)
- Base/layout templates: `base.html`

---

## Enums

PascalCase for enum class, UPPER_SNAKE_CASE for values:

```python
class MemberStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class CohortStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class DuesPaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    WAIVED = "waived"
```

All enums are consolidated in `src/db/enums.py`. Do not create enum definitions elsewhere.

---

## Environment Variables

UPPER_SNAKE_CASE. Prefix with app name for custom vars:

```bash
# Standard
DATABASE_URL=postgresql://...
SECRET_KEY=...
FLASK_ENV=development
SENTRY_DSN=...
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...

# App-specific
IP2A_MAX_UPLOAD_SIZE=10485760
IP2A_DEFAULT_PAGE_SIZE=50
```

---

## Quick Reference Card

| Thing | Convention | Example |
|-------|------------|---------|
| Python file | snake_case.py | `member_service.py` |
| Doc file | kebab-case.md | `getting-started.md` |
| Template file | snake_case.html | `member_list.html` |
| Template partial | _snake_case.html | `_pagination.html` |
| Class | PascalCase | `MemberService` |
| Function | snake_case | `get_member()` |
| Variable | snake_case | `member_count` |
| Constant | UPPER_SNAKE | `MAX_PAGE_SIZE` |
| DB table | snake_case plural | `members` |
| DB column | snake_case | `created_at` |
| API route | /plural-nouns | `/audit-logs` |
| Blueprint | singular lowercase | `Blueprint("members", ...)` |
| Enum class | PascalCase | `MemberStatus` |
| Enum value | UPPER_SNAKE | `IN_PROGRESS` |
| Env var | UPPER_SNAKE | `DATABASE_URL` |

---

> **End-of-Session Rule:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

---

| Cross-Reference | Location |
|----------------|----------|
| Coding Standards | `/docs/standards/coding-standards.md` |
| ADR-010: Frontend Architecture | `/docs/decisions/ADR-010-frontend-architecture.md` |
| ADR-011: Dues Frontend Patterns | `/docs/decisions/ADR-011-dues-frontend-patterns.md` |
| Getting Started | `/docs/guides/getting-started.md` |

---

*When encountering existing code that doesn't follow these conventions, prefer consistency with surrounding code over strict adherence. Fix conventions in dedicated refactoring commits.*

*Document Version: 1.1*
*Last Updated: February 3, 2026*
