# IP2A-Database-v2: Phase 7 - Complete Implementation Plan

> **Document Created:** February 2, 2026
> **Last Updated:** February 3, 2026 (Batch 4b documentation update)
> **Version:** 2.1
> **Status:** Ready for Implementation
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1-19)

---

## Related Documents

| Document | Location | Relationship |
|----------|----------|-------------|
| Phase 7 Referral & Dispatch Plan | `docs/phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md` | Alternate schema (more detailed dispatch/bid models) — reconcile in Session 20A |
| LaborPower Gap Analysis | `docs/phase7/LABORPOWER_GAP_ANALYSIS.md` | Feature gaps that Phase 7 addresses |
| LaborPower Implementation Plan | `docs/phase7/LABORPOWER_IMPLEMENTATION_PLAN.md` | Original 6-phase build schedule (Weeks 20-32) |
| LaborPower Reports Inventory | `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` | ~78 reports these models must power |
| Local 46 Referral Books | `docs/phase7/LOCAL46_REFERRAL_BOOKS.md` | Book/classification seed data reference |
| Phase 7 Continuity Doc | `docs/phase7/PHASE7_CONTINUITY_DOC.md` | Session-by-session continuity notes |
| Phase 7 Continuity Addendum | `docs/phase7/PHASE7_CONTINUITY_DOC_ADDENDUM.md` | Report sprint schedule overlap notes |
| ADR-008 Dues Tracking | `docs/decisions/ADR-008-dues-tracking-system.md` | Existing DuesPayment model — Phase 7B transactions build on this |
| ADR-012 Audit Logging | `docs/decisions/ADR-012-audit-logging.md` | Immutability trigger — dispatch actions must integrate |
| ADR-013 Stripe Integration | `docs/decisions/ADR-013-stripe-payment-integration.md` | Existing Stripe — MemberTransaction must coexist |
| ADR-014 Grant Compliance | `docs/decisions/ADR-014-grant-compliance-reporting.md` | WeasyPrint + openpyxl report infrastructure |

---

## Current Baseline (v0.9.4-alpha)

Phase 7 builds on top of 19 weeks of completed work:

| Metric | Current Value |
|--------|--------------|
| **Version** | v0.9.4-alpha — FEATURE-COMPLETE (Weeks 1-19) |
| **Tests** | ~470 total (~200+ frontend, 165 backend, ~78 production, 25 Stripe) |
| **API Endpoints** | ~150 |
| **ORM Models** | 26 (Phase 7 adds 14 new tables) |
| **ADRs** | 14 (Phase 7 will add ADR-015+) |
| **Deployment** | Railway (prod), Render (backup) |
| **Payments** | Stripe live (Checkout Sessions + webhooks) |
| **Reports** | WeasyPrint PDF + openpyxl Excel + Chart.js dashboard |
| **Mobile** | PWA with offline support and service worker |

### Key Integration Points for Phase 7

| Existing Feature | Phase 7 Interaction |
|-----------------|---------------------|
| **DuesPayment model** (Week 10) | MemberTransaction extends this — may wrap or replace DuesPayment for referral-era transactions |
| **Stripe** (Week 11) | MemberTransaction includes `stripe_payment_id` / `stripe_session_id` — must coexist with existing Checkout flow |
| **Audit logging** (Week 11) | All dispatch/registration actions MUST generate audit trail entries (NLRA 7-year compliance) |
| **Organization model** (Week 6) | LaborRequest.employer_id → organizations.id — existing FK |
| **Member model** (Week 5) | Phase 7A adds 15+ fields to Member — migration must be non-destructive |
| **Chart.js dashboard** (Week 19) | Referral summary reports (C-40, B-12, B-13) extend the analytics dashboard |
| **Report builder** (Week 19) | Filter framework for ~78 reports extends the existing report builder |

### Architecture Reminders

- **Enums** always in `src/db/enums/`, import from `src.db.enums` — Phase 7 enums go in `src/db/enums/phase7_enums.py`
- **Member is SEPARATE from Student** (linked via FK on Student) — dispatch qualifications ≠ JATC training
- **User** model uses `locked_until` datetime field (NOT boolean `is_locked`)
- **Seed data** follows registry-based ordering — new Phase 7 seeds must register in the correct dependency order

---

## 📋 Executive Summary

Phase 7 implements the core union hall operations from LaborPower, using the official **IBEW Local 46 Referral Procedures** (effective October 4, 2024) as the authoritative source for business rules.

### Scope

| Module | Priority | Est. Weeks | New Tables | Builds On |
|--------|----------|------------|------------|-----------|
| Member & Financial Enhancement | 🔴 HIGH | 2 | 2 | Member model (Week 5), DuesPayment (Week 10) |
| Transaction System | 🔴 HIGH | 2 | 1 | Stripe (Week 11/ADR-013), DuesPayment (Week 10/ADR-008) |
| Referral Books & Registration | 🔴 HIGH | 2 | 3 | — (new domain) |
| Labor Requests & Dispatch | 🔴 HIGH | 3 | 2 | Organization (Week 6), Audit (Week 11/ADR-012) |
| Skills & Qualifications | 🟡 MEDIUM | 2 | 4 | **⚠️ Member ≠ Student** — dispatch skills only |
| Pension & Benefits | 🟢 LOW | 2 | 2 | MemberFinancial (Phase 7A) |
| **Total** | | **13 weeks** | **14 tables** | |

---

## 📜 IBEW Local 46 Referral Rules Summary

### Office Hours & Locations

| Location | Hours | Phone |
|----------|-------|-------|
| Kent Office | 8:00 AM - 5:00 PM | 253-395-6530 |
| Bremerton Office | 8:00 AM - 3:00 PM | - |
| Email | dispatch1@ibew46.com | - |
| Job Line | 253-395-6516 | - |

### Morning Referral Schedule

| Time | Classification |
|------|----------------|
| 8:30 AM | Inside Wireperson |
| 9:00 AM | Tradeshow |
| 9:30 AM | Seattle School District |
| 9:30 AM | Sound and Communication |
| 9:30 AM | Marine |
| 9:30 AM | Stockperson |
| 9:30 AM | Light Fixture Maintenance |
| 9:30 AM | Residential |

### Key Business Rules

#### Registration
- Must be **in person or via email**
- Can only sign **highest priority book/list for ONE classification**
- Cannot sign wire/tradeshow combination
- Processed AFTER Inside Wireperson Book 1 referral completes

#### Re-Sign Requirements
- Required every **30 days** from registration or last re-sign
- Can be done: in person, fax, Internet, or email

#### Check Marks
- **2 check marks allowed** without penalty
- **3rd check mark** = rolled completely off the book
- Must re-register in person or via email after rolloff
- **Separate books**: Seattle, Bremerton, Port Angeles
- Requests for one book don't generate check marks for other area books
- **Max 1 check mark per book per day**

#### No Check Marks For
- Specialty requests/skills not in CBA
- Start times before 6:00 AM
- Under scale work recovery jobs
- Short call requests
- Rejection by employer

#### Short Calls
- Jobs **≤10 business days** (excluding referral day and holidays)
- Limited to "unemployed status" **twice** for short calls
- Short calls **≤3 working days** = no limit
- "Long Call" request = registration restored
- Laid off within Short Call period = registration restored

#### Internet/Email Bidding
- Available **5:30 PM to 7:00 AM**
- Must check in with employer by **3:00 PM** on dispatch day
- Reject after bidding = **considered a quit**
- Second rejection in 12 months = **lose privileges for 1 year**

#### Quit or Discharge
- **Rolled completely off ALL books**
- Cannot fill "Foreperson-by-Name" request for **2 weeks** after quit/discharge

#### Exempt Status (from check marks and re-sign)
- Military service
- Union business
- Salting
- Medically unfit
- Jury duty
- Working under scale or traveling (up to 6 months)

---

## 🗄️ Database Schema

### Phase 7A: Member & Financial Enhancement

> **Builds on:** Member model (Week 5), DuesPayment model (Week 10/ADR-008)

#### 1. Member Model Updates

```python
# Add to src/models/member.py

class Member(Base):
    # ... existing fields ...
    
    # IBEW Identification
    card_number = Column(String(20), unique=True, index=True)  # "7464416"
    member_type = Column(String(5))                             # "A", "BA", "CE", "CW"
    local_number = Column(String(10), default="0046")
    
    # Key Dates
    initiation_date = Column(Date)
    application_date = Column(Date)
    seniority_date = Column(Date)
    exam_date = Column(Date)
    last_activity_date = Column(Date)
    last_activity_code = Column(String(20))
    
    # Classification
    job_class = Column(String(10))                              # "1.0", "1.1", "1.4"
    job_class_date = Column(Date)
    
    # Referral Status
    referral_status = Column(String(20), default="available")   # Enum
    internet_bidding_enabled = Column(Boolean, default=True)
    internet_bidding_suspended_until = Column(Date)             # For 1-year suspension
    
    # Exempt Status
    is_exempt = Column(Boolean, default=False)
    exempt_reason = Column(String(50))                          # Enum
    exempt_until = Column(Date)
    
    # Additional
    ethnic_code = Column(String(10))
```

> **⚠️ Migration note:** This adds 15+ columns to an existing table with production data. Use `ALTER TABLE ADD COLUMN` with defaults — do NOT recreate the table. Test migration against a Railway snapshot first.

#### 2. Member Financial Table (NEW)

```python
# src/models/member_financial.py

class MemberFinancial(Base):
    __tablename__ = "member_financials"
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"), unique=True)
    
    # Dues Tracking (separate basic and working)
    basic_paid_thru = Column(Date)
    working_paid_thru = Column(Date)
    
    # Balance
    account_balance = Column(Numeric(10, 2), default=0)  # Negative = owes
    credit_balance = Column(Numeric(10, 2), default=0)
    
    # Initiation Fees
    init_fee_charged = Column(Numeric(10, 2), default=0)
    init_fee_paid = Column(Numeric(10, 2), default=0)
    
    # Other Funds
    jury_paid_thru = Column(Integer)       # Year
    sick_paid_thru = Column(Integer)       # Year
    vacation_balance = Column(Numeric(10, 2), default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    @property
    def init_fee_due(self):
        return max(Decimal("0"), (self.init_fee_charged or 0) - (self.init_fee_paid or 0))
```

> **Coexistence note:** MemberFinancial tracks LaborPower-style financial state. The existing DuesPayment model (ADR-008) handles Stripe-era payments. During Phase 7, determine whether DuesPayment records should auto-update MemberFinancial fields or remain independent.

### Phase 7B: Transaction System

> **Builds on:** DuesPayment model (Week 10/ADR-008), Stripe integration (Week 11/ADR-013)

#### 3. Member Transaction Table (NEW)

```python
# src/models/member_transaction.py

class MemberTransaction(Base):
    """
    Comprehensive transaction history matching LaborPower structure.
    Coexists with existing DuesPayment model for Stripe-era payments.
    """
    __tablename__ = "member_transactions"
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    
    # Transaction Info
    transaction_date = Column(Date, nullable=False, index=True)
    amount_paid = Column(Numeric(10, 2), nullable=False)
    
    # Basic Dues
    basic_months = Column(Integer, default=0)
    basic_amount = Column(Numeric(10, 2), default=0)
    basic_paid_thru = Column(Date)
    
    # Working Dues
    working_amount = Column(Numeric(10, 2), default=0)
    working_months = Column(Integer, default=0)
    working_paid_thru = Column(Date)
    
    # Additional Funds
    jury_amount = Column(Numeric(10, 2), default=0)
    sick_amount = Column(Numeric(10, 2), default=0)
    reinstatement_fee = Column(Numeric(10, 2), default=0)
    
    # Running Balance
    credit_balance = Column(Numeric(10, 2), default=0)
    
    # Source/Batch
    batch_id = Column(String(100))           # "IBEW46 -TANIH 01/07/2026"
    batch_source = Column(String(50))        # "IBEW46", "VECA", "WEB"
    processor = Column(String(50))           # Staff name
    activity_code = Column(String(5))        # "X", "V", "D", "N"
    payment_source = Column(String(20))      # Enum: dco, web, cash, check, cc
    
    # Employer (for DCO)
    employer_id = Column(Integer, ForeignKey("organizations.id"))
    
    # Stripe Integration (coexists with existing DuesPayment.stripe_session_id)
    stripe_payment_id = Column(String(100))
    stripe_session_id = Column(String(100))
    
    # Notes
    description = Column(Text)
    
    # Audit (all transactions are also captured by the immutability trigger — ADR-012)
    created_at = Column(DateTime, default=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
```

### Phase 7C: Referral Books & Registration

> **New domain** — no existing models to build on. Seed data must integrate with existing registry-based seed ordering (see `seeds.mmd` diagram).

#### 4. Referral Book Table (NEW)

```python
# src/models/referral_book.py

class ReferralBook(Base):
    """
    Out-of-work list definition.
    """
    __tablename__ = "referral_books"
    
    id = Column(Integer, primary_key=True)
    
    # Identification
    name = Column(String(100), nullable=False)       # "Wire Seattle"
    code = Column(String(30), unique=True)           # "WIRE_SEA_1"
    
    # Classification
    classification = Column(String(50))              # "inside_wireperson", "sound_comm"
    book_number = Column(Integer, default=1)         # 1 = Book 1, 2 = Book 2
    region = Column(String(50))                      # "Seattle", "Bremerton", "Port Angeles"
    
    # Referral Schedule
    referral_start_time = Column(Time)               # 8:30 AM for Inside Wire
    
    # Rules (from Local 46 procedures)
    re_sign_days = Column(Integer, default=30)       # Must re-sign every X days
    max_check_marks = Column(Integer, default=2)     # Allowed before rolloff
    
    # Status
    is_active = Column(Boolean, default=True)
    internet_bidding_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

> **Seed data note:** ReferralBook seed data includes fields (`book_number`, `re_sign_days`, `max_check_marks`) not present in the Gap Analysis schema. These were added based on LOCAL46_REFERRAL_BOOKS.md. Resolve final field list in Session 20A. See `LOCAL46_REFERRAL_BOOKS.md` open questions.

#### 5. Book Registration Table (NEW)

```python
# src/models/book_registration.py

class BookRegistration(Base):
    """
    Member's position on an out-of-work list.
    """
    __tablename__ = "book_registrations"
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("referral_books.id"), nullable=False)
    
    # Registration
    registration_date = Column(DateTime, nullable=False)
    registration_number = Column(Integer)            # Queue position at registration
    current_position = Column(Integer)               # Current queue position
    registration_method = Column(String(20))         # "in_person", "email"
    
    # Status
    status = Column(String(20), default="active")    # Enum: active, rolled_off, dispatched
    
    # Re-sign Tracking
    last_sign_date = Column(DateTime)
    next_sign_deadline = Column(DateTime)            # 30 days from last sign
    
    # Check Marks
    check_marks = Column(Integer, default=0)
    last_check_mark_date = Column(Date)
    
    # Short Call Tracking
    short_call_count = Column(Integer, default=0)    # Max 2 for short calls
    
    # Rolloff
    rolled_off_date = Column(DateTime)
    rolloff_reason = Column(String(100))             # "3_check_marks", "quit", "dispatched"
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('member_id', 'book_id', 'registration_date'),
    )
```

#### 6. Registration Activity Log (NEW)

```python
# src/models/registration_activity.py

class RegistrationActivity(Base):
    """
    Audit trail for registration changes.
    Supplements the global audit log (ADR-012) with referral-specific detail.
    """
    __tablename__ = "registration_activities"
    
    id = Column(Integer, primary_key=True)
    registration_id = Column(Integer, ForeignKey("book_registrations.id"))
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("referral_books.id"))
    
    # Activity
    activity_date = Column(DateTime, nullable=False, default=func.now())
    action = Column(String(50), nullable=False)      # Enum
    details = Column(Text)
    
    # Source
    processor = Column(String(100))                  # "SYSTEM", "MEMBER VIA WEB", staff
    processor_id = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime, default=func.now())
```

> **Audit integration note:** RegistrationActivity provides referral-specific audit data (powering reports B-17, A-11, AP-02). The global audit log (ADR-012, immutability trigger) provides the compliance-grade immutable record. Both should be written for dispatch/registration actions — the global log for NLRA compliance, RegistrationActivity for operational queries.

### Phase 7D: Labor Requests & Dispatch

> **Builds on:** Organization model (Week 6) for employer FK, Audit logging (Week 11/ADR-012) for dispatch audit trail

#### 7. Labor Request Table (NEW)

```python
# src/models/labor_request.py

class LaborRequest(Base):
    """
    Employer request for workers.
    Based on Local 46 referral procedures.
    """
    __tablename__ = "labor_requests"
    
    id = Column(Integer, primary_key=True)
    
    # Request Info
    request_number = Column(Integer, unique=True)    # Auto-generated
    request_date = Column(DateTime, nullable=False)
    
    # Employer (FK to existing Organization model — Week 6)
    employer_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    employer_name = Column(String(200))              # Denormalized for display
    
    # Job Details
    job_class = Column(String(20), nullable=False)   # "JRY WIRE"
    book_id = Column(Integer, ForeignKey("referral_books.id"))
    book_name = Column(String(100))                  # "Wire Seattle"
    region = Column(String(50))                      # "SEATTLE"
    
    # Worksite
    worksite_name = Column(String(200))
    worksite_address = Column(Text)
    worksite_city = Column(String(100))
    worksite_state = Column(String(2), default="WA")
    
    # Position Details
    positions_requested = Column(Integer, default=1)
    positions_filled = Column(Integer, default=0)
    wage_rate = Column(Numeric(10, 2))               # $54.46/hr
    
    # Schedule
    start_date = Column(Date, nullable=False)
    start_time = Column(Time)                        # 07:00 AM
    estimated_duration_days = Column(Integer)
    
    # Request Type
    is_short_call = Column(Boolean, default=False)   # ≤10 business days
    is_long_call = Column(Boolean, default=False)
    is_by_name = Column(Boolean, default=False)      # Foreperson by name
    is_specialty = Column(Boolean, default=False)    # No check marks
    
    # Special Flags
    generates_check_marks = Column(Boolean, default=True)
    early_start = Column(Boolean, default=False)     # Before 6:00 AM
    
    # Requirements
    requirements = Column(Text)                      # "BIRTH CERTIFICATE, Drug Test, etc."
    comments = Column(Text)
    
    # PLA/CWA/TERO
    agreement_type = Column(String(50))              # "PLA", "CWA", "TERO", null
    
    # Status
    status = Column(String(20), default="open")      # Enum: open, filled, cancelled, expired
    
    # Internet Bidding
    bidding_enabled = Column(Boolean, default=True)
    bidding_opens = Column(DateTime)                 # 5:30 PM day before
    bidding_closes = Column(DateTime)                # 7:00 AM day of
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
```

#### 8. Dispatch Table (NEW)

```python
# src/models/dispatch.py

class Dispatch(Base):
    """
    Assignment of member to labor request.
    Creates corresponding MemberEmployment record on dispatch.
    All dispatch actions generate audit trail entries (ADR-012).
    """
    __tablename__ = "dispatches"
    
    id = Column(Integer, primary_key=True)
    
    # Links
    labor_request_id = Column(Integer, ForeignKey("labor_requests.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    registration_id = Column(Integer, ForeignKey("book_registrations.id"))
    
    # Dispatch Info
    dispatch_date = Column(DateTime, nullable=False)
    dispatch_method = Column(String(30))             # "morning_referral", "internet_bid", "by_name"
    
    # From Labor Request (denormalized)
    employer_id = Column(Integer, ForeignKey("organizations.id"))
    job_class = Column(String(20))
    worksite = Column(String(200))
    wage_rate = Column(Numeric(10, 2))
    
    # Status
    status = Column(String(20), default="dispatched")  # dispatched, checked_in, working, terminated
    
    # Check-in (must be by 3:00 PM)
    checked_in = Column(Boolean, default=False)
    check_in_time = Column(DateTime)
    check_in_deadline = Column(DateTime)             # 3:00 PM on dispatch day
    
    # Internet Bid Specific
    bid_submitted_at = Column(DateTime)
    bid_accepted = Column(Boolean)
    bid_rejected = Column(Boolean, default=False)
    rejection_reason = Column(String(100))
    
    # Employment Tracking
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)
    term_reason = Column(String(50))                 # Enum: rif, quit, fired, etc.
    days_worked = Column(Integer)
    
    # Short Call Tracking
    is_short_call = Column(Boolean, default=False)
    short_call_registration_restored = Column(Boolean, default=False)
    
    # Check Mark Generated
    generated_check_mark = Column(Boolean, default=False)
    
    # Link to Employment Record
    employment_id = Column(Integer, ForeignKey("member_employments.id"))
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
```

### Phase 7E: Skills & Qualifications

> **⚠️ CRITICAL: Member ≠ Student.** Skills tracked here are dispatch qualifications (certifications, licenses) used for referral eligibility. These are SEPARATE from JATC training records tracked via the Student model (linked to Member via FK on Student). Do not confuse or merge these concerns.

#### 9. Member Skill Table (NEW)

```python
# src/models/member_skill.py

class MemberSkill(Base):
    """
    Certifications, licenses, and qualifications for DISPATCH purposes.
    NOT JATC training records (those are on Student model via FK).
    """
    __tablename__ = "member_skills"
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    
    # Skill Info
    skill_name = Column(String(100), nullable=False)
    skill_code = Column(String(30))
    category = Column(String(50))                    # "license", "certification", "training"
    
    # Certification Details
    certification_number = Column(String(50))
    issuing_authority = Column(String(100))
    issue_date = Column(Date)
    expiration_date = Column(Date)
    
    # Status
    is_active = Column(Boolean, default=True)
    verified = Column(Boolean, default=False)
    verified_by_id = Column(Integer, ForeignKey("users.id"))
    verified_date = Column(Date)
    
    # Notes
    notes = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

#### 10. Member Qualified Book Table (NEW)

```python
# src/models/member_qualified_book.py

class MemberQualifiedBook(Base):
    """
    Which books a member is qualified to sign.
    """
    __tablename__ = "member_qualified_books"
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("referral_books.id"), nullable=False)
    
    # Qualification
    book_number = Column(Integer, default=1)         # 1 or 2
    qualification_date = Column(Date)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        UniqueConstraint('member_id', 'book_id'),
    )
```

---

## 📊 New Enums

> **Convention:** All enums go in `src/db/enums/`, import from `src.db.enums`. Phase 7 enums go in `src/db/enums/phase7_enums.py`.

```python
# src/db/enums/phase7_enums.py

from enum import Enum

class MemberType(str, Enum):
    """IBEW membership card types"""
    A = "A"                         # Journeyman Inside Wireman
    BA = "BA"                       # BA card
    CE = "CE"                       # Construction Electrician
    CW = "CW"                       # Construction Wireman
    APPRENTICE = "APP"

class ReferralStatus(str, Enum):
    """Member's referral availability"""
    AVAILABLE = "available"
    WORKING = "working"
    DISPATCHED = "dispatched"
    EXEMPT = "exempt"
    SUSPENDED = "suspended"

class ExemptReason(str, Enum):
    """Reasons for exempt status"""
    MILITARY = "military"
    UNION_BUSINESS = "union_business"
    SALTING = "salting"
    MEDICAL = "medical"
    JURY_DUTY = "jury_duty"
    UNDER_SCALE = "under_scale"
    TRAVELING = "traveling"

class BookClassification(str, Enum):
    """Job classifications for books"""
    INSIDE_WIREPERSON = "inside_wireperson"
    TRADESHOW = "tradeshow"
    SEATTLE_SCHOOL = "seattle_school"
    SOUND_COMM = "sound_comm"
    MARINE = "marine"
    STOCKPERSON = "stockperson"
    LIGHT_FIXTURE = "light_fixture"
    RESIDENTIAL = "residential"

class RegistrationStatus(str, Enum):
    """Status of book registration"""
    ACTIVE = "active"
    ROLLED_OFF = "rolled_off"
    DISPATCHED = "dispatched"
    EXPIRED = "expired"

class RegistrationAction(str, Enum):
    """Actions for registration activity log"""
    REGISTER = "register"
    RE_SIGN = "re_sign"
    CHECK_MARK = "check_mark"
    ROLL_OFF = "roll_off"
    DISPATCH = "dispatch"
    RESTORE = "restore"
    EXEMPT_START = "exempt_start"
    EXEMPT_END = "exempt_end"
    INTERNET_BID = "internet_bid"
    BID_REJECT = "bid_reject"
    POSITION_CHANGE = "position_change"

class RolloffReason(str, Enum):
    """Reasons for being rolled off books"""
    THREE_CHECK_MARKS = "3_check_marks"
    QUIT = "quit"
    DISCHARGE = "discharge"
    DISPATCHED = "dispatched"
    FAILED_RE_SIGN = "failed_re_sign"
    BID_REJECT_QUIT = "bid_reject_quit"
    MANUAL = "manual"

class LaborRequestStatus(str, Enum):
    """Status of labor requests"""
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class DispatchMethod(str, Enum):
    """How dispatch was made"""
    MORNING_REFERRAL = "morning_referral"
    INTERNET_BID = "internet_bid"
    EMAIL_BID = "email_bid"
    BY_NAME = "by_name"
    EMERGENCY = "emergency"

class DispatchStatus(str, Enum):
    """Status of dispatch"""
    DISPATCHED = "dispatched"
    CHECKED_IN = "checked_in"
    WORKING = "working"
    TERMINATED = "terminated"
    REJECTED = "rejected"
    NO_SHOW = "no_show"

class TermReason(str, Enum):
    """Termination reasons"""
    RIF = "rif"                     # Reduction in Force
    QUIT = "quit"
    FIRED = "fired"
    LAID_OFF = "laid_off"
    SHORT_CALL_END = "short_call_end"
    CONTRACT_END = "contract_end"
    NINETY_DAY_RULE = "90_day_rule"
    TURNAROUND = "turnaround"
    UNDER_SCALE = "under_scale"

class ActivityCode(str, Enum):
    """Transaction activity codes"""
    PAYMENT = "X"
    VOID = "V"
    DCO = "D"
    NEW_MEMBER = "N"
    ADJUSTMENT = "A"

class PaymentSource(str, Enum):
    """Payment sources"""
    DCO = "dco"                     # Dues Check-Off
    WEB = "web"
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "cc"
    MAIL = "mail"
    STRIPE_CARD = "stripe_card"
    STRIPE_ACH = "stripe_ach"
```

> **Schema reconciliation note:** The Referral & Dispatch Plan (`PHASE7_REFERRAL_DISPATCH_PLAN.md`) defines a slightly different enum set (e.g., separate `NoCheckMarkReason`, `BidStatus`, `JobClass`, `Region` enums and a `JobBid` model). Reconcile the two schemas in Session 20A to produce the authoritative model set.

---

## 🏗️ Seed Data

### Referral Books (Local 46)

> **Cross-reference:** `LOCAL46_REFERRAL_BOOKS.md` has the full book/classification mapping with open questions to resolve before seeding. Seed data must register in the existing registry-based ordering — see `docs/architecture/diagrams/seeds.mmd`.

```python
# src/seed/phase7_seed.py

REFERRAL_BOOKS = [
    # Inside Wireperson - Seattle (8:30 AM referral)
    {"name": "Wire Seattle", "code": "WIRE_SEA_1", "classification": "inside_wireperson",
     "book_number": 1, "region": "Seattle", "referral_start_time": "08:30:00"},
    {"name": "Wire Seattle", "code": "WIRE_SEA_2", "classification": "inside_wireperson",
     "book_number": 2, "region": "Seattle", "referral_start_time": "08:30:00"},
    
    # Inside Wireperson - Bremerton
    {"name": "Wire Bremerton", "code": "WIRE_BREM_1", "classification": "inside_wireperson",
     "book_number": 1, "region": "Bremerton", "referral_start_time": "08:30:00"},
    {"name": "Wire Bremerton", "code": "WIRE_BREM_2", "classification": "inside_wireperson",
     "book_number": 2, "region": "Bremerton", "referral_start_time": "08:30:00"},
    
    # Inside Wireperson - Port Angeles
    {"name": "Wire Port Angeles", "code": "WIRE_PA_1", "classification": "inside_wireperson",
     "book_number": 1, "region": "Port Angeles", "referral_start_time": "08:30:00"},
    {"name": "Wire Port Angeles", "code": "WIRE_PA_2", "classification": "inside_wireperson",
     "book_number": 2, "region": "Port Angeles", "referral_start_time": "08:30:00"},
    
    # Tradeshow (9:00 AM referral)
    {"name": "Tradeshow Seattle", "code": "TRADE_SEA_1", "classification": "tradeshow",
     "book_number": 1, "region": "Seattle", "referral_start_time": "09:00:00"},
    
    # Seattle School District (9:30 AM referral)
    {"name": "Seattle School District", "code": "SCHOOL_SEA_1", "classification": "seattle_school",
     "book_number": 1, "region": "Seattle", "referral_start_time": "09:30:00"},
    
    # Sound and Communication (9:30 AM referral)
    {"name": "Sound Seattle", "code": "SOUND_SEA_1", "classification": "sound_comm",
     "book_number": 1, "region": "Seattle", "referral_start_time": "09:30:00"},
    {"name": "Sound Seattle", "code": "SOUND_SEA_2", "classification": "sound_comm",
     "book_number": 2, "region": "Seattle", "referral_start_time": "09:30:00"},
    
    # Marine (9:30 AM referral)
    {"name": "Marine Seattle", "code": "MARINE_SEA_1", "classification": "marine",
     "book_number": 1, "region": "Seattle", "referral_start_time": "09:30:00"},
    
    # Residential (9:30 AM referral)
    {"name": "Residential Seattle", "code": "RES_SEA_1", "classification": "residential",
     "book_number": 1, "region": "Seattle", "referral_start_time": "09:30:00"},
]
```

---

## 📅 Implementation Schedule

### Week 20: Member & Financial Foundation
| Session | Hours | Focus |
|---------|-------|-------|
| 20A | 4 | Enums (`src/db/enums/phase7_enums.py`), Member model updates |
| 20B | 4 | MemberFinancial model, service |
| 20C | 4 | Tests (20+) |

### Week 21: Transaction System
| Session | Hours | Focus |
|---------|-------|-------|
| 21A | 4 | MemberTransaction model |
| 21B | 4 | Transaction service, balance calc (coexists with DuesPayment/Stripe) |
| 21C | 4 | API endpoints, tests (20+) |

### Week 22: Referral Books
| Session | Hours | Focus |
|---------|-------|-------|
| 22A | 4 | ReferralBook model, seed data (registry integration) |
| 22B | 4 | BookRegistration model |
| 22C | 4 | RegistrationActivity, tests |

### Week 23: Registration Business Logic
| Session | Hours | Focus |
|---------|-------|-------|
| 23A | 4 | Re-sign logic, deadline tracking |
| 23B | 4 | Check mark logic, rolloff rules |
| 23C | 4 | Position management, tests |

### Week 24: Labor Requests
| Session | Hours | Focus |
|---------|-------|-------|
| 24A | 4 | LaborRequest model |
| 24B | 4 | Request service, validation rules |
| 24C | 4 | Internet bidding logic, tests |

### Week 25: Dispatch System
| Session | Hours | Focus |
|---------|-------|-------|
| 25A | 4 | Dispatch model |
| 25B | 4 | Dispatch service, employment creation, audit trail integration (ADR-012) |
| 25C | 4 | Short call logic, tests |

### Week 26-27: Transaction UI
> **Frontend patterns:** Follow ADR-002 (Jinja2 + HTMX + Alpine.js) and ADR-010 (list/detail/form patterns)

| Session | Hours | Focus |
|---------|-------|-------|
| 26A | 4 | Transaction list page |
| 26B | 4 | Transaction detail, recording |
| 27A | 4 | DCO import tool |
| 27B | 4 | Payment reports |

### Week 28-29: Dispatch UI
> **Frontend patterns:** Follow ADR-002, ADR-010. PWA considerations from Week 18 for dispatch window use.

| Session | Hours | Focus |
|---------|-------|-------|
| 28A | 4 | Book list, detail pages |
| 28B | 4 | Registration form |
| 29A | 4 | Labor request management |
| 29B | 4 | Dispatch workflow UI |

### Week 30: Integration & Reports
| Session | Hours | Focus |
|---------|-------|-------|
| 30A | 4 | Payment history report (match LaborPower format; PDF via WeasyPrint) |
| 30B | 4 | Out-of-work reports |
| 30C | 4 | End-to-end testing |

### Week 31-32: Skills & Polish (Optional)
| Session | Hours | Focus |
|---------|-------|-------|
| 31A | 4 | MemberSkill model (**dispatch skills only — NOT JATC training**) |
| 31B | 4 | MemberQualifiedBook model |
| 32A | 4 | Skills UI |
| 32B | 4 | Documentation, ADRs (ADR-015-referral-dispatch-system) |

### Report Sprints (Overlap with Weeks 29-32+)

> **Cross-reference:** See `LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` for the full ~78-report inventory and `PHASE7_CONTINUITY_DOC_ADDENDUM.md` for schedule reconciliation.

| Sprint | Weeks | Reports | Notes |
|--------|-------|---------|-------|
| Sprint 1 | 29-30 | ~16 P0 Critical | Overlaps Week 30 Integration |
| Sprint 2 | 30-31 | ~33 P1 High | Overlaps Week 31 Skills |
| Sprint 3 | 32+ | ~29 P2/P3 | After core Phase 7 completion |

> **Schedule note:** Report sprints share sessions with the core schedule above. Coordinate within each week to avoid conflicts. If report infrastructure (filter framework, export templates) takes longer than expected, Phase 7E (Skills) may shift.

---

## ✅ Acceptance Criteria

### Transaction System
- [ ] Track basic and working dues separately
- [ ] Calculate running credit balance
- [ ] Support all payment sources (DCO, web, cash, CC)
- [ ] Generate report matching LaborPower format (PDF via WeasyPrint)
- [ ] Integrate with existing Stripe payments (coexist with DuesPayment model)

### Referral System
- [ ] All Local 46 books seeded with correct schedules
- [ ] Registration requires in-person or email
- [ ] 30-day re-sign enforcement
- [ ] 2 check marks allowed, 3rd = rolloff
- [ ] Check marks don't cross regions
- [ ] Max 1 check mark per book per day

### Labor Requests & Dispatch
- [ ] Track all request details from LaborPower
- [ ] Internet bidding window (5:30 PM - 7:00 AM)
- [ ] Check-in deadline (3:00 PM)
- [ ] Short call logic (≤10 days, 2x limit)
- [ ] Reject after bid = quit handling
- [ ] By-name 2-week restriction after quit

### Integration
- [ ] Dispatch creates MemberEmployment record
- [ ] Registration status updates on dispatch
- [ ] Audit trail for all changes (ADR-012 immutability trigger)
- [ ] All dispatch actions logged to both RegistrationActivity and global audit log

---

## 📝 End-of-Session Documentation (MANDATORY)

**CRITICAL:** Before completing each session:

> **Update *ANY* and *ALL* relevant documents to capture progress. Scan `/docs/*` and make or create relevant updates. Do not forget about ADRs—update as necessary.**

### Required Updates
- [ ] `/CHANGELOG.md`
- [ ] `/CLAUDE.md`
- [ ] `/docs/IP2A_MILESTONE_CHECKLIST.md`
- [ ] `/docs/decisions/ADR-015-*.md` (as needed)
- [ ] `/docs/reports/session-logs/YYYY-MM-DD-*.md`

See `/docs/standards/END_OF_SESSION_DOCUMENTATION.md` for full checklist.

---

## 🚀 Ready to Start

Copy these files to your project:
1. `PHASE7_IMPLEMENTATION_PLAN_v2.md` → `docs/phase7/`
2. Update `CLAUDE.md` with Phase 7 overview
3. Begin with Week 20 Session A

**First session command:**
```
I'm starting IP2A-Database-v2 Phase 7 - Week 20 Session A.

Read:
1. /CLAUDE.md
2. /docs/phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md

Task: Create src/db/enums/phase7_enums.py with all new enums.
Then update Member model with new IBEW fields.
```

> **⚠️ Session 20A prerequisite:** Before creating enums, reconcile the two schema proposals (this document vs. `PHASE7_REFERRAL_DISPATCH_PLAN.md`) to produce one authoritative model set. Key differences: this doc combines bids into the Dispatch model; the Dispatch Plan has a separate JobBid model. Resolve before writing code.

---

Document Version: 2.1
Last Updated: February 3, 2026
Previous Version: 2.0 (February 2, 2026 — Initial v2 plan with Local 46 rules)

*Phase 7 Implementation Plan v2.1*
*Based on IBEW Local 46 Referral Procedures (Oct 4, 2024)*
