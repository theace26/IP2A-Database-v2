# Week 13: IP2A Entity Completion

**Version:** 1.0.0  
**Created:** February 1, 2026  
**Branch:** `develop`  
**Estimated Effort:** 6-8 hours (2-3 sessions)

---

## Overview

This instruction document addresses **overlooked IP2A-specific entities** identified during the ChatGPT transfer reconciliation. The original pre-apprenticeship training system design included entities that may not have been fully implemented during the union operations expansion.

### Entities to Verify/Implement

| Entity | Purpose | Priority | Status |
|--------|---------|----------|--------|
| `Location` | Training facility/site tracking | High | ❓ Verify |
| `InstructorHours` | Hours worked per session/cohort | High | ❓ Verify |
| `ToolCheckout` | Equipment issued to students | Medium | ❓ Verify |
| `GrantExpense` | Grant-specific expense tracking | Medium | ❓ Verify |

---

## Pre-Flight Checklist

- [ ] On `develop` branch
- [ ] All tests passing (`pytest -v`)
- [ ] Docker services running
- [ ] Reviewed existing models in `src/models/`
- [ ] Reviewed existing schemas in `src/schemas/`
- [ ] Scanned `/docs/*` for relevant context

---

## Phase 1: Entity Audit (Session 1)

### 1.1 Verify Existing Models

Run this audit to determine current state:

```bash
# List all model files
ls -la src/models/

# Search for Location-related code
grep -r "Location" src/models/ src/schemas/ src/services/

# Search for Hours tracking
grep -r "Hours" src/models/ src/schemas/ src/services/
grep -r "hours" src/models/ src/schemas/ src/services/

# Search for Tool/Equipment tracking
grep -r "Tool" src/models/ src/schemas/ src/services/
grep -r "Equipment" src/models/ src/schemas/ src/services/
grep -r "Checkout" src/models/ src/schemas/ src/services/

# Search for Expense tracking
grep -r "Expense" src/models/ src/schemas/ src/services/
```

### 1.2 Document Findings

Create a findings document before proceeding:

```markdown
# IP2A Entity Audit Findings
**Date:** YYYY-MM-DD

## Location
- [ ] Model exists: Yes/No
- [ ] If no, is `Organization` sufficient? Yes/No
- [ ] Fields needed: [list]

## InstructorHours
- [ ] Model exists: Yes/No
- [ ] Current tracking method: [describe]
- [ ] Fields needed: [list]

## ToolCheckout
- [ ] Model exists: Yes/No
- [ ] Current tracking method: [describe]
- [ ] Fields needed: [list]

## GrantExpense
- [ ] Model exists: Yes/No
- [ ] Relation to DuesPayment/Grant: [describe]
- [ ] Fields needed: [list]
```

---

## Phase 2: Location Model (If Needed)

### 2.1 Requirements

Training locations need tracking for:
- Multiple training sites (main hall, satellite locations, employer sites)
- Capacity tracking for scheduling
- Address/contact information
- Active/inactive status

### 2.2 Model Definition

If `Organization` doesn't cover this, create `src/models/location.py`:

```python
"""Training location model for IP2A program sites."""
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.cohort import Cohort


class Location(Base):
    """Training facility/site for IP2A program."""
    
    __tablename__ = "locations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address_line1: Mapped[str] = mapped_column(String(200), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), default="WA")
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
    
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    cohorts: Mapped[list["Cohort"]] = relationship(back_populates="location")
```

### 2.3 Schema Definition

Create `src/schemas/location.py`:

```python
"""Pydantic schemas for Location."""
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class LocationBase(BaseModel):
    name: str
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str = "WA"
    zip_code: str
    capacity: int | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    notes: str | None = None
    is_active: bool = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    capacity: int | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    notes: str | None = None
    is_active: bool | None = None


class LocationResponse(LocationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime
```

### 2.4 Update Cohort Model

Add foreign key to Cohort if location tracking needed:

```python
# In src/models/cohort.py, add:
location_id: Mapped[int | None] = mapped_column(
    ForeignKey("locations.id"), nullable=True
)
location: Mapped["Location"] = relationship(back_populates="cohorts")
```

---

## Phase 3: InstructorHours Model (If Needed)

### 3.1 Requirements

Track instructor time for:
- Grant compliance reporting
- Payroll/compensation tracking
- Utilization metrics
- Session-by-session records

### 3.2 Model Definition

Create `src/models/instructor_hours.py`:

```python
"""Instructor hours tracking for IP2A program."""
from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import String, Date, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.enums import InstructorHoursType

if TYPE_CHECKING:
    from src.models.instructor import Instructor
    from src.models.cohort import Cohort


class InstructorHours(Base):
    """Hours worked by instructor for a specific cohort/date."""
    
    __tablename__ = "instructor_hours"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    instructor_id: Mapped[int] = mapped_column(
        ForeignKey("instructors.id"), nullable=False
    )
    cohort_id: Mapped[int | None] = mapped_column(
        ForeignKey("cohorts.id"), nullable=True
    )
    
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    hours: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    hours_type: Mapped[InstructorHoursType] = mapped_column(
        default=InstructorHoursType.INSTRUCTION
    )
    
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    
    # Relationships
    instructor: Mapped["Instructor"] = relationship(back_populates="hours_entries")
    cohort: Mapped["Cohort"] = relationship(back_populates="instructor_hours")
```

### 3.3 Add Enum

Add to `src/db/enums/__init__.py`:

```python
class InstructorHoursType(str, Enum):
    """Types of instructor hours."""
    INSTRUCTION = "instruction"
    PREP = "prep"
    GRADING = "grading"
    ADMIN = "admin"
    MEETING = "meeting"
    OTHER = "other"
```

---

## Phase 4: ToolCheckout Model (If Needed)

### 4.1 Requirements

Track equipment/tools issued to students:
- What was issued
- When issued/returned
- Condition tracking
- Loss/damage handling

### 4.2 Model Definition

Create `src/models/tool_checkout.py`:

```python
"""Tool/equipment checkout tracking for IP2A students."""
from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import String, Date, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.enums import ToolCheckoutStatus

if TYPE_CHECKING:
    from src.models.student import Student


class ToolCheckout(Base):
    """Equipment issued to students during training."""
    
    __tablename__ = "tool_checkouts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"), nullable=False
    )
    
    tool_name: Mapped[str] = mapped_column(String(200), nullable=False)
    tool_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    checkout_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    status: Mapped[ToolCheckoutStatus] = mapped_column(
        default=ToolCheckoutStatus.CHECKED_OUT
    )
    condition_out: Mapped[str | None] = mapped_column(String(50), nullable=True)
    condition_in: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    replacement_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    student: Mapped["Student"] = relationship(back_populates="tool_checkouts")
```

### 4.3 Add Enum

```python
class ToolCheckoutStatus(str, Enum):
    """Status of tool checkout."""
    CHECKED_OUT = "checked_out"
    RETURNED = "returned"
    LOST = "lost"
    DAMAGED = "damaged"
    TRANSFERRED = "transferred"
```

---

## Phase 5: GrantExpense Model (If Needed)

### 5.1 Requirements

Track grant-specific expenses for:
- Funder compliance reporting
- Budget tracking per grant
- Expense categorization
- Receipt/documentation linking

### 5.2 Model Definition

Create `src/models/grant_expense.py`:

```python
"""Grant expense tracking for IP2A program funding."""
from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import String, Date, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.enums import GrantExpenseCategory, GrantExpenseStatus

if TYPE_CHECKING:
    from src.models.grant import Grant
    from src.models.document import Document


class GrantExpense(Base):
    """Expense charged against a specific grant."""
    
    __tablename__ = "grant_expenses"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    grant_id: Mapped[int] = mapped_column(
        ForeignKey("grants.id"), nullable=False
    )
    
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[GrantExpenseCategory] = mapped_column(nullable=False)
    
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    vendor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    status: Mapped[GrantExpenseStatus] = mapped_column(
        default=GrantExpenseStatus.PENDING
    )
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Link to receipt/documentation
    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id"), nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    
    # Relationships
    grant: Mapped["Grant"] = relationship(back_populates="expenses")
    document: Mapped["Document"] = relationship()
```

### 5.3 Add Enums

```python
class GrantExpenseCategory(str, Enum):
    """Categories for grant expenses."""
    MATERIALS = "materials"
    EQUIPMENT = "equipment"
    SUPPLIES = "supplies"
    INSTRUCTOR = "instructor"
    FACILITY = "facility"
    TRAVEL = "travel"
    ADMIN = "admin"
    OTHER = "other"


class GrantExpenseStatus(str, Enum):
    """Approval status for grant expenses."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REIMBURSED = "reimbursed"
```

---

## Phase 6: Testing

### 6.1 Test Files to Create

For each new model, create corresponding test file:

- `src/tests/test_location.py`
- `src/tests/test_instructor_hours.py`
- `src/tests/test_tool_checkout.py`
- `src/tests/test_grant_expense.py`

### 6.2 Minimum Test Coverage

Each entity needs:
- [ ] CRUD operations (create, read, update, delete)
- [ ] Relationship tests (FKs work correctly)
- [ ] Validation tests (required fields, constraints)
- [ ] Service layer tests (if service created)

---

## Phase 7: Frontend Integration (Optional This Week)

If time permits, add basic UI for:
- [ ] Location management page
- [ ] Instructor hours entry form
- [ ] Tool checkout tracking
- [ ] Grant expense entry

Otherwise, defer to Week 14.

---

## Acceptance Criteria

### Required
- [ ] Entity audit completed and documented
- [ ] Missing models created with migrations
- [ ] All new models have Pydantic schemas
- [ ] All new enums in `src/db/enums/`
- [ ] Minimum CRUD tests passing
- [ ] Relationships verified working

### Optional
- [ ] Service layer created for each entity
- [ ] API endpoints created
- [ ] Basic frontend pages

---

## Migration Notes

When creating migrations for new tables:

```bash
# Generate migration
alembic revision --autogenerate -m "add_ip2a_entities_location_hours_tools_expenses"

# Review the migration file!
# Check foreign key dependencies

# Apply migration
alembic upgrade head
```

---

## 📝 MANDATORY: End-of-Session Documentation

> **REQUIRED:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. **Do not forget about ADRs—update as necessary.**

### Quick Checklist

- [ ] `/CHANGELOG.md` — Version bump, new entities added
- [ ] `/CLAUDE.md` — Update model count, entity list
- [ ] `/docs/IP2A_MILESTONE_CHECKLIST.md` — Mark entity completion
- [ ] `/docs/decisions/ADR-XXX.md` — If architectural decisions made (e.g., Location vs Organization)
- [ ] `/docs/reports/session-logs/YYYY-MM-DD-ip2a-entities.md` — **Create new session log**

### ADR Triggers for This Week

Create an ADR if:
- Deciding Location is separate from Organization
- Choosing hours tracking granularity
- Expense approval workflow design

---

*Last Updated: February 1, 2026*
