# LaborPower → IP2A-Database-v2 Gap Analysis

> **Document Created:** February 2, 2026
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Phase 7 Planning — Pre-Implementation Reference
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1-19)

---

## Executive Summary

After analyzing 14 screenshots of the LaborPower system currently used by IBEW Local 46, this document identifies **8 major feature gaps** and **14 new database tables** (plus 2 table modifications) needed to achieve feature parity. These gaps form the basis for Phase 7 implementation planning.

> **⚠️ Important:** The implementation roadmap at the end of this document is a high-level overview only. The authoritative implementation schedule lives in **`LABORPOWER_IMPLEMENTATION_PLAN.md`**, which breaks each phase into detailed sessions with file-level granularity. The report sprint schedule (Weeks 29-32+) is documented in **`PHASE7_CONTINUITY_DOC_ADDENDUM.md`**.

### What IP2A Already Has (v0.9.4-alpha Baseline)

Before reviewing gaps, note what's already built and operational:

| Existing Feature | Version Shipped | Relevant Weeks | Related ADR |
|---|---|---|---|
| Member management (CRUD, profiles, search) | v0.7.0+ | Weeks 1-9 | — |
| Dues tracking & payments | v0.7.9 | Week 10 | ADR-008, ADR-011 |
| Stripe integration (Checkout Sessions + webhooks) | v0.8.0-alpha1 | Week 11 | ADR-013 |
| Audit logging (NLRA 7-year, immutability trigger) | v0.8.0-alpha1 | Week 11 | ADR-012 |
| Organization/employer management | v0.8.2-alpha | Week 13 | — |
| Grant compliance reporting | v0.9.0-alpha | Week 14 | ADR-014 |
| Production hardening (Sentry, security headers, connection pooling) | v0.9.1-alpha | Week 16 | ADR-007 |
| Admin metrics & backup scripts | v0.9.2-alpha | Week 17 | — |
| Mobile PWA (offline, service worker) | v0.9.3-alpha | Week 18 | — |
| Analytics dashboard (Chart.js, report builder) | v0.9.4-alpha | Week 19 | — |

**Current totals:** 26 ORM models, ~150 API endpoints, ~470 tests, 14 ADRs, Railway (prod) + Render (backup).

### Priority Assessment

| Priority | Module | Complexity | Est. Hours |
|----------|--------|------------|------------|
| 🔴 HIGH | Out-of-Work List / Dispatch | High | 40-60 |
| 🔴 HIGH | Enhanced Member Financial | Medium | 20-30 |
| 🔴 HIGH | Transaction History Enhancement | Medium | 15-20 |
| 🟡 MEDIUM | Pension & Benefits | High | 30-40 |
| 🟡 MEDIUM | Skills & Qualifications | Medium | 15-20 |
| 🟡 MEDIUM | Earnings History Integration | Medium | 20-25 |
| 🟢 LOW | Current Charges System | Low | 10-15 |
| 🟢 LOW | Web User Activity Logging | Low | 8-12 |

**Total Estimated:** 158-222 hours (16-22 weeks at 10 hrs/week)

### Related Documents

| Document | Purpose |
|---|---|
| `LABORPOWER_IMPLEMENTATION_PLAN.md` | Detailed session-by-session build schedule (authoritative) |
| `PHASE7_REFERRAL_DISPATCH_PLAN.md` | Referral & dispatch system deep-dive |
| `PHASE7_IMPLEMENTATION_PLAN_v2.md` | Broader Phase 7 plan (models, services, API, frontend) |
| `PHASE7_CONTINUITY_DOC.md` | Session-to-session continuity for Phase 7 work |
| `PHASE7_CONTINUITY_DOC_ADDENDUM.md` | Report sprint schedule (Weeks 29-32+) |
| `LOCAL46_REFERRAL_BOOKS.md` | Referral book seed data and open questions |
| `LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` | Full inventory of ~78 LaborPower reports to replicate |

---

## Detailed Gap Analysis

### 1. OUT-OF-WORK LIST / DISPATCH SYSTEM (🔴 HIGH PRIORITY)

**What LaborPower Has:**
- Multiple "Books" (WIRE SEATTLE, WIRE BREMERTON, WIRE PT ANGELES)
- Registration queue with position numbers
- Sign-in/Sign-out tracking
- Dispatch workflow (member → employer job)
- Re-sign deadlines and grace periods
- Automatic deactivation rules ("WORKED MORE THAN 90 DAYS")
- Registration Activity audit trail

**Current IP2A Status:** ❌ NOT IMPLEMENTED

> **Note:** Confirmed referral books and seed data are documented in `LOCAL46_REFERRAL_BOOKS.md`. Open questions about Sound & Communication, VDV, Residential, and Apprentice books are tracked there.

**Proposed Tables:**

```sql
-- Work books/referral lists
CREATE TABLE referral_books (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,           -- "WIRE SEATTLE"
    code VARCHAR(20) NOT NULL UNIQUE,     -- "WIRE_SEA"
    description TEXT,
    region VARCHAR(50),
    skill_type VARCHAR(50),               -- "WIRE", "SOUND", etc.
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Member registration on books
CREATE TABLE book_registrations (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    book_id INTEGER REFERENCES referral_books(id),
    registration_number INTEGER,          -- Position in queue
    registration_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    days_on_book INTEGER DEFAULT 0,
    adjusted_work_days INTEGER DEFAULT 0,
    available_position INTEGER,
    hours_available DECIMAL(10,2),
    date_dropped TIMESTAMP,
    grace_period_ends TIMESTAMP,
    dropped_reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(member_id, book_id, registration_date)
);

-- Registration activity log
CREATE TABLE registration_activities (
    id SERIAL PRIMARY KEY,
    registration_id INTEGER REFERENCES book_registrations(id),
    member_id INTEGER REFERENCES members(id),
    activity_date TIMESTAMP NOT NULL,
    action VARCHAR(50) NOT NULL,          -- REGISTER, WEB-SIGN-IN, DEACTIVATED, EMPLOY. STATUS CHANGE
    details TEXT,                         -- "BOOK: WIRE SEATTLE [1]"
    comment TEXT,
    processor VARCHAR(100),               -- "SYSTEM", "MEMBER VIA WEB", staff name
    created_at TIMESTAMP DEFAULT NOW()
);

-- Dispatch records (job assignments)
CREATE TABLE dispatches (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    employer_id INTEGER REFERENCES organizations(id),
    book_id INTEGER REFERENCES referral_books(id),
    request_id INTEGER,                   -- Links to employer request
    dispatch_date DATE NOT NULL,
    dispatch_class VARCHAR(20),           -- "JRY WIRE", "1.0", "1.4"
    dispatch_skill VARCHAR(50),           -- "WIRE - JRY"
    dispatch_type VARCHAR(50),
    worksite VARCHAR(100),
    start_date DATE,
    start_rate DECIMAL(10,2),
    start_comment TEXT,
    term_date DATE,
    term_reason VARCHAR(100),             -- "RIF", "QUIT", etc.
    term_rate DECIMAL(10,2),
    term_comment TEXT,
    notice_date DATE,
    days_worked INTEGER,
    hours_worked DECIMAL(10,2),
    is_short_call BOOLEAN DEFAULT false,
    by_name BOOLEAN DEFAULT false,        -- Employer requested by name
    exception BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
```

> **Architecture note:** Registration activities integrate with the existing audit logging infrastructure (ADR-012, Week 11). The immutability trigger pattern should be extended to dispatch-critical records to maintain NLRA compliance.

**New Enums** (in `src/db/enums/dispatch_enums.py` per project convention):
```python
class RegistrationAction(str, Enum):
    REGISTER = "register"
    WEB_SIGN_IN = "web_sign_in"
    DEACTIVATED = "deactivated"
    EMPLOY_STATUS_CHANGE = "employ_status_change"
    MANUAL_EDIT = "manual_edit"

class TermReason(str, Enum):
    RIF = "rif"                    # Reduction in Force
    QUIT = "quit"
    FIRED = "fired"
    LAID_OFF = "laid_off"
    CONTRACT_END = "contract_end"
    OTHER = "other"

class DispatchType(str, Enum):
    NORMAL = "normal"
    SHORT_CALL = "short_call"
    BY_NAME = "by_name"
    EMERGENCY = "emergency"
```

---

### 2. ENHANCED MEMBER FINANCIAL TRACKING (🔴 HIGH PRIORITY)

**What LaborPower Has:**
- Basic Paid-Thru date
- Work Paid-Thru date
- Account Balance (current dues owed)
- Total Init. Fee Due / Init. Fee Paid
- 401K Deferral Level (A1-A4, etc.)
- Jury Paid-Thru, Sick Paid-Thru
- BF (Benevolence Fund) tracking
- Vacation Balance, Last Vac. Payout, Last Vac. Deposit
- Jury Duty Exempt flag
- Include Basic on DCO flag

**Current IP2A Status:** ⚠️ PARTIAL — `DuesPayment` model exists (Week 10, ADR-008) with Stripe integration (Week 11, ADR-013) and analytics (Week 19), but missing many LaborPower-specific financial fields.

**Proposed Table:**

```sql
-- Create member_financials (one-to-one with members)
CREATE TABLE member_financials (
    id SERIAL PRIMARY KEY,
    member_id INTEGER UNIQUE REFERENCES members(id),
    
    -- Paid-thru tracking
    basic_paid_thru DATE,                 -- Basic dues paid through
    work_paid_thru DATE,                  -- Working dues paid through
    jury_paid_thru INTEGER,               -- Year (e.g., 2025)
    sick_paid_thru INTEGER,               -- Year (e.g., 2025)
    
    -- Account balance
    account_balance DECIMAL(10,2) DEFAULT 0,
    
    -- Initiation fees
    total_init_fee_due DECIMAL(10,2),
    init_fee_paid DECIMAL(10,2) DEFAULT 0,
    
    -- 401K
    deferral_level_401k VARCHAR(10),      -- "A1", "A2", "A3", "A4"
    
    -- Vacation tracking
    vacation_balance DECIMAL(10,2) DEFAULT 0,
    last_vacation_payout DECIMAL(10,2),
    last_vacation_deposit DECIMAL(10,2),
    last_vacation_payout_date DATE,
    last_vacation_deposit_date DATE,
    
    -- Benevolence Fund
    bf_paid_year INTEGER,
    bf_amount_paid DECIMAL(10,2),
    
    -- Flags
    jury_duty_exempt BOOLEAN DEFAULT false,
    include_basic_on_dco BOOLEAN DEFAULT false,
    
    updated_at TIMESTAMP DEFAULT NOW()
);
```

> **Integration note:** This table complements the existing `DuesPayment` model and Stripe payment flow. The `account_balance` field should be computed/reconciled from `dues_payments` records. Week 19 analytics dashboard can be extended to visualize paid-thru trends.

---

### 3. TRANSACTION HISTORY ENHANCEMENT (🔴 HIGH PRIORITY)

**What LaborPower Has:**
- I.O. Code (International Office transaction codes)
- Amount Paid
- Receipt # and Check #
- Batch processing (batch ID, batch date)
- User ID who processed
- Act. Date (Activity Date)
- I.O. Period (e.g., "12/2025")
- Type (DCO = Dues Check-Off, Payment, etc.)
- Trans. # (Transaction number)
- Note field
- Act. Code (Activity Code)
- Basic # and Basic PTD
- Description

**Current IP2A Status:** ⚠️ PARTIAL — `DuesPayment` model exists but with a simpler schema. Stripe integration (ADR-013) handles online payments; DCO (employer deduction) workflow is not yet implemented.

**Proposed Enhancement:**

```sql
-- Enhance dues_payments with LaborPower fields
ALTER TABLE dues_payments ADD COLUMN IF NOT EXISTS
    io_code VARCHAR(20),                  -- International Office code
    receipt_number VARCHAR(50),
    check_number VARCHAR(50),
    batch_id VARCHAR(50),
    batch_date DATE,
    processed_by_id INTEGER REFERENCES users(id),
    io_period VARCHAR(20),                -- "12/2025"
    transaction_type VARCHAR(20),         -- "DCO", "PAYMENT", "ADJUSTMENT"
    transaction_number INTEGER,
    activity_code VARCHAR(20),
    basic_number VARCHAR(50),
    basic_ptd DATE,                        -- Basic Paid-Thru Date
    description TEXT;
```

**New Enum** (in `src/db/enums/` per project convention):
```python
class TransactionType(str, Enum):
    DCO = "dco"                       # Dues Check-Off (employer deduction)
    PAYMENT = "payment"               # Direct payment
    ADJUSTMENT = "adjustment"         # Manual adjustment
    REFUND = "refund"                 # Refund
    TRANSFER = "transfer"             # Transfer from another local
    WRITE_OFF = "write_off"           # Write-off
    ELECTION = "election"             # Election-related
    MEMBER_INFO_CHANGE = "member_info_change"
```

> **Migration note:** Existing `dues_payments` records created via Stripe (Week 11) will have NULL values for the new LaborPower-specific columns. This is expected — Stripe payments populate `stripe_payment_id` while LaborPower-style transactions populate `io_code`/`batch_id`/etc. Both paths coexist.

---

### 4. PENSION & BENEFITS MODULE (🟡 MEDIUM PRIORITY)

**What LaborPower Has:**
- Pension Status dropdown
- Notes (Old/New)
- Spouse name and DOB
- Reminder Date
- Sub-tabs: IO Pension, Withdrawal, NEBF
- Beneficiaries table (Relation, Name, Birthdate, Phone)

**Current IP2A Status:** ❌ NOT IMPLEMENTED

**Proposed Tables:**

```sql
-- Pension tracking
CREATE TABLE member_pension (
    id SERIAL PRIMARY KEY,
    member_id INTEGER UNIQUE REFERENCES members(id),
    pension_status VARCHAR(50),
    spouse_first_name VARCHAR(100),
    spouse_last_name VARCHAR(100),
    spouse_dob DATE,
    reminder_date DATE,
    notes TEXT,
    notes_type VARCHAR(10),               -- "old" or "new"
    
    -- IO Pension specific
    io_pension_enrolled BOOLEAN DEFAULT false,
    io_pension_start_date DATE,
    io_pension_status VARCHAR(50),
    
    -- NEBF (National Electrical Benefit Fund)
    nebf_enrolled BOOLEAN DEFAULT false,
    nebf_start_date DATE,
    nebf_status VARCHAR(50),
    
    -- Withdrawal info
    withdrawal_date DATE,
    withdrawal_reason TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Beneficiaries
CREATE TABLE beneficiaries (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    relation VARCHAR(50),                 -- "Spouse", "Child", "Parent", etc.
    first_name VARCHAR(100) NOT NULL,
    middle_initial CHAR(1),
    last_name VARCHAR(100) NOT NULL,
    birthdate DATE,
    home_phone VARCHAR(20),
    percentage DECIMAL(5,2),              -- Percentage of benefits
    is_primary BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**New Enums** (in `src/db/enums/pension_enums.py`):
```python
class BeneficiaryRelation(str, Enum):
    SPOUSE = "spouse"
    CHILD = "child"
    PARENT = "parent"
    SIBLING = "sibling"
    OTHER = "other"

class PensionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    VESTED = "vested"
    RETIRED = "retired"
    WITHDRAWN = "withdrawn"
```

---

### 5. SKILLS & QUALIFICATIONS (🟡 MEDIUM PRIORITY)

**What LaborPower Has:**
- Skills tab (certifications, licenses)
- Conditions tab (restrictions, limitations)
- Exclusions tab (employers/jobs excluded from)
- Qualified Books table (which out-of-work lists member can sign)

**Current IP2A Status:** ⚠️ PARTIAL — Training/certification tracking exists for the JATC training module (Weeks 5-6), but that covers *student* certifications, not *member* union skills and dispatch qualifications. These are separate concerns per the Member/Student separation pattern.

> **Reminder:** Member is SEPARATE from Student (linked via FK on Student). Training certifications track JATC educational progress. Member skills track union dispatch qualifications. Do not conflate them.

**Proposed Tables:**

```sql
-- Member skills/certifications (dispatch-related)
CREATE TABLE member_skills (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    skill_name VARCHAR(100) NOT NULL,
    skill_code VARCHAR(20),
    certification_number VARCHAR(50),
    issue_date DATE,
    expiration_date DATE,
    issuing_authority VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Member conditions (restrictions)
CREATE TABLE member_conditions (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    condition_type VARCHAR(50),           -- "medical", "discipline", "legal"
    condition_code VARCHAR(20),
    description TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Member exclusions
CREATE TABLE member_exclusions (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    exclusion_type VARCHAR(50),           -- "employer", "worksite", "job_type"
    excluded_entity_id INTEGER,           -- FK to employer or worksite
    excluded_entity_name VARCHAR(200),    -- Denormalized for display
    reason TEXT,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Member qualified books (which lists they can sign)
CREATE TABLE member_qualified_books (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    book_id INTEGER REFERENCES referral_books(id),
    book_number INTEGER DEFAULT 1,        -- Which book level (1, 2, etc.)
    qualification_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(member_id, book_id)
);
```

---

### 6. EARNINGS HISTORY (🟡 MEDIUM PRIORITY)

**What LaborPower Has:**
- Work Period (month end date)
- Hours worked
- Gross pay
- Monthly breakdown going back years

**Current IP2A Status:** ❌ NOT IMPLEMENTED — Employment tracking exists (via dispatch/employment records) but not granular earnings data from employer payroll reports.

**Proposed Table:**

```sql
-- Earnings history (populated from employer reports)
CREATE TABLE member_earnings (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    employer_id INTEGER REFERENCES organizations(id),
    work_period DATE NOT NULL,            -- Last day of period (e.g., 12/31/2025)
    hours_worked DECIMAL(10,2),
    gross_pay DECIMAL(12,2),
    dues_deducted DECIMAL(10,2),
    pension_contribution DECIMAL(10,2),
    health_contribution DECIMAL(10,2),
    source VARCHAR(50),                   -- "employer_report", "manual", "import"
    report_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(member_id, employer_id, work_period)
);
```

> **Integration note:** Earnings data feeds into the Week 19 analytics dashboard. Chart.js membership trends can be extended with earnings visualizations (hours worked by month, gross pay by employer, etc.).

---

### 7. CURRENT CHARGES SYSTEM (🟢 LOW PRIORITY)

**What LaborPower Has:**
- Outstanding charges list
- Charge type (H = Hourly?, W = Working?)
- Unit Cost
- Quantity
- Paid Thru date
- Amount

**Current IP2A Status:** ❌ NOT IMPLEMENTED

**Proposed Table:**

```sql
CREATE TABLE member_charges (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id),
    charge_date TIMESTAMP NOT NULL,
    charge_type VARCHAR(10) NOT NULL,     -- "H", "W", "INIT", etc.
    charge_code VARCHAR(20),
    description TEXT,
    unit_cost DECIMAL(10,2),
    quantity INTEGER DEFAULT 1,
    paid_thru DATE,
    amount DECIMAL(10,2) NOT NULL,
    is_paid BOOLEAN DEFAULT false,
    paid_date DATE,
    payment_id INTEGER REFERENCES dues_payments(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

> **Integration note:** Charges link to the existing `dues_payments` table via `payment_id` FK. Outstanding charges can flow through the Stripe payment pipeline (ADR-013) for online payment.

---

### 8. WEB USER ACTIVITY LOGGING (🟢 LOW PRIORITY)

**What LaborPower Has:**
- Activity log with timestamps
- Action types (/ajaxlogin, View Personal Info, New Session Login, /logout)
- Request/Session tracking
- Path info

**Current IP2A Status:** ⚠️ PARTIAL — `AuditLog` model exists (Week 11, ADR-012) for NLRA-compliant record changes. Sentry captures errors (Week 16, ADR-007). Structured logging captures request context (Week 16). However, a dedicated *member-facing web activity log* (login/logout/page views) is not implemented.

**Proposed Table:**

```sql
-- Web activity log (supplement to audit_logs)
CREATE TABLE web_activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    member_id INTEGER REFERENCES members(id),  -- If member self-service
    session_id VARCHAR(100),
    activity_date TIMESTAMP NOT NULL,
    action_type VARCHAR(50) NOT NULL,         -- "login", "logout", "view_personal_info"
    path_info VARCHAR(200),
    request_info TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_web_activity_user_date ON web_activity_logs(user_id, activity_date DESC);
```

> **Architecture note:** This supplements — does not replace — the existing audit log infrastructure. `AuditLog` tracks *data changes* (NLRA compliance, immutability trigger). `web_activity_logs` tracks *user sessions and navigation* (operational visibility). Different purposes, different retention requirements.

---

## Existing IP2A Features to Enhance

### Member Model Enhancements

Based on the screenshots, the current `Member` model needs these additional fields:

```python
# Add to Member model
class Member(Base):
    # ... existing fields ...
    
    # IBEW-specific fields (from screenshots)
    local_number = Column(String(10))           # "0046"
    membership_type = Column(String(5))         # "A" (A-card member)
    card_number = Column(String(20))            # "7464416"
    io_status_code = Column(String(20))         # "Active"
    
    # Dates
    initiation_date = Column(Date)              # "01/09/2013"
    application_date = Column(Date)             # "10/24/2012"
    seniority_date = Column(Date)
    exam_date = Column(Date)
    last_activity_date = Column(Date)
    
    # Work info
    job_class = Column(String(10))              # "1.1"
    job_class_date = Column(Date)
    electric_license_number = Column(String(50))
    work_location_id = Column(Integer, ForeignKey('organizations.id'))
    
    # Contact preferences
    preferred_phone_type = Column(String(20))   # "Cell", "Home", "Work"
    preferred_phone_number = Column(String(20))
    bad_address = Column(Boolean, default=False)
    
    # Political/Union
    political_party = Column(String(50))
    is_veteran = Column(Boolean, default=False)
    is_registered_voter = Column(Boolean, default=False)
    
    # Organized (for SALTing — see salting_score 1-5 scale in existing schema)
    was_organized = Column(Boolean, default=False)
    organized_date = Column(Date)
    
    # COPE (Committee on Political Education)
    cope_checkoff = Column(Boolean, default=False)
    ibew_auth_card = Column(Boolean, default=False)
    direct_hire = Column(Boolean, default=False)
    erts = Column(Boolean, default=False)       # Electronic Referral Tracking System
    
    # Inactive tracking
    is_inactive_record = Column(Boolean, default=False)
    iris_record_deactivated = Column(Boolean, default=False)  # IBEW Records system
```

> **⚠️ Reminder:** The `User` model uses `locked_until` (datetime), NOT `is_locked` (boolean), for account lockout. This was established in the auth architecture and confirmed across all ADRs in Batch 3. Any new authentication or user status logic must use the `locked_until` pattern.

### Employment History Enhancement

```python
# Add to MemberEmployment model
class MemberEmployment(Base):
    # ... existing fields ...
    
    # From LaborPower
    employer_code = Column(String(20))          # "IBEW46", "VECA", etc.
    worksite_code = Column(String(50))          # "MAIN OFFICE", "WSCC"
    
    # Dispatch info
    dispatch_class = Column(String(20))         # "JRY WIRE", "1.0"
    dispatch_skill = Column(String(50))         # "WIRE - JRY"
    dispatch_date = Column(Date)
    dispatch_type = Column(String(20))
    request_number = Column(Integer)
    is_short_call = Column(Boolean, default=False)
    is_by_name = Column(Boolean, default=False)
    
    # Rate tracking
    start_rate = Column(Numeric(10, 2))
    term_rate = Column(Numeric(10, 2))
    
    # Time tracking
    days_worked = Column(Integer)
    hours_worked = Column(Numeric(10, 2))
    
    # Termination details
    term_reason = Column(String(50))            # "RIF", etc.
    term_comment = Column(Text)
    notice_date = Column(Date)
    
    # Book tracking
    book_id = Column(Integer, ForeignKey('referral_books.id'))
```

---

## Implementation Roadmap (Overview)

> **⚠️ This is a summary only.** For the detailed, session-by-session implementation plan with file trees and test targets, see **`LABORPOWER_IMPLEMENTATION_PLAN.md`**. For the report sprint schedule, see **`PHASE7_CONTINUITY_DOC_ADDENDUM.md`**.

### Phase 1: Foundation (Weeks 20-22)
**Focus:** Core dispatch/referral system — `referral_books`, `book_registrations`, `registration_activities`, `dispatches` tables, enums, CRUD services, API endpoints, frontend, +40 tests.

### Phase 2: Financial Enhancement (Weeks 23-24)
**Focus:** `member_financials`, `member_charges`, `dues_payments` enhancement, financial dashboard UI, reports.

### Phase 3: Skills & Qualifications (Weeks 25-26)
**Focus:** `member_skills`, `member_conditions`, `member_exclusions`, `member_qualified_books`, skills management UI.

### Phase 4: Pension & Benefits (Weeks 27-28)
**Focus:** `member_pension`, `beneficiaries`, pension management and beneficiary UIs.

### Phase 5: Earnings & History (Weeks 29-30)
**Focus:** `member_earnings`, `web_activity_logs`, employer payroll import tools, earnings UI.

### Phase 6: Integration & Polish (Weeks 31-32)
**Focus:** Cross-module integration, enhanced reporting, LaborPower data migration tools.

### Report Sprints (Weeks 29-32+, per Addendum)
**Focus:** Replicating ~78 LaborPower reports — P0 critical (16), P1 high (33), P2/P3 (29).

---

## Data Migration Considerations

### Export from LaborPower
- LaborPower likely uses SQL Server or Oracle
- Need to identify export capabilities
- May need to work with vendor for data dictionary

### Import to IP2A
- Create migration scripts for each table
- Map LaborPower fields to IP2A schema
- Handle data type conversions
- Validate referential integrity

### Parallel Running
- Run both systems during transition
- Compare outputs for accuracy
- Train staff on new system

---

## Summary

| Category | New Tables | Modified Tables | New Enums |
|----------|------------|-----------------|-----------|
| Dispatch/Referral | 4 | 1 | 3 |
| Financial | 2 | 1 | 1 |
| Skills | 4 | 0 | 2 |
| Pension | 2 | 0 | 2 |
| Earnings | 2 | 0 | 0 |
| **Total** | **14** | **2** | **8** |

**Recommendation:** Start with Phase 1 (Dispatch/Referral) as it's the most critical differentiator from current IP2A functionality and directly impacts daily union hall operations.

---

## 📝 End-of-Session Documentation (MANDATORY)

**Before completing ANY session:**

> Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

See `/docs/standards/END_OF_SESSION_DOCUMENTATION.md` for full checklist.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (February 2, 2026 — Initial gap analysis from LaborPower screenshots)
