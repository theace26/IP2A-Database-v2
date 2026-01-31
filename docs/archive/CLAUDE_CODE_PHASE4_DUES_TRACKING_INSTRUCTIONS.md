# Claude Code Instructions: Phase 4 - Dues Tracking System

**Document Version:** 1.0
**Created:** January 28, 2026
**Estimated Time:** 6-8 hours
**Priority:** Medium (financial management feature)
**Target Version:** v0.7.0

---

## Objective

Implement a comprehensive dues tracking system for IBEW Local 46, including payment schedules, payment recording, arrears tracking, and financial reporting.

---

## Context

### Business Requirements

Union dues are essential revenue for operations. The system needs to:
- Track monthly dues for all members
- Support multiple payment methods (payroll deduction, check, cash, online)
- Handle partial payments and payment plans
- Track arrears and generate notifications
- Provide financial reporting for officers
- Maintain audit trail for all financial transactions

### Current State
- Member model exists with card types (A, BA, D cards)
- Different card types may have different dues amounts
- No existing dues tracking in the system

### Integration Points
- **Members** - Dues are per-member
- **Audit Logging** - All financial changes must be audited
- **Document Management** - Payment receipts can be stored as documents

---

## Database Design

### New Models (4 models)

#### 1. DuesRate
Defines dues amounts by member card type and effective date.

```python
# src/models/dues_rate.py
class DuesRate(Base, TimestampMixin):
    """Dues rate schedule by card type."""
    
    __tablename__ = "dues_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    card_type = Column(SQLAlchemyEnum(MemberCardType), nullable=False)
    monthly_amount = Column(Numeric(10, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # NULL = currently active
    description = Column(String(255), nullable=True)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('card_type', 'effective_date', name='uq_dues_rate_card_effective'),
    )
```

#### 2. DuesPeriod
Represents a billing period (typically monthly).

```python
# src/models/dues_period.py
class DuesPeriod(Base, TimestampMixin):
    """Monthly dues billing period."""
    
    __tablename__ = "dues_periods"
    
    id = Column(Integer, primary_key=True, index=True)
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)  # 1-12
    due_date = Column(Date, nullable=False)  # When dues are due
    grace_period_end = Column(Date, nullable=False)  # End of grace period
    is_closed = Column(Boolean, default=False)  # Period closed for new charges
    closed_at = Column(DateTime, nullable=True)
    closed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    closed_by = relationship("User", foreign_keys=[closed_by_id])
    payments = relationship("DuesPayment", back_populates="period")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('period_year', 'period_month', name='uq_dues_period_year_month'),
    )
    
    @property
    def period_name(self) -> str:
        """Return formatted period name like 'January 2026'."""
        import calendar
        return f"{calendar.month_name[self.period_month]} {self.period_year}"
```

#### 3. DuesPayment
Individual payment records.

```python
# src/models/dues_payment.py
class DuesPayment(Base, TimestampMixin, SoftDeleteMixin):
    """Individual dues payment record."""
    
    __tablename__ = "dues_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    period_id = Column(Integer, ForeignKey("dues_periods.id"), nullable=False, index=True)
    
    # Payment details
    amount_due = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), nullable=False, default=0)
    payment_date = Column(Date, nullable=True)
    payment_method = Column(SQLAlchemyEnum(PaymentMethod), nullable=True)
    
    # Status
    status = Column(SQLAlchemyEnum(DuesPaymentStatus), nullable=False, default=DuesPaymentStatus.PENDING)
    
    # Reference info
    reference_number = Column(String(100), nullable=True)  # Check number, transaction ID
    receipt_number = Column(String(50), nullable=True, unique=True)
    
    # Processing
    processed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    
    notes = Column(Text, nullable=True)
    
    # Relationships
    member = relationship("Member", back_populates="dues_payments")
    period = relationship("DuesPeriod", back_populates="payments")
    processed_by = relationship("User", foreign_keys=[processed_by_id])
    
    @property
    def balance_due(self) -> Decimal:
        """Calculate remaining balance."""
        return self.amount_due - self.amount_paid
    
    @property
    def is_paid_in_full(self) -> bool:
        """Check if payment is complete."""
        return self.amount_paid >= self.amount_due
```

#### 4. DuesAdjustment
Adjustments, waivers, and credits.

```python
# src/models/dues_adjustment.py
class DuesAdjustment(Base, TimestampMixin):
    """Dues adjustments, waivers, and credits."""
    
    __tablename__ = "dues_adjustments"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    payment_id = Column(Integer, ForeignKey("dues_payments.id"), nullable=True)  # Optional link to specific payment
    
    adjustment_type = Column(SQLAlchemyEnum(DuesAdjustmentType), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)  # Positive = credit, Negative = additional charge
    reason = Column(Text, nullable=False)
    
    # Approval workflow
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    status = Column(SQLAlchemyEnum(AdjustmentStatus), nullable=False, default=AdjustmentStatus.PENDING)
    
    # Relationships
    member = relationship("Member")
    payment = relationship("DuesPayment")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
```

---

## New Enums

Create `src/db/enums/dues_enums.py`:

```python
"""Enums for dues tracking system."""
from enum import Enum


class PaymentMethod(str, Enum):
    """How dues were paid."""
    PAYROLL_DEDUCTION = "payroll_deduction"
    CHECK = "check"
    CASH = "cash"
    MONEY_ORDER = "money_order"
    CREDIT_CARD = "credit_card"
    ACH_TRANSFER = "ach_transfer"
    ONLINE = "online"
    OTHER = "other"


class DuesPaymentStatus(str, Enum):
    """Status of a dues payment."""
    PENDING = "pending"          # Not yet due
    DUE = "due"                  # Due, not paid
    PARTIAL = "partial"          # Partially paid
    PAID = "paid"                # Paid in full
    OVERDUE = "overdue"          # Past grace period
    WAIVED = "waived"            # Waived (e.g., hardship)
    WRITTEN_OFF = "written_off"  # Uncollectable


class DuesAdjustmentType(str, Enum):
    """Type of dues adjustment."""
    WAIVER = "waiver"              # Full or partial waiver
    HARDSHIP = "hardship"          # Hardship reduction
    CREDIT = "credit"              # Credit for overpayment
    CORRECTION = "correction"      # Error correction
    LATE_FEE = "late_fee"          # Late payment fee
    REINSTATEMENT = "reinstatement"  # Reinstatement fee
    OTHER = "other"


class AdjustmentStatus(str, Enum):
    """Approval status for adjustments."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
```

---

## Step-by-Step Implementation

### Step 1: Create Enums

**File:** `src/db/enums/dues_enums.py`

Create the enums file with content from above.

**File:** `src/db/enums/__init__.py`

Add exports:
```python
from src.db.enums.dues_enums import (
    PaymentMethod,
    DuesPaymentStatus,
    DuesAdjustmentType,
    AdjustmentStatus,
)
```

### Step 2: Create Models

Create these files in `src/models/`:

1. `dues_rate.py`
2. `dues_period.py`
3. `dues_payment.py`
4. `dues_adjustment.py`

**File:** `src/models/__init__.py`

Add exports:
```python
from src.models.dues_rate import DuesRate
from src.models.dues_period import DuesPeriod
from src.models.dues_payment import DuesPayment
from src.models.dues_adjustment import DuesAdjustment
```

**File:** `src/models/member.py`

Add relationship:
```python
# In Member class
dues_payments = relationship("DuesPayment", back_populates="member")
```

### Step 3: Create Migration

```bash
alembic revision --autogenerate -m "Add dues tracking models"
```

Review the migration, then apply:
```bash
alembic upgrade head
```

### Step 4: Create Schemas

**File:** `src/schemas/dues_rate.py`

```python
"""Pydantic schemas for dues rates."""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.db.enums import MemberCardType


class DuesRateBase(BaseModel):
    """Base schema for dues rate."""
    card_type: MemberCardType
    monthly_amount: Decimal = Field(..., ge=0, decimal_places=2)
    effective_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None


class DuesRateCreate(DuesRateBase):
    """Schema for creating a dues rate."""
    pass


class DuesRateUpdate(BaseModel):
    """Schema for updating a dues rate."""
    monthly_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    end_date: Optional[date] = None
    description: Optional[str] = None


class DuesRateRead(DuesRateBase):
    """Schema for reading a dues rate."""
    id: int
    
    class Config:
        from_attributes = True
```

**File:** `src/schemas/dues_period.py`

```python
"""Pydantic schemas for dues periods."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class DuesPeriodBase(BaseModel):
    """Base schema for dues period."""
    period_year: int = Field(..., ge=2000, le=2100)
    period_month: int = Field(..., ge=1, le=12)
    due_date: date
    grace_period_end: date
    notes: Optional[str] = None


class DuesPeriodCreate(DuesPeriodBase):
    """Schema for creating a dues period."""
    pass


class DuesPeriodUpdate(BaseModel):
    """Schema for updating a dues period."""
    due_date: Optional[date] = None
    grace_period_end: Optional[date] = None
    notes: Optional[str] = None


class DuesPeriodRead(DuesPeriodBase):
    """Schema for reading a dues period."""
    id: int
    is_closed: bool
    closed_at: Optional[datetime] = None
    period_name: str
    
    class Config:
        from_attributes = True


class DuesPeriodClose(BaseModel):
    """Schema for closing a period."""
    notes: Optional[str] = None
```

**File:** `src/schemas/dues_payment.py`

```python
"""Pydantic schemas for dues payments."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.db.enums import PaymentMethod, DuesPaymentStatus


class DuesPaymentBase(BaseModel):
    """Base schema for dues payment."""
    member_id: int
    period_id: int
    amount_due: Decimal = Field(..., ge=0, decimal_places=2)


class DuesPaymentCreate(DuesPaymentBase):
    """Schema for creating a dues payment record."""
    pass


class DuesPaymentRecord(BaseModel):
    """Schema for recording a payment."""
    amount_paid: Decimal = Field(..., gt=0, decimal_places=2)
    payment_date: date
    payment_method: PaymentMethod
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class DuesPaymentUpdate(BaseModel):
    """Schema for updating a payment."""
    amount_paid: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    payment_date: Optional[date] = None
    payment_method: Optional[PaymentMethod] = None
    reference_number: Optional[str] = None
    status: Optional[DuesPaymentStatus] = None
    notes: Optional[str] = None


class DuesPaymentRead(DuesPaymentBase):
    """Schema for reading a payment."""
    id: int
    amount_paid: Decimal
    payment_date: Optional[date]
    payment_method: Optional[PaymentMethod]
    status: DuesPaymentStatus
    reference_number: Optional[str]
    receipt_number: Optional[str]
    balance_due: Decimal
    is_paid_in_full: bool
    processed_at: Optional[datetime]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class DuesPaymentWithMember(DuesPaymentRead):
    """Payment with member details."""
    member_name: str
    member_card_number: str
    period_name: str


class MemberDuesSummary(BaseModel):
    """Summary of member's dues status."""
    member_id: int
    member_name: str
    card_type: str
    total_due: Decimal
    total_paid: Decimal
    balance: Decimal
    periods_overdue: int
    last_payment_date: Optional[date]
```

**File:** `src/schemas/dues_adjustment.py`

```python
"""Pydantic schemas for dues adjustments."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.db.enums import DuesAdjustmentType, AdjustmentStatus


class DuesAdjustmentBase(BaseModel):
    """Base schema for dues adjustment."""
    member_id: int
    payment_id: Optional[int] = None
    adjustment_type: DuesAdjustmentType
    amount: Decimal = Field(..., decimal_places=2)
    reason: str = Field(..., min_length=10)


class DuesAdjustmentCreate(DuesAdjustmentBase):
    """Schema for creating an adjustment."""
    pass


class DuesAdjustmentApprove(BaseModel):
    """Schema for approving/denying adjustment."""
    approved: bool
    notes: Optional[str] = None


class DuesAdjustmentRead(DuesAdjustmentBase):
    """Schema for reading an adjustment."""
    id: int
    status: AdjustmentStatus
    requested_by_id: int
    approved_by_id: Optional[int]
    approved_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Step 5: Create Services

**File:** `src/services/dues_rate_service.py`

```python
"""Service for dues rate operations."""
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from src.db.enums import MemberCardType
from src.models.dues_rate import DuesRate
from src.schemas.dues_rate import DuesRateCreate, DuesRateUpdate


def get_current_rate(db: Session, card_type: MemberCardType) -> Optional[DuesRate]:
    """Get current active dues rate for a card type."""
    today = date.today()
    return db.query(DuesRate).filter(
        DuesRate.card_type == card_type,
        DuesRate.effective_date <= today,
        (DuesRate.end_date.is_(None) | (DuesRate.end_date >= today))
    ).order_by(DuesRate.effective_date.desc()).first()


def get_rate_for_date(
    db: Session, card_type: MemberCardType, target_date: date
) -> Optional[DuesRate]:
    """Get dues rate for a specific date."""
    return db.query(DuesRate).filter(
        DuesRate.card_type == card_type,
        DuesRate.effective_date <= target_date,
        (DuesRate.end_date.is_(None) | (DuesRate.end_date >= target_date))
    ).order_by(DuesRate.effective_date.desc()).first()


def get_all_rates(db: Session, active_only: bool = False) -> list[DuesRate]:
    """Get all dues rates."""
    query = db.query(DuesRate)
    if active_only:
        today = date.today()
        query = query.filter(
            DuesRate.end_date.is_(None) | (DuesRate.end_date >= today)
        )
    return query.order_by(DuesRate.card_type, DuesRate.effective_date.desc()).all()


def create_rate(db: Session, data: DuesRateCreate) -> DuesRate:
    """Create a new dues rate."""
    rate = DuesRate(**data.model_dump())
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


def update_rate(db: Session, rate_id: int, data: DuesRateUpdate) -> Optional[DuesRate]:
    """Update a dues rate."""
    rate = db.query(DuesRate).filter(DuesRate.id == rate_id).first()
    if not rate:
        return None
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rate, field, value)
    
    db.commit()
    db.refresh(rate)
    return rate
```

**File:** `src/services/dues_period_service.py`

```python
"""Service for dues period operations."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.models.dues_period import DuesPeriod
from src.schemas.dues_period import DuesPeriodCreate, DuesPeriodUpdate


def get_period(db: Session, period_id: int) -> Optional[DuesPeriod]:
    """Get a dues period by ID."""
    return db.query(DuesPeriod).filter(DuesPeriod.id == period_id).first()


def get_period_by_month(
    db: Session, year: int, month: int
) -> Optional[DuesPeriod]:
    """Get a dues period by year and month."""
    return db.query(DuesPeriod).filter(
        DuesPeriod.period_year == year,
        DuesPeriod.period_month == month
    ).first()


def get_current_period(db: Session) -> Optional[DuesPeriod]:
    """Get the current (most recent open) period."""
    return db.query(DuesPeriod).filter(
        DuesPeriod.is_closed == False
    ).order_by(DuesPeriod.period_year.desc(), DuesPeriod.period_month.desc()).first()


def get_all_periods(
    db: Session,
    year: Optional[int] = None,
    include_closed: bool = True
) -> list[DuesPeriod]:
    """Get all dues periods."""
    query = db.query(DuesPeriod)
    
    if year:
        query = query.filter(DuesPeriod.period_year == year)
    
    if not include_closed:
        query = query.filter(DuesPeriod.is_closed == False)
    
    return query.order_by(
        DuesPeriod.period_year.desc(),
        DuesPeriod.period_month.desc()
    ).all()


def create_period(db: Session, data: DuesPeriodCreate) -> DuesPeriod:
    """Create a new dues period."""
    period = DuesPeriod(**data.model_dump())
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


def close_period(
    db: Session,
    period_id: int,
    user_id: int,
    notes: Optional[str] = None
) -> Optional[DuesPeriod]:
    """Close a dues period."""
    period = get_period(db, period_id)
    if not period or period.is_closed:
        return None
    
    period.is_closed = True
    period.closed_at = datetime.utcnow()
    period.closed_by_id = user_id
    if notes:
        period.notes = notes
    
    db.commit()
    db.refresh(period)
    return period


def generate_periods_for_year(db: Session, year: int) -> list[DuesPeriod]:
    """Generate all 12 monthly periods for a year."""
    periods = []
    for month in range(1, 13):
        existing = get_period_by_month(db, year, month)
        if existing:
            periods.append(existing)
            continue
        
        # Due on 1st of month, grace period ends on 15th
        due_date = date(year, month, 1)
        grace_end = date(year, month, 15)
        
        period = DuesPeriod(
            period_year=year,
            period_month=month,
            due_date=due_date,
            grace_period_end=grace_end
        )
        db.add(period)
        periods.append(period)
    
    db.commit()
    return periods
```

**File:** `src/services/dues_payment_service.py`

```python
"""Service for dues payment operations."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy.orm import Session

from src.db.enums import DuesPaymentStatus, MemberCardType
from src.models.dues_payment import DuesPayment
from src.models.member import Member
from src.schemas.dues_payment import (
    DuesPaymentCreate,
    DuesPaymentRecord,
    DuesPaymentUpdate,
    MemberDuesSummary,
)
from src.services import dues_rate_service, dues_period_service


def get_payment(db: Session, payment_id: int) -> Optional[DuesPayment]:
    """Get a payment by ID."""
    return db.query(DuesPayment).filter(
        DuesPayment.id == payment_id,
        DuesPayment.deleted_at.is_(None)
    ).first()


def get_member_payments(
    db: Session,
    member_id: int,
    year: Optional[int] = None,
    status: Optional[DuesPaymentStatus] = None
) -> list[DuesPayment]:
    """Get all payments for a member."""
    query = db.query(DuesPayment).join(DuesPayment.period).filter(
        DuesPayment.member_id == member_id,
        DuesPayment.deleted_at.is_(None)
    )
    
    if year:
        query = query.filter(DuesPayment.period.has(period_year=year))
    
    if status:
        query = query.filter(DuesPayment.status == status)
    
    return query.order_by(DuesPayment.period_id.desc()).all()


def get_period_payments(
    db: Session,
    period_id: int,
    status: Optional[DuesPaymentStatus] = None
) -> list[DuesPayment]:
    """Get all payments for a period."""
    query = db.query(DuesPayment).filter(
        DuesPayment.period_id == period_id,
        DuesPayment.deleted_at.is_(None)
    )
    
    if status:
        query = query.filter(DuesPayment.status == status)
    
    return query.all()


def get_overdue_payments(db: Session) -> list[DuesPayment]:
    """Get all overdue payments."""
    return db.query(DuesPayment).filter(
        DuesPayment.status == DuesPaymentStatus.OVERDUE,
        DuesPayment.deleted_at.is_(None)
    ).all()


def create_payment_record(
    db: Session,
    data: DuesPaymentCreate
) -> DuesPayment:
    """Create a new payment record (typically when generating for a period)."""
    # Generate receipt number
    receipt_number = f"RCP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    payment = DuesPayment(
        **data.model_dump(),
        receipt_number=receipt_number,
        status=DuesPaymentStatus.PENDING
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def record_payment(
    db: Session,
    payment_id: int,
    data: DuesPaymentRecord,
    processed_by_id: int
) -> Optional[DuesPayment]:
    """Record a payment against a dues record."""
    payment = get_payment(db, payment_id)
    if not payment:
        return None
    
    payment.amount_paid += data.amount_paid
    payment.payment_date = data.payment_date
    payment.payment_method = data.payment_method
    payment.reference_number = data.reference_number
    payment.notes = data.notes
    payment.processed_by_id = processed_by_id
    payment.processed_at = datetime.utcnow()
    
    # Update status
    if payment.amount_paid >= payment.amount_due:
        payment.status = DuesPaymentStatus.PAID
    elif payment.amount_paid > 0:
        payment.status = DuesPaymentStatus.PARTIAL
    
    db.commit()
    db.refresh(payment)
    return payment


def generate_period_dues(
    db: Session,
    period_id: int,
    member_ids: Optional[list[int]] = None
) -> list[DuesPayment]:
    """Generate dues records for all active members for a period."""
    from src.db.enums import MemberStatus
    
    period = dues_period_service.get_period(db, period_id)
    if not period:
        raise ValueError(f"Period {period_id} not found")
    
    # Get active members
    query = db.query(Member).filter(Member.status == MemberStatus.ACTIVE)
    if member_ids:
        query = query.filter(Member.id.in_(member_ids))
    
    members = query.all()
    payments = []
    
    for member in members:
        # Check if payment record already exists
        existing = db.query(DuesPayment).filter(
            DuesPayment.member_id == member.id,
            DuesPayment.period_id == period_id,
            DuesPayment.deleted_at.is_(None)
        ).first()
        
        if existing:
            payments.append(existing)
            continue
        
        # Get rate for this member's card type
        rate = dues_rate_service.get_rate_for_date(
            db,
            member.card_type,
            date(period.period_year, period.period_month, 1)
        )
        
        if not rate:
            continue  # Skip if no rate defined
        
        payment = DuesPayment(
            member_id=member.id,
            period_id=period_id,
            amount_due=rate.monthly_amount,
            status=DuesPaymentStatus.PENDING,
            receipt_number=f"RCP-{period.period_year}{period.period_month:02d}-{uuid.uuid4().hex[:8].upper()}"
        )
        db.add(payment)
        payments.append(payment)
    
    db.commit()
    return payments


def update_overdue_status(db: Session) -> int:
    """Update status to OVERDUE for past-grace-period unpaid dues. Returns count updated."""
    from sqlalchemy import and_
    
    today = date.today()
    
    # Find payments that should be marked overdue
    payments = db.query(DuesPayment).join(DuesPayment.period).filter(
        and_(
            DuesPayment.status.in_([DuesPaymentStatus.PENDING, DuesPaymentStatus.DUE, DuesPaymentStatus.PARTIAL]),
            DuesPayment.period.has(grace_period_end < today),
            DuesPayment.deleted_at.is_(None)
        )
    ).all()
    
    count = 0
    for payment in payments:
        if payment.amount_paid < payment.amount_due:
            payment.status = DuesPaymentStatus.OVERDUE
            count += 1
    
    db.commit()
    return count


def get_member_dues_summary(db: Session, member_id: int) -> Optional[MemberDuesSummary]:
    """Get summary of member's dues status."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return None
    
    payments = get_member_payments(db, member_id)
    
    total_due = sum(p.amount_due for p in payments)
    total_paid = sum(p.amount_paid for p in payments)
    overdue_count = len([p for p in payments if p.status == DuesPaymentStatus.OVERDUE])
    
    last_payment = max(
        (p.payment_date for p in payments if p.payment_date),
        default=None
    )
    
    return MemberDuesSummary(
        member_id=member.id,
        member_name=f"{member.first_name} {member.last_name}",
        card_type=member.card_type.value,
        total_due=total_due,
        total_paid=total_paid,
        balance=total_due - total_paid,
        periods_overdue=overdue_count,
        last_payment_date=last_payment
    )
```

**File:** `src/services/dues_adjustment_service.py`

```python
"""Service for dues adjustment operations."""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.db.enums import AdjustmentStatus
from src.models.dues_adjustment import DuesAdjustment
from src.schemas.dues_adjustment import DuesAdjustmentCreate


def get_adjustment(db: Session, adjustment_id: int) -> Optional[DuesAdjustment]:
    """Get an adjustment by ID."""
    return db.query(DuesAdjustment).filter(DuesAdjustment.id == adjustment_id).first()


def get_pending_adjustments(db: Session) -> list[DuesAdjustment]:
    """Get all pending adjustments."""
    return db.query(DuesAdjustment).filter(
        DuesAdjustment.status == AdjustmentStatus.PENDING
    ).order_by(DuesAdjustment.created_at).all()


def get_member_adjustments(db: Session, member_id: int) -> list[DuesAdjustment]:
    """Get all adjustments for a member."""
    return db.query(DuesAdjustment).filter(
        DuesAdjustment.member_id == member_id
    ).order_by(DuesAdjustment.created_at.desc()).all()


def create_adjustment(
    db: Session,
    data: DuesAdjustmentCreate,
    requested_by_id: int
) -> DuesAdjustment:
    """Create a new adjustment request."""
    adjustment = DuesAdjustment(
        **data.model_dump(),
        requested_by_id=requested_by_id,
        status=AdjustmentStatus.PENDING
    )
    db.add(adjustment)
    db.commit()
    db.refresh(adjustment)
    return adjustment


def approve_adjustment(
    db: Session,
    adjustment_id: int,
    approved_by_id: int,
    approved: bool
) -> Optional[DuesAdjustment]:
    """Approve or deny an adjustment."""
    adjustment = get_adjustment(db, adjustment_id)
    if not adjustment or adjustment.status != AdjustmentStatus.PENDING:
        return None
    
    adjustment.status = AdjustmentStatus.APPROVED if approved else AdjustmentStatus.DENIED
    adjustment.approved_by_id = approved_by_id
    adjustment.approved_at = datetime.utcnow()
    
    # If approved and linked to a payment, apply the adjustment
    if approved and adjustment.payment_id:
        from src.models.dues_payment import DuesPayment
        payment = db.query(DuesPayment).filter(DuesPayment.id == adjustment.payment_id).first()
        if payment:
            payment.amount_due += adjustment.amount  # Negative = credit
    
    db.commit()
    db.refresh(adjustment)
    return adjustment
```

### Step 6: Create Routers

Create these router files in `src/routers/`:

1. `dues_rates.py`
2. `dues_periods.py`
3. `dues_payments.py`
4. `dues_adjustments.py`

(Full router code similar to existing patterns - CRUD operations with authentication)

### Step 7: Register Routers

**File:** `src/main.py`

Add:
```python
from src.routers.dues_rates import router as dues_rates_router
from src.routers.dues_periods import router as dues_periods_router
from src.routers.dues_payments import router as dues_payments_router
from src.routers.dues_adjustments import router as dues_adjustments_router

# Register routers
app.include_router(dues_rates_router)
app.include_router(dues_periods_router)
app.include_router(dues_payments_router)
app.include_router(dues_adjustments_router)
```

### Step 8: Create Seed Data

**File:** `src/seed/dues_seed.py`

```python
"""Seed data for dues tracking system."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.db.enums import MemberCardType
from src.models.dues_rate import DuesRate
from src.services import dues_period_service


def seed_dues_rates(db: Session) -> None:
    """Seed default dues rates."""
    rates = [
        {
            "card_type": MemberCardType.A,
            "monthly_amount": Decimal("45.00"),
            "effective_date": date(2024, 1, 1),
            "description": "A Card monthly dues"
        },
        {
            "card_type": MemberCardType.BA,
            "monthly_amount": Decimal("35.00"),
            "effective_date": date(2024, 1, 1),
            "description": "BA Card monthly dues"
        },
        {
            "card_type": MemberCardType.D,
            "monthly_amount": Decimal("25.00"),
            "effective_date": date(2024, 1, 1),
            "description": "D Card monthly dues"
        },
    ]
    
    for rate_data in rates:
        existing = db.query(DuesRate).filter(
            DuesRate.card_type == rate_data["card_type"],
            DuesRate.effective_date == rate_data["effective_date"]
        ).first()
        
        if not existing:
            rate = DuesRate(**rate_data)
            db.add(rate)
    
    db.commit()


def seed_dues_periods(db: Session, year: int = 2026) -> None:
    """Seed dues periods for a year."""
    dues_period_service.generate_periods_for_year(db, year)


def run_dues_seed(db: Session) -> None:
    """Run all dues seed data."""
    print("Seeding dues rates...")
    seed_dues_rates(db)
    
    print("Seeding dues periods for 2026...")
    seed_dues_periods(db, 2026)
    
    print("Dues seed data complete!")


if __name__ == "__main__":
    from src.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        run_dues_seed(db)
    finally:
        db.close()
```

### Step 9: Create Tests

**File:** `src/tests/test_dues.py`

Create comprehensive tests for:
- Dues rate CRUD
- Dues period generation
- Payment recording
- Overdue status updates
- Member dues summary
- Adjustment workflow

### Step 10: Run and Verify

```bash
# Apply migration
alembic upgrade head

# Run seed
python -m src.seed.dues_seed

# Run tests
pytest src/tests/test_dues.py -v

# Run all tests
pytest -v
```

---

## API Endpoints Summary

### Dues Rates
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/dues/rates` | Staff+ | List all rates |
| GET | `/dues/rates/current/{card_type}` | Staff+ | Get current rate |
| POST | `/dues/rates` | Admin | Create rate |
| PATCH | `/dues/rates/{id}` | Admin | Update rate |

### Dues Periods
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/dues/periods` | Staff+ | List periods |
| GET | `/dues/periods/current` | Staff+ | Get current period |
| POST | `/dues/periods` | Admin | Create period |
| POST | `/dues/periods/generate/{year}` | Admin | Generate year |
| POST | `/dues/periods/{id}/close` | Admin | Close period |

### Dues Payments
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/dues/payments` | Staff+ | List with filters |
| GET | `/dues/payments/{id}` | Staff+ | Get payment |
| GET | `/dues/payments/member/{id}` | Staff+ | Member payments |
| GET | `/dues/payments/member/{id}/summary` | Staff+ | Member summary |
| POST | `/dues/payments/{id}/record` | Staff+ | Record payment |
| POST | `/dues/payments/generate/{period_id}` | Admin | Generate for period |
| POST | `/dues/payments/update-overdue` | Admin | Update overdue status |

### Dues Adjustments
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/dues/adjustments` | Staff+ | List adjustments |
| GET | `/dues/adjustments/pending` | Officer+ | Pending approvals |
| POST | `/dues/adjustments` | Staff+ | Create adjustment |
| POST | `/dues/adjustments/{id}/approve` | Officer+ | Approve/deny |

---

## Checklist

- [ ] Create `src/db/enums/dues_enums.py`
- [ ] Update `src/db/enums/__init__.py`
- [ ] Create `src/models/dues_rate.py`
- [ ] Create `src/models/dues_period.py`
- [ ] Create `src/models/dues_payment.py`
- [ ] Create `src/models/dues_adjustment.py`
- [ ] Update `src/models/__init__.py`
- [ ] Update `src/models/member.py` (add relationship)
- [ ] Create and apply migration
- [ ] Create `src/schemas/dues_rate.py`
- [ ] Create `src/schemas/dues_period.py`
- [ ] Create `src/schemas/dues_payment.py`
- [ ] Create `src/schemas/dues_adjustment.py`
- [ ] Create `src/services/dues_rate_service.py`
- [ ] Create `src/services/dues_period_service.py`
- [ ] Create `src/services/dues_payment_service.py`
- [ ] Create `src/services/dues_adjustment_service.py`
- [ ] Create `src/routers/dues_rates.py`
- [ ] Create `src/routers/dues_periods.py`
- [ ] Create `src/routers/dues_payments.py`
- [ ] Create `src/routers/dues_adjustments.py`
- [ ] Register routers in `src/main.py`
- [ ] Create `src/seed/dues_seed.py`
- [ ] Create `src/tests/test_dues.py`
- [ ] Run all tests - should pass
- [ ] Update CLAUDE.md changelog
- [ ] Commit with descriptive message

---

## CLAUDE.md Changelog Entry

```
| 2026-01-XX HH:MM UTC | Claude Code | Phase 4 Complete - Dues Tracking: 4 models (DuesRate, DuesPeriod, DuesPayment, DuesAdjustment), 4 enums, ~20 API endpoints. Payment recording, overdue tracking, adjustment workflow. X new tests. Migration: XXXXX. Ready for v0.7.0. |
```

---

## Commit Message Template

```
feat: Phase 4 - Dues Tracking System

- Add 4 dues models: DuesRate, DuesPeriod, DuesPayment, DuesAdjustment
- Add 4 enums: PaymentMethod, DuesPaymentStatus, DuesAdjustmentType, AdjustmentStatus
- Add dues services with payment recording, overdue tracking
- Add ~20 API endpoints for complete dues management
- Add dues seed data (rates by card type, 2026 periods)
- Add comprehensive tests

Features:
- Monthly dues by card type (A, BA, D)
- Multiple payment methods
- Partial payment support
- Overdue tracking with grace periods
- Adjustment/waiver workflow with approval
- Member dues summary

Migration: [hash]
```

---

## Expected Outcome

- 4 new models for dues tracking
- ~20 new API endpoints
- Payment recording and history
- Overdue status management
- Adjustment workflow
- Seed data for rates and periods
- Comprehensive tests
- Ready for v0.7.0 tag

---

*End of Instructions*
