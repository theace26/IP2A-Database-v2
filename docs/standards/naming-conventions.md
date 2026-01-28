# IP2A Naming Conventions

Consistent naming makes code easier to read and maintain. Follow these conventions throughout the project.

## File Names

| Type | Convention | Example |
|------|------------|---------|
| Python modules | snake_case | `member_service.py` |
| Test files | test_*.py | `test_member_service.py` |
| Documentation | kebab-case.md | `getting-started.md` |
| Configuration | lowercase or UPPERCASE | `.env`, `Dockerfile` |

## Python Code

### Classes
- **PascalCase** for class names
- Suffix with type for clarity

```python
# Models
class Member:
class MemberEmployment:

# Schemas (Pydantic)
class MemberCreate:
class MemberUpdate:
class MemberRead:

# Services
class MemberService:  # or just functions in member_service.py

# Exceptions
class MemberNotFoundError:
```

### Functions and Methods
- **snake_case**
- Verb-first for actions
- Prefix with `get_`, `list_`, `create_`, `update_`, `delete_` for CRUD

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
- **snake_case**
- Descriptive, avoid abbreviations (except common ones like `id`, `db`)

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
- **UPPER_SNAKE_CASE**
- Define at module level

```python
MAX_PAGE_SIZE = 100
DEFAULT_TOKEN_EXPIRY_HOURS = 24
VALID_STATUS_TRANSITIONS = {"pending": ["active", "rejected"]}
```

## Database

### Tables
- **snake_case**, **plural**
- Match the entity being stored

```sql
members
member_employments
organizations
org_contacts
audit_logs
```

### Columns
- **snake_case**
- Common suffixes:
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

## API Endpoints

- **Plural nouns** for resources
- **Lowercase with hyphens** for multi-word resources
- **Nested** for relationships

```
GET    /members              # List members
POST   /members              # Create member
GET    /members/{id}         # Get member
PUT    /members/{id}         # Update member
DELETE /members/{id}         # Delete member

GET    /members/{id}/employments  # List member's employments
POST   /members/{id}/employments  # Add employment to member

GET    /audit-logs           # Multi-word resource with hyphen
```

## Enums

- **PascalCase** for enum class
- **UPPER_SNAKE_CASE** for enum values

```python
class MemberStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class CohortStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
```

## Environment Variables

- **UPPER_SNAKE_CASE**
- Prefix with app name for custom vars

```bash
# Standard
DATABASE_URL=postgresql://...
SECRET_KEY=...

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
| Class | PascalCase | `MemberService` |
| Function | snake_case | `get_member()` |
| Variable | snake_case | `member_count` |
| Constant | UPPER_SNAKE | `MAX_PAGE_SIZE` |
| DB table | snake_case plural | `members` |
| DB column | snake_case | `created_at` |
| API route | /plural-nouns | `/audit-logs` |
| Enum class | PascalCase | `MemberStatus` |
| Enum value | UPPER_SNAKE | `IN_PROGRESS` |
| Env var | UPPER_SNAKE | `DATABASE_URL` |

---

*When encountering existing code that doesn't follow these conventions, prefer consistency with surrounding code over strict adherence. Fix conventions in dedicated refactoring commits.*
