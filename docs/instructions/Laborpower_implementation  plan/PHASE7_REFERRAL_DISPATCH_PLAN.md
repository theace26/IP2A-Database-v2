# IP2A-Database-v2: Phase 7 - Dispatch & Referral System

> **Document Created:** February 2, 2026
> **Last Updated:** February 3, 2026 (Batch 4b documentation update)
> **Version:** 2.1
> **Status:** Ready for Implementation — Reconcile with Implementation Plan v2 in Session 20A
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1-19)
> **Source:** IBEW Local 46 Referral Procedures (Effective October 4, 2024)

---

## Related Documents

| Document | Location | Relationship |
|----------|----------|-------------|
| Phase 7 Implementation Plan v2 | `docs/phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md` | Alternate schema (combined bid/dispatch) — **reconcile in Session 20A** |
| LaborPower Gap Analysis | `docs/phase7/LABORPOWER_GAP_ANALYSIS.md` | Feature gaps that Phase 7 addresses |
| LaborPower Implementation Plan | `docs/phase7/LABORPOWER_IMPLEMENTATION_PLAN.md` | Original 6-phase build schedule |
| LaborPower Reports Inventory | `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` | ~78 reports these models must power |
| Local 46 Referral Books | `docs/phase7/LOCAL46_REFERRAL_BOOKS.md` | Book/classification seed data reference |
| Phase 7 Continuity Doc | `docs/phase7/PHASE7_CONTINUITY_DOC.md` | Session-by-session continuity notes |
| Phase 7 Continuity Addendum | `docs/phase7/PHASE7_CONTINUITY_DOC_ADDENDUM.md` | Report sprint schedule overlap notes |
| ADR-008 Dues Tracking | `docs/decisions/ADR-008-dues-tracking-system.md` | Existing DuesPayment model context |
| ADR-012 Audit Logging | `docs/decisions/ADR-012-audit-logging.md` | Immutability trigger — dispatch must integrate |
| ADR-013 Stripe Integration | `docs/decisions/ADR-013-stripe-payment-integration.md` | Existing payment infrastructure |
| ADR-014 Grant Compliance | `docs/decisions/ADR-014-grant-compliance-reporting.md` | WeasyPrint + openpyxl report export |

---

## Current Baseline (v0.9.4-alpha)

Phase 7 builds on 19 weeks of completed work:

| Metric | Current Value |
|--------|--------------|
| **Version** | v0.9.4-alpha — FEATURE-COMPLETE (Weeks 1-19) |
| **Tests** | ~470 total |
| **API Endpoints** | ~150 |
| **ORM Models** | 26 (Phase 7 adds ~14 new tables) |
| **Deployment** | Railway (prod), Render (backup) |
| **Reports** | WeasyPrint PDF + openpyxl Excel + Chart.js dashboard |
| **Mobile** | PWA with offline support |

### Key Integration Points

| Existing Feature | Phase 7 Interaction |
|-----------------|---------------------|
| **Organization model** (Week 6) | LaborRequest.employer_id → organizations.id |
| **Member model** (Week 5) | All referral/dispatch models FK to members.id |
| **Audit logging** (Week 11/ADR-012) | Dispatch and registration actions MUST write to global audit trail |
| **WeasyPrint** (Week 14/ADR-014) | PDF generation for out-of-work lists, dispatch reports |
| **Chart.js** (Week 19) | Dashboard integration for unemployed counts, dispatch metrics |
| **PWA** (Week 18) | Dispatch window UI must be touch-friendly and mobile-responsive |

### Architecture Reminders

- **Enums** always in `src/db/enums/`, import from `src.db.enums`
- **Member is SEPARATE from Student** (linked via FK on Student) — dispatch qualifications ≠ JATC training
- **User** model uses `locked_until` datetime field (NOT boolean `is_locked`)
- **Seed data** follows registry-based ordering — new Phase 7 seeds must register in the correct dependency order (see `docs/architecture/diagrams/seeds.mmd`)

---

## ⚠️ Schema Reconciliation Required (Session 20A)

> **This document and `PHASE7_IMPLEMENTATION_PLAN_v2.md` propose overlapping but different schema designs.** Key differences that must be resolved before writing code:
>
> | Aspect | This Document | Implementation Plan v2 |
> |--------|---------------|----------------------|
> | **Job Bids** | Separate `JobBid` model | Bid fields embedded in `Dispatch` model |
> | **ReferralBook fields** | `job_class`, `skill_type`, `morning_referral_time`, `allows_online_bidding` | `classification`, `referral_start_time`, `internet_bidding_enabled` |
> | **BookRegistration exempt fields** | `is_exempt`, `exempt_reason`, `exempt_start_date`, `exempt_end_date` on registration | `is_exempt`, `exempt_reason`, `exempt_until` on Member model |
> | **Dispatch employer_id** | Required (`nullable=False`) | Optional (nullable) |
> | **Enum file** | `src/db/enums/referral_enums.py` | `src/db/enums/phase7_enums.py` |
> | **Additional enums** | `NoCheckMarkReason`, `BidStatus`, `JobClass`, `Region` | Not present |
>
> **Recommendation:** Use this document's more detailed models (separate JobBid, richer enums) as the base, with the Implementation Plan v2's scheduling and integration notes. Produce one authoritative schema in Session 20A.

---

## 📋 Executive Summary

Phase 7 implements the Out-of-Work List (Referral) and Dispatch system based on the official IBEW Local 46 Referral Procedures document. This is the core daily workflow of the union hall.

**Key Components:**
1. Referral Books (Out-of-Work Lists)
2. Member Registration & Re-Sign
3. Labor Requests from Employers
4. Job Bidding (Online & In-Person)
5. Dispatch Workflow
6. Check Mark System
7. Enhanced Transaction Tracking

---

## 🏛️ IBEW Local 46 Referral Rules (From Official Document)

### Office Hours & Locations

| Location | Hours | Phone |
|----------|-------|-------|
| Kent Office | 8:00 AM - 5:00 PM | 253-395-6530 |
| Bremerton Office | 8:00 AM - 3:00 PM | - |

**Email:** dispatch1@ibew46.com
**Fax:** 253-395-6539
**Job Line:** 253-395-6516
**Website:** www.ibew46.org

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
- **Method:** In person or via email only
- **Restriction:** May only sign highest priority book/list for ONE wire/tradeshow combination
- **Timing:** Registration requests not processed before completion of Inside Wireperson Book 1 Referral

#### Re-Sign Requirements
- **Frequency:** Every 30 days or less from Registration date or last Re-sign
- **Methods:** In person, by fax, by Internet, or via email

#### Re-Registration (After Termination)
- Required for: Short Call terminations, Under Scale terminations, 90 Day Rule, Turnarounds
- **Deadline:** By end of next normal working day to avoid being rolled off all Books
- Must be done every day before Referral process starts

#### Check Mark System
| Rule | Description |
|------|-------------|
| Allowed | 2 check marks without penalty |
| Third check mark | Rolled completely off the book |
| After roll-off | Must re-register in person or via email |
| Cross-area | Seattle, Bremerton, Port Angeles are SEPARATE - requests for one don't affect others |
| Lower priority | Requests falling to lower priority list give higher priority list a check mark |
| Unfilled requests | Give ALL registrants on that book a check mark |
| Maximum | 1 check mark per book, per day |

#### No Check Marks For
- Specialty requests/skills not in CBA
- MOU jobsites
- Start times before 6:00 AM
- Under scale work recovery jobs
- Various location requests
- Short call requests
- Rejection of applicant by employer

#### Internet/Email Bidding
- **Hours:** 5:30 PM to 7:00 AM
- **Requirement:** Must check in with employer by 3:00 PM on dispatch day or be rolled off
- **Rejection:** Rejecting referral after bidding = quit
- **Penalty:** Second rejection in 12 months = lose Internet/Email privileges for ONE YEAR
- **"In Person" dispatch:** Required during computer/electronic failure

#### Short Calls
- **Definition:** Jobs 10 business days or less (not counting referral day or holidays)
- **Limit:** Registration restored to "unemployed status" twice for short calls
- **Exception:** 3 normal working days or less = no limit
- **"Long Call":** Laid off within Short Call period = registration restored
- **Friday rule:** If Short Call ends Friday, may work weekend and report Monday

#### Quit or Discharge
- **Effect:** Rolled completely off ALL Books
- **Foreperson restriction:** Cannot fill "Foreperson-by-Name" request for that employer for 2 weeks

#### Exempt Status (No Re-Sign Required)
- Military service
- Union business
- Salting
- Medically unfit
- Jury duty
- Working under scale or traveling
- **Duration:** Up to 6 months unless Business Manager approves extension

---

## 🗄️ Database Schema

### 1. Referral Books

```python
# src/models/referral_book.py

class ReferralBook(Base):
    """
    Out-of-work list definition.
    Each book represents a specific classification + region combination.
    """
    __tablename__ = "referral_books"
    
    id = Column(Integer, primary_key=True)
    
    # Identification
    name = Column(String(100), nullable=False)          # "WIRE SEATTLE"
    code = Column(String(30), unique=True, nullable=False)  # "WIRE_SEA_1"
    book_number = Column(Integer, default=1)            # 1 = local members, 2 = travelers
    
    # Classification
    job_class = Column(String(30), nullable=False)      # "JRY WIRE", "SOUND", "RESIDENTIAL"
    skill_type = Column(String(30))                     # "wire", "sound", "residential"
    
    # Region (CRITICAL - separate check mark tracking)
    region = Column(String(30), nullable=False)         # "SEATTLE", "BREMERTON", "PT_ANGELES"
    
    # Referral timing
    morning_referral_time = Column(Time)                # 8:30 AM for Inside Wire
    
    # Rules
    re_sign_days = Column(Integer, default=30)          # Must re-sign every X days
    max_check_marks = Column(Integer, default=2)        # Rolled off after X+1 check marks
    
    # Status
    is_active = Column(Boolean, default=True)
    allows_online_bidding = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    registrations = relationship("BookRegistration", back_populates="book")
    labor_requests = relationship("LaborRequest", back_populates="book")
```

> **Seed data note:** See `LOCAL46_REFERRAL_BOOKS.md` for the complete book/classification mapping. Seed data must register in the existing registry-based ordering (see `seeds.mmd` diagram). Open questions about field naming (this doc uses `job_class`/`skill_type`; Implementation Plan v2 uses `classification`) must be resolved in Session 20A.

### 2. Book Registration (Member on List)

```python
# src/models/book_registration.py

class BookRegistration(Base):
    """
    Tracks a member's position on an out-of-work list.
    """
    __tablename__ = "book_registrations"
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("referral_books.id"), nullable=False, index=True)
    
    # Registration tracking
    registration_date = Column(DateTime, nullable=False)
    registration_number = Column(Integer)               # Queue position at registration
    current_position = Column(Integer)                  # Current queue position
    
    # Status
    status = Column(String(20), default="active")       # active, rolled_off, dispatched, exempt
    
    # Re-sign tracking (every 30 days per rules)
    last_re_sign_date = Column(DateTime)
    re_sign_deadline = Column(DateTime)                 # 30 days from last re-sign
    
    # Check marks (rolled off at 3)
    check_marks = Column(Integer, default=0)
    last_check_mark_date = Column(Date)                 # Max 1 per day
    
    # Short call tracking
    short_call_restorations = Column(Integer, default=0)  # Max 2 per rules
    
    # Exempt status
    is_exempt = Column(Boolean, default=False)
    exempt_reason = Column(String(50))                  # military, union_business, salting, medical, jury, etc.
    exempt_start_date = Column(Date)
    exempt_end_date = Column(Date)                      # Max 6 months unless extended
    
    # Termination tracking
    date_rolled_off = Column(DateTime)
    roll_off_reason = Column(String(100))               # "3rd check mark", "quit", "90 day rule", etc.
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    member = relationship("Member", back_populates="book_registrations")
    book = relationship("ReferralBook", back_populates="registrations")
    activities = relationship("RegistrationActivity", back_populates="registration")
```

> **Schema note:** This places exempt fields on BookRegistration (per-book exempt status). Implementation Plan v2 places them on the Member model (global exempt status). Resolve in Session 20A — consider whether a member can be exempt on one book but not another, or if exempt status is always global.

### 3. Labor Request (Employer Job Posting)

```python
# src/models/labor_request.py

class LaborRequest(Base):
    """
    Employer request for workers.
    Must be received by 3:00 PM for next morning referral.
    """
    __tablename__ = "labor_requests"
    
    id = Column(Integer, primary_key=True)
    
    # Employer info (FK to existing Organization model — Week 6)
    employer_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Book/Classification
    book_id = Column(Integer, ForeignKey("referral_books.id"), nullable=False)
    job_class = Column(String(30), nullable=False)      # "JRY WIRE"
    
    # Request details
    request_date = Column(DateTime, nullable=False)
    request_number = Column(String(20))                 # Internal tracking #
    
    # Job details
    positions_requested = Column(Integer, default=1)
    positions_filled = Column(Integer, default=0)
    
    wage_rate = Column(Numeric(10, 2))                  # $54.46/hr
    
    start_date = Column(Date, nullable=False)
    start_time = Column(Time)                           # 07:00 AM
    estimated_duration_days = Column(Integer)
    
    # Short call determination
    is_short_call = Column(Boolean, default=False)      # 10 business days or less
    
    # Location
    region = Column(String(30))                         # SEATTLE, BREMERTON, PT_ANGELES
    worksite_name = Column(String(200))
    worksite_address = Column(String(300))
    city = Column(String(100))
    state = Column(String(2), default="WA")
    report_to_address = Column(String(300))             # May differ from worksite
    
    # Requirements (from job posting)
    requirements = Column(Text)                         # "Wireman Journeyman, BIRTH CERTIFICATE..."
    comments = Column(Text)                             # "Phone interview mandatory. OSHA 30..."
    
    # Check mark rules
    generates_check_mark = Column(Boolean, default=True)
    no_check_mark_reason = Column(String(100))          # specialty, mou, early_start, etc.
    
    # Special request types
    is_foreperson_by_name = Column(Boolean, default=False)
    foreperson_member_id = Column(Integer, ForeignKey("members.id"))
    
    # Status
    status = Column(String(20), default="open")         # open, filled, cancelled, expired
    
    # Online bidding
    allows_online_bidding = Column(Boolean, default=True)
    bidding_opens_at = Column(DateTime)                 # 5:30 PM day before
    bidding_closes_at = Column(DateTime)                # 7:00 AM day of
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    employer = relationship("Organization")
    book = relationship("ReferralBook", back_populates="labor_requests")
    dispatches = relationship("Dispatch", back_populates="labor_request")
    bids = relationship("JobBid", back_populates="labor_request")
```

### 4. Job Bid (Online/Email Bidding)

> **Note:** This model is unique to this document. The Implementation Plan v2 embeds bid tracking fields directly in the Dispatch model. This separate model provides better audit trail granularity and cleaner query patterns for bid history reports (B-18, AP-08, C-42, C-43, C-44). **Recommend keeping as separate model — resolve in Session 20A.**

```python
# src/models/job_bid.py

class JobBid(Base):
    """
    Member bid on a labor request.
    Online bidding: 5:30 PM to 7:00 AM
    """
    __tablename__ = "job_bids"
    
    id = Column(Integer, primary_key=True)
    
    labor_request_id = Column(Integer, ForeignKey("labor_requests.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    registration_id = Column(Integer, ForeignKey("book_registrations.id"))
    
    # Bid details
    bid_date = Column(DateTime, nullable=False)
    bid_method = Column(String(20))                     # "online", "email", "in_person"
    queue_position_at_bid = Column(Integer)             # Position when bid placed
    
    # Status
    status = Column(String(20), default="pending")      # pending, accepted, rejected, withdrawn
    
    # Outcome
    was_dispatched = Column(Boolean, default=False)
    rejection_reason = Column(String(100))              # If member rejected after acceptance
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    processed_at = Column(DateTime)
    
    # Relationships
    labor_request = relationship("LaborRequest", back_populates="bids")
    member = relationship("Member")
    registration = relationship("BookRegistration")
```

### 5. Dispatch (Job Assignment)

```python
# src/models/dispatch.py

class Dispatch(Base):
    """
    Actual job assignment from labor request to member.
    Creates corresponding MemberEmployment record.
    All dispatch actions MUST generate audit trail entries (ADR-012 immutability trigger).
    """
    __tablename__ = "dispatches"
    
    id = Column(Integer, primary_key=True)
    
    # Core relationships
    labor_request_id = Column(Integer, ForeignKey("labor_requests.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    registration_id = Column(Integer, ForeignKey("book_registrations.id"))
    employer_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Dispatch details
    dispatch_date = Column(DateTime, nullable=False)
    dispatch_method = Column(String(20))                # "morning_referral", "online_bid", "by_name"
    
    # Job classification
    job_class = Column(String(30))
    book_code = Column(String(30))
    wage_rate = Column(Numeric(10, 2))
    
    # Worksite
    worksite = Column(String(200))
    city = Column(String(100))
    
    # Start details
    start_date = Column(Date)
    start_time = Column(Time)
    
    # Short call tracking
    is_short_call = Column(Boolean, default=False)
    
    # Employer check-in requirement (by 3:00 PM)
    check_in_deadline = Column(DateTime)
    checked_in_at = Column(DateTime)
    checked_in = Column(Boolean, default=False)
    
    # Termination
    term_date = Column(Date)
    term_reason = Column(String(50))                    # rif, quit, discharged, short_call_end
    
    # Time tracking
    days_worked = Column(Integer)
    
    # Link to employment record (existing MemberEmployment model)
    employment_id = Column(Integer, ForeignKey("member_employments.id"))
    
    # Status
    status = Column(String(20), default="dispatched")   # dispatched, working, completed, quit, discharged
    
    # Foreperson restriction tracking
    foreperson_restriction_until = Column(Date)         # Can't fill by-name for 2 weeks after quit
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    labor_request = relationship("LaborRequest", back_populates="dispatches")
    member = relationship("Member")
    registration = relationship("BookRegistration")
    employer = relationship("Organization")
    employment = relationship("MemberEmployment")
```

### 6. Registration Activity (Audit Trail)

```python
# src/models/registration_activity.py

class RegistrationActivity(Base):
    """
    Complete audit trail for all registration changes.
    Supplements the global audit log (ADR-012) with referral-specific detail.
    Powers historical reports: B-17, A-11, AP-02, C-42.
    """
    __tablename__ = "registration_activities"
    
    id = Column(Integer, primary_key=True)
    
    registration_id = Column(Integer, ForeignKey("book_registrations.id"))
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("referral_books.id"))
    
    # Activity details
    activity_date = Column(DateTime, nullable=False)
    action = Column(String(50), nullable=False)         # See RegistrationAction enum
    
    # Context
    details = Column(Text)                              # "BOOK: WIRE SEATTLE [1]"
    old_value = Column(String(200))                     # Previous state
    new_value = Column(String(200))                     # New state
    
    # Related entities
    labor_request_id = Column(Integer, ForeignKey("labor_requests.id"))
    dispatch_id = Column(Integer, ForeignKey("dispatches.id"))
    
    # Who did it
    processor = Column(String(100))                     # "SYSTEM", "MEMBER VIA WEB", staff name
    processor_user_id = Column(Integer, ForeignKey("users.id"))
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    registration = relationship("BookRegistration", back_populates="activities")
    member = relationship("Member")
    book = relationship("ReferralBook")
```

> **Dual audit note:** RegistrationActivity provides referral-specific audit data for operational queries and reports. The global audit log (ADR-012, PostgreSQL immutability trigger) provides the NLRA 7-year compliance record. Both should fire for dispatch/registration actions.

---

## 📊 Enums

> **Convention:** All enums go in `src/db/enums/`, import from `src.db.enums`. This document proposes `referral_enums.py`; Implementation Plan v2 proposes `phase7_enums.py`. Reconcile in Session 20A — may combine into one file or keep separate by domain.

```python
# src/db/enums/referral_enums.py

class RegistrationStatus(str, Enum):
    """Status of a book registration"""
    ACTIVE = "active"
    ROLLED_OFF = "rolled_off"
    DISPATCHED = "dispatched"
    EXEMPT = "exempt"
    QUIT = "quit"
    DISCHARGED = "discharged"

class RegistrationAction(str, Enum):
    """Actions that can occur on a registration"""
    REGISTER = "register"
    RE_SIGN = "re_sign"
    RE_REGISTER = "re_register"         # After being rolled off
    CHECK_MARK = "check_mark"
    ROLLED_OFF = "rolled_off"
    DISPATCHED = "dispatched"
    QUIT = "quit"
    DISCHARGED = "discharged"
    SHORT_CALL_END = "short_call_end"
    RESTORED = "restored"               # Registration restored after short call
    EXEMPT_START = "exempt_start"
    EXEMPT_END = "exempt_end"
    POSITION_CHANGE = "position_change"
    MANUAL_EDIT = "manual_edit"

class ExemptReason(str, Enum):
    """Reasons for exempt status (no re-sign required)"""
    MILITARY = "military"
    UNION_BUSINESS = "union_business"
    SALTING = "salting"
    MEDICAL = "medical"
    JURY_DUTY = "jury_duty"
    UNDER_SCALE = "under_scale"
    TRAVELING = "traveling"

class RollOffReason(str, Enum):
    """Reasons for being rolled off the book"""
    CHECK_MARKS = "check_marks"         # 3rd check mark
    QUIT = "quit"
    DISCHARGED = "discharged"
    NINETY_DAY_RULE = "90_day_rule"
    MISSED_RE_SIGN = "missed_re_sign"
    REJECTED_REFERRAL = "rejected_referral"  # After online bid acceptance

class LaborRequestStatus(str, Enum):
    """Status of a labor request"""
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class NoCheckMarkReason(str, Enum):
    """Reasons a request doesn't generate check marks"""
    SPECIALTY = "specialty"
    MOU_JOBSITE = "mou_jobsite"
    EARLY_START = "early_start"         # Before 6:00 AM
    UNDER_SCALE = "under_scale"
    VARIOUS_LOCATION = "various_location"
    SHORT_CALL = "short_call"
    EMPLOYER_REJECTION = "employer_rejection"

class BidStatus(str, Enum):
    """Status of a job bid"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"

class DispatchMethod(str, Enum):
    """How the dispatch was made"""
    MORNING_REFERRAL = "morning_referral"
    ONLINE_BID = "online_bid"
    EMAIL_BID = "email_bid"
    IN_PERSON = "in_person"
    BY_NAME = "by_name"
    EMERGENCY = "emergency"

class TermReason(str, Enum):
    """Employment termination reasons"""
    RIF = "rif"                         # Reduction in Force
    QUIT = "quit"
    DISCHARGED = "discharged"
    SHORT_CALL_END = "short_call_end"
    CONTRACT_END = "contract_end"
    TURNAROUND = "turnaround"

class JobClass(str, Enum):
    """Job classifications"""
    JRY_WIRE = "JRY WIRE"               # Journeyman Wireman
    SOUND = "SOUND"                     # Sound & Communication
    RESIDENTIAL = "RESIDENTIAL"
    MARINE = "MARINE"
    STOCKPERSON = "STOCKPERSON"
    LIGHT_FIXTURE = "LIGHT_FIXTURE"
    TRADESHOW = "TRADESHOW"

class Region(str, Enum):
    """Geographic regions (separate check mark tracking)"""
    SEATTLE = "SEATTLE"
    BREMERTON = "BREMERTON"
    PT_ANGELES = "PT_ANGELES"
```

> **This enum set is richer than Implementation Plan v2's.** Unique additions: `NoCheckMarkReason`, `BidStatus`, `JobClass`, `Region`, plus more granular `RegistrationAction` and `RegistrationStatus` values. Recommend adopting these during reconciliation.

---

## 📅 Implementation Schedule

> **Note:** This schedule differs slightly from `PHASE7_IMPLEMENTATION_PLAN_v2.md`. The Implementation Plan v2 has a different session breakdown and includes Transaction/Financial phases not covered here. Use the Implementation Plan v2 as the authoritative schedule and this document as the authoritative schema reference. Reconcile in Session 20A.

### Week 20: Core Models
| Session | Hours | Focus |
|---------|-------|-------|
| 20A | 4 | Enums, ReferralBook model |
| 20B | 4 | BookRegistration model |
| 20C | 4 | LaborRequest model |

### Week 21: Dispatch Models
| Session | Hours | Focus |
|---------|-------|-------|
| 21A | 4 | JobBid model |
| 21B | 4 | Dispatch model |
| 21C | 4 | RegistrationActivity model |

### Week 22: Services - Registration
| Session | Hours | Focus |
|---------|-------|-------|
| 22A | 4 | ReferralBookService, seed data (integrate with registry-based ordering) |
| 22B | 4 | BookRegistrationService (register, re-sign) |
| 22C | 4 | Check mark logic, roll-off rules |

### Week 23: Services - Dispatch
| Session | Hours | Focus |
|---------|-------|-------|
| 23A | 4 | LaborRequestService |
| 23B | 4 | JobBidService (online bidding rules) |
| 23C | 4 | DispatchService (dispatch workflow, audit trail integration) |

### Week 24: Queue Management
| Session | Hours | Focus |
|---------|-------|-------|
| 24A | 4 | QueueService (position calculations) |
| 24B | 4 | Re-sign deadline enforcement |
| 24C | 4 | Short call restoration logic |

### Week 25: API Endpoints
| Session | Hours | Focus |
|---------|-------|-------|
| 25A | 4 | Book/Registration API |
| 25B | 4 | LaborRequest/Bid API |
| 25C | 4 | Dispatch API |

### Week 26: Frontend - Books
> **Frontend patterns:** Follow ADR-002 (Jinja2 + HTMX + Alpine.js) and ADR-010 (list/detail/form patterns). PWA considerations from Week 18.

| Session | Hours | Focus |
|---------|-------|-------|
| 26A | 4 | Book list, book detail pages |
| 26B | 4 | Registration form, queue display |
| 26C | 4 | Re-sign workflow |

### Week 27: Frontend - Labor Requests
| Session | Hours | Focus |
|---------|-------|-------|
| 27A | 4 | Labor request list (like job posting screenshot) |
| 27B | 4 | Request detail, bid interface |
| 27C | 4 | Request creation form |

### Week 28: Frontend - Dispatch
| Session | Hours | Focus |
|---------|-------|-------|
| 28A | 4 | Morning referral workflow |
| 28B | 4 | Dispatch confirmation, check-in tracking |
| 28C | 4 | Termination workflow |

### Week 29: Integration & Reports
| Session | Hours | Focus |
|---------|-------|-------|
| 29A | 4 | Integration with MemberEmployment |
| 29B | 4 | Activity reports (PDF via WeasyPrint, CSV via openpyxl) |
| 29C | 4 | Out-of-work reports |

### Week 30: Testing & Polish
| Session | Hours | Focus |
|---------|-------|-------|
| 30A | 4 | Unit tests (50+ tests) |
| 30B | 4 | Integration tests |
| 30C | 4 | Documentation, ADRs (ADR-015-referral-dispatch-system) |

### Report Sprints (Weeks 29-32+)

> **Cross-reference:** See `LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` for the full ~78-report inventory.

| Sprint | Weeks | Reports | Notes |
|--------|-------|---------|-------|
| Sprint 1 | 29-30 | ~16 P0 Critical | Concurrent with Integration & Testing |
| Sprint 2 | 30-31 | ~33 P1 High | After core testing |
| Sprint 3 | 32+ | ~29 P2/P3 | As time allows |

---

## 🎯 Acceptance Criteria

### Registration System
- [ ] Members can register on books (in person/email simulation)
- [ ] Registration number assigned based on queue position
- [ ] Re-sign deadline tracked (30 days)
- [ ] Re-sign resets deadline
- [ ] Exempt status pauses re-sign requirement

### Check Mark System
- [ ] Check marks assigned per rules
- [ ] Max 1 check mark per book per day
- [ ] 3rd check mark rolls member off
- [ ] Cross-region requests don't generate check marks
- [ ] "No check mark" reasons respected

### Labor Requests
- [ ] Employers can submit requests
- [ ] Short call auto-detection (≤10 days)
- [ ] Online bidding window (5:30 PM - 7:00 AM)
- [ ] Bid queue based on registration position

### Dispatch
- [ ] Morning referral workflow
- [ ] Online bid acceptance
- [ ] 3:00 PM check-in deadline
- [ ] Creates MemberEmployment record
- [ ] Quit/discharge rolls off all books

### Short Call Rules
- [ ] Restoration limited to 2x
- [ ] 3-day-or-less exception
- [ ] "Long Call" restoration
- [ ] Friday weekend rule

### Audit & Compliance
- [ ] All dispatch actions logged to RegistrationActivity
- [ ] All dispatch actions logged to global audit trail (ADR-012)
- [ ] NLRA 7-year compliance via immutability trigger

---

## 📁 Seed Data

### Referral Books

> **Cross-reference:** See `LOCAL46_REFERRAL_BOOKS.md` for the full classification mapping and open questions.

```python
REFERRAL_BOOKS = [
    # Inside Wireman - Seattle
    {"name": "WIRE SEATTLE", "code": "WIRE_SEA_1", "book_number": 1, 
     "job_class": "JRY WIRE", "region": "SEATTLE", "morning_referral_time": "08:30"},
    {"name": "WIRE SEATTLE", "code": "WIRE_SEA_2", "book_number": 2,
     "job_class": "JRY WIRE", "region": "SEATTLE", "morning_referral_time": "08:30"},
    
    # Inside Wireman - Bremerton
    {"name": "WIRE BREMERTON", "code": "WIRE_BREM_1", "book_number": 1,
     "job_class": "JRY WIRE", "region": "BREMERTON", "morning_referral_time": "08:30"},
    {"name": "WIRE BREMERTON", "code": "WIRE_BREM_2", "book_number": 2,
     "job_class": "JRY WIRE", "region": "BREMERTON", "morning_referral_time": "08:30"},
    
    # Inside Wireman - Port Angeles
    {"name": "WIRE PT ANGELES", "code": "WIRE_PA_1", "book_number": 1,
     "job_class": "JRY WIRE", "region": "PT_ANGELES", "morning_referral_time": "08:30"},
    {"name": "WIRE PT ANGELES", "code": "WIRE_PA_2", "book_number": 2,
     "job_class": "JRY WIRE", "region": "PT_ANGELES", "morning_referral_time": "08:30"},
    
    # Sound & Communication - Seattle
    {"name": "SOUND SEATTLE", "code": "SOUND_SEA_1", "book_number": 1,
     "job_class": "SOUND", "region": "SEATTLE", "morning_referral_time": "09:30"},
    {"name": "SOUND SEATTLE", "code": "SOUND_SEA_2", "book_number": 2,
     "job_class": "SOUND", "region": "SEATTLE", "morning_referral_time": "09:30"},
    
    # Tradeshow
    {"name": "TRADESHOW SEATTLE", "code": "TRADE_SEA_1", "book_number": 1,
     "job_class": "TRADESHOW", "region": "SEATTLE", "morning_referral_time": "09:00"},
    
    # Residential
    {"name": "RESIDENTIAL SEATTLE", "code": "RES_SEA_1", "book_number": 1,
     "job_class": "RESIDENTIAL", "region": "SEATTLE", "morning_referral_time": "09:30"},
    
    # Seattle School District (special)
    {"name": "SEATTLE SCHOOL DISTRICT", "code": "SSD_SEA_1", "book_number": 1,
     "job_class": "JRY WIRE", "region": "SEATTLE", "morning_referral_time": "09:30"},
]
```

---

## 📝 End-of-Session Documentation (MANDATORY)

**CRITICAL:** Before completing each implementation session, you MUST:

> **Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs—update as necessary.**

### Documentation Checklist
- [ ] `/CHANGELOG.md` — Version bump, changes summary
- [ ] `/CLAUDE.md` — Update with Phase 7 progress
- [ ] `/docs/IP2A_MILESTONE_CHECKLIST.md` — Progress updates
- [ ] `/docs/decisions/ADR-015-referral-dispatch-system.md` — Architecture decision
- [ ] `/docs/reports/session-logs/YYYY-MM-DD-*.md` — Create session log

See `/docs/standards/END_OF_SESSION_DOCUMENTATION.md` for full checklist.

---

Document Version: 2.1
Last Updated: February 3, 2026
Previous Version: 2.0 (February 2, 2026 — Initial v2 plan with Local 46 rules)

*Phase 7 Dispatch & Referral Plan v2.1*
*Based on IBEW Local 46 Referral Procedures (Effective October 4, 2024)*
