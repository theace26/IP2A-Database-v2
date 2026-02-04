# UNIONCORE — IP2A Database v2 — CONTINUITY DOCUMENT
## Master Reference (Consolidated) — Volumes 1 & 2
### Last Updated: February 2, 2026 | Version: v0.9.4-alpha | Schema Status: Corrections Pending

---

## PURPOSE OF THIS DOCUMENT

This is the **complete continuity document** for the UnionCore / IP2A-Database-v2 project. It is designed to be pasted into a new Claude conversation to provide full context. It consolidates the original Continuity Document (Volume 1, Feb 3, 2026) with the Batch 2 Data Extraction Analysis (Volume 2, Feb 2, 2026). All corrections from Volume 2 have been applied inline.

---

## TABLE OF CONTENTS
1. Project Overview
2. Architecture & Tech Stack
3. Current Development State
4. LaborPower Reconnaissance Summary
5. LaborPower Data Extraction — Complete Findings (Batches 1 & 2)
6. Referral Procedures — 14 Business Rules
7. Activity List — Job Request Data Model
8. Gap Analysis — UnionCore vs LaborPower
9. Proposed & Corrected Schema for Referral/Dispatch Module
10. Remaining Data Gaps (Updated)
11. Key Decisions & Principles
12. What Comes Next

---

## 1. PROJECT OVERVIEW

**UnionCore** is a comprehensive union management platform being built to replace three fragmented systems at IBEW Local 46 (International Brotherhood of Electrical Workers, Seattle, WA):

| System Being Replaced | Current State | UnionCore Approach |
|---|---|---|
| **LaborPower** (referral/dispatch) | Vendor software, limited export capability | Full replacement with modern referral module |
| **Access Database** (member records) | Single protective owner, ~20 years of data | Migration after demo proves value (Phase 5) |
| **QuickBooks** (accounting/dues) | Works well for its purpose | Sync-don't-replace — bidirectional integration |

- **Users:** ~40 internal staff (admins, officers, organizers, instructors) + ~4,000 external (members, stewards, applicants)
- **Repository:** github.com/theace26/IP2A-Database-v2
- **Developer:** Xerxes — IBEW Local 46 Business Representative, part-time volunteer (5–10 hrs/week)
- **Timeline:** 12–18 month realistic timeline
- **Dev Machine:** MacBook Pro M4 Pro (personal), Windows machine (development)

---

## 2. ARCHITECTURE & TECH STACK

**Backend (Production-Ready, v0.9.4-alpha):**
- PostgreSQL 16 with comprehensive audit trails (7-year NLRA compliance)
- FastAPI with service layer pattern (API → Business Logic → Data Access)
- SQLAlchemy ORM — 26 ORM models
- JWT authentication with bcrypt + role-based access control
- MinIO (dev) / B2/S3 (prod) for file storage with lifecycle management
- SendGrid for email services
- Stripe integration for payments
- ~470 passing tests, ~150 API endpoints
- 8 Architecture Decision Records (ADR-001 through ADR-008)
- Railway deployment + PWA capabilities

**Frontend (Not Started — Phase 6):**
- Jinja2 templates + HTMX + Alpine.js + Tailwind CSS + DaisyUI
- Server-rendered for maintainability (chosen over React/Vue per ADR)

**Infrastructure:**
- Docker containers for deployment
- Caddy reverse proxy with security headers
- Grafana + Loki + Promtail for observability
- Three deployment targets: dev, demo (laptop for stakeholder presentations), production (union server)

---

## 3. CURRENT DEVELOPMENT STATE

- **Backend:** Complete and production-ready. All core modules implemented: authentication, file storage, training management, union operations, dues tracking.
- **Development History:** 19 weeks of active development, grown from initial concept to ~470 tests and ~150 endpoints
- **Phase 5 (Access DB migration):** BLOCKED pending stakeholder approval. Requires demonstration-first approach.
- **Phase 6 (Frontend):** Ready to begin. Week 1 instruction document prepared (790 lines). BUT referral/dispatch schema must be finalized FIRST.
- **Phase 7 (LaborPower):** Schema analysis in progress. Planning documents updated. Feature parity analysis for referral/dispatch and financial tracking systems.
- **Referral/Dispatch Module:** Schema analysis in progress. 24 LaborPower data exports analyzed across 2 batches. Critical corrections identified. Awaiting 3 additional data exports to finalize.
- **Documentation:** Comprehensive update project completed through Batches 1-4a. All docs updated from v0.7.8–v0.9.0 to reflect v0.9.4-alpha. Established conventions: header blocks, implementation status tables, cross-references.

---

## 4. LABORPOWER RECONNAISSANCE SUMMARY

### 4.1 Screenshot Analysis (5 screenshots, prior session)
- **Report Preparation Interface:** Custom Reports module with named report configurations
- **Activity List (Web Bid Interface):** Shows job request fields visible to members during online bidding
- **Referral Procedures Document:** 14 business rules governing dispatch operations

Key custom reports identified: REGLIST (registration data), RAW DISPATCH DATA (dispatch transactions), EMPLOYCONTRACT (employer/contract relationships), ALL_FOREMANLJ_LIST (foreman tracking), plus various drop/check mark tracking reports.

### 4.2 Data Extraction Summary

| Batch | Date | Files | Contents |
|---|---|---|---|
| Batch 1 | Feb 2, 2026 | 12 | Wire SEA/BREM/PA reg lists + Technician + Utility Worker reg lists + 7 employer lists (WIREPERSON, S&C, STOCKPERSON, LFM, MARINE, TV&APPL, MARKET RECOVERY) |
| Batch 2 | Feb 2, 2026 | 12 | STOCKMAN + TRADESHOW + TERO APPR WIRE + Technician + Utility Worker reg lists + 7 employer lists (WIREPERSON, S&C, STOCKPERSON, LFM, MARINE, MARKET RECOVERY, **RESIDENTIAL**) |

---

## 5. LABORPOWER DATA EXTRACTION — COMPLETE FINDINGS

### 5.1 Registration Lists — 8 Books, 4,033 Total Records

| Book Name | Book 1 | Book 2 | Book 3 | Total | Tier Pattern |
|---|---|---|---|---|---|
| WIRE SEATTLE | 1,186 | (incl in total) | (incl) | 1,186* | Normal |
| WIRE BREMERTON | 1,115 | (incl) | (incl) | 1,115* | Normal |
| WIRE PT ANGELES | 1,100 | (incl) | (incl) | 1,100* | Normal |
| TRADESHOW | 298 | 16 | 1 | 315 | Normal (94.6% Book 1) |
| TECHNICIAN | 112 | 17 | 131 | 260 | **INVERTED** (B3 > B1) |
| STOCKMAN | 5 | 6 | 43 | 54 | **INVERTED** (B3 = 8.6× B1) |
| TERO APPR WIRE | 2 | — | — | 2 | Single tier |
| UTILITY WORKER | 1 | — | — | 1 | Single tier |

*Wire books show tier totals across all tiers (data from Batch 1, tier-level breakdown available).

**Column structure:** Book_priority_number (tier 1–4), Book_name, Applicant_priority_number (decimal)

### 5.2 Employer Lists — 9 Contract Codes, ~843 Unique Employers, ~1,544 Relationships

| Contract Code | Unique Employers | Duplicate Entries | Notes |
|---|---|---|---|
| WIREPERSON | 689 | 63 | Largest |
| SOUND & COMM | 300 | 45 | |
| **RESIDENTIAL** | **259** | **33** | **NEW — missing from all prior docs** |
| STOCKPERSON | 180 | 38 | Maps to STOCKMAN book |
| LT FXT MAINT | 92 | 17 | |
| GROUP MARINE | 21 | 0 | Clean |
| GROUP TV & APPL | 2 | 0 | Batch 1 only; not re-uploaded |
| MARKET RECOVERY | 1 | 0 | ELECTRIC HOME SERVICE only |

**Multi-contract distribution:**
- 1 contract: 449 employers
- 2 contracts: 201 employers
- 3 contracts: 109 employers
- 4 contracts: 47 employers
- 5 contracts: 34 employers
- 6 contracts: 1 employer (ELECTRIC HOME SERVICE — signed to WIREPERSON, S&C, STOCKPERSON, LFM, MARKET RECOVERY, RESIDENTIAL)

### 5.3 CRITICAL FINDING: APN Format

The Applicant Priority Number (APN) is a composite decimal encoding:
- **Integer part = Excel serial date** (days since Dec 30, 1899). Example: 40966 = February 27, 2012.
- **Decimal part = secondary sort key** (.23 to .91, ~46–53 unique values across batches). Likely encodes time-of-day or sequential position within same-day registrations. Most values cluster in .34–.65 range.
- **Function:** FIFO dispatch priority. Lowest APN = earliest registration = dispatched first.
- **SCHEMA REQUIREMENT:** Must use DECIMAL(10,2), NOT INTEGER. Integer would truncate the decimal and break dispatch ordering.

### 5.4 CRITICAL FINDING: Duplicate APNs

APNs are NOT unique identifiers within a book tier:
- Wire Seattle Book 1: 52 duplicate APNs (Batch 1)
- Wire Bremerton Book 1: 40 duplicates (Batch 1)
- Wire Pt. Angeles Book 1: 39 duplicates (Batch 1)
- Technician Book 1: 1 duplicate (Batch 2)
- Tradeshow Book 1: 4 duplicates (Batch 2)
- **Two different members can share the same APN** (registered same day, same decimal slot)
- **Cannot use APN as unique key.** Must use UNIQUE(member_id, book_id, book_priority_number)
- **DATA GAP:** Current exports don't include member identifiers — need REGLIST custom report to resolve which member each APN belongs to

### 5.5 CRITICAL FINDING: Cross-Regional Registration Patterns (Batch 1)

Wire Book 1 overlap across three regions:
- **932 members (87%) registered on ALL THREE regional books** (Seattle + Bremerton + Pt. Angeles)
- 117 members Seattle ONLY; 6 Bremerton ONLY; 10 Pt. Angeles ONLY
- **Implication:** registrations table will have ~3x rows vs unique members for Wire classification

### 5.6 CRITICAL FINDING: Cross-Classification Registrations

Combined findings from both batches:
- 88 members on BOTH Wire Seattle AND Technician books (34% of Technician) — Batch 1
- **95 shared APNs between Technician and Tradeshow (36.5% of Technician)** — Batch 2
- 1 member on BOTH Utility Worker AND Wire Seattle Book 1 — Batch 1
- **APN 45880.41 appears on FOUR books simultaneously** (Technician, TERO Appr Wire, Tradeshow, Utility Worker) — Batch 2
- Confirms: Rule 5 allows one registration per classification, multiple classifications simultaneously
- Validates many-to-many model via registrations table

### 5.7 Tier Distribution Analysis — "Book 3 = Travelers" Hypothesis

| Book | Book 1 | Book 3 | Pattern | Evidence |
|---|---|---|---|---|
| STOCKMAN | 5 | 43 | INVERTED 8.6× | Heavy traveler classification |
| TECHNICIAN | 112 | 131 | INVERTED 1.2× | Moderate travelers |
| TRADESHOW | 298 | 1 | NORMAL | Local-focused work |
| Wire books | Largest | Smaller | NORMAL | Local jurisdiction |

**Hypothesis:** Book 1 = Local journeymen (A-ticket), Book 2 = Organized/lower-priority, Book 3 = Travelers from other IBEW locals, Book 4 = Not yet observed.

### 5.8 Complete Book Catalog (All Known — 11 Total)

| Book Name | Classification | Region | Contract Code | Agreement | Work Level | Book Type | Source |
|---|---|---|---|---|---|---|---|
| WIRE SEATTLE | Wire | Seattle | WIREPERSON | Standard | Journeyman | Primary | Batch 1 reg list |
| WIRE BREMERTON | Wire | Bremerton | WIREPERSON | Standard | Journeyman | Primary | Batch 1 reg list |
| WIRE PT ANGELES | Wire | Pt. Angeles | WIREPERSON | Standard | Journeyman | Primary | Batch 1 reg list |
| TECHNICIAN | Technician | Jurisdiction-wide | *(unknown)* | Standard | Journeyman | Primary | Both batches |
| UTILITY WORKER | Utility Worker | Jurisdiction-wide | *(unknown)* | Standard | Journeyman | Primary | Both batches |
| STOCKMAN | Stockman | Jurisdiction-wide | STOCKPERSON | Standard | Journeyman | Primary | Batch 2 reg list |
| TRADESHOW | Tradeshow | Jurisdiction-wide | *(none — supplemental)* | Standard | Journeyman | Supplemental | Batch 2 reg list |
| TERO APPR WIRE | Wire | *(unknown)* | *(WIREPERSON?)* | **TERO** | **Apprentice** | Primary | Batch 2 reg list |
| *(implied)* SOUND & COMM | Sound & Comm | *(unknown)* | SOUND & COMM | Standard | Journeyman | Primary | Contract code only |
| *(implied)* LT FXT MAINT | Lt. Fixture Maint. | *(unknown)* | LT FXT MAINT | Standard | Journeyman | Primary | Contract code only |
| *(implied)* MARINE | Marine | *(unknown)* | GROUP MARINE | Standard | Journeyman | Primary | Contract code only |

**CRITICAL: Book Name ≠ Contract Code.** STOCKMAN book → STOCKPERSON contract. Schema must have separate fields for book_name, classification, and contract_code.

### 5.9 TERO APPR WIRE — Compound Book Type

TERO APPR WIRE encodes three pieces of information:
- **TERO** = Tribal Employment Rights Ordinance (Rule 4 agreement type)
- **APPR** = Apprentice (work level)
- **WIRE** = Wireperson (classification)

Only 2 registrations. Governed by Rule 4. May indicate other compound books exist (PLA WIRE, CWA WIRE, TERO APPR S&C, etc.).

### 5.10 RESIDENTIAL — 8th Contract Code

259 unique employers. 80% also signed WIREPERSON. 52 are residential-only shops. Completely missing from prior documentation. Questions: Does RESIDENTIAL have its own out-of-work book? Different wage rates? Different dispatch rules?

### 5.11 Duplicate Employer Records

196 total duplicate entries across all contract codes. ELECTRICAL CONSTRUCTION CO appears 4× under the same contract. Hypothesis: multiple contract periods, different effective dates, or data quality issues. Need EMPLOYCONTRACT custom report to resolve.

---

## 6. REFERRAL PROCEDURES — 14 BUSINESS RULES

Source: "IBEW Local 46 Referral Procedures" — Effective October 4, 2024, signed by Sean Bagsby, Business Manager / Financial Secretary.

### RULE 1 — Office Hours & Regions
- Kent Office: 8:00 AM – 5:00 PM; Bremerton Office: 8:00 AM – 3:00 PM; Monday–Friday, no holidays
- **System:** Regions are entities with operating parameters

### RULE 2 — Morning Referral Processing Order
- Inside Wireperson: 8:30 AM; Sound & Comm / Marine / Stockperson / LFM / Residential: 9:00 AM; Tradeshow & Seattle School District: 9:30 AM
- **System:** morning_sort_order field on referral_books table

### RULE 3 — Labor Request Cutoff
- Employer requests by 3:00 PM for next morning; Internet/Job Line available after 5:30 PM
- **System:** cutoff_timestamp and visibility_window on job_requests

### RULE 4 — Agreement Types
- PLA, CWA, TERO follow own referral terms
- **System:** agreement_type on job_requests AND referral_books acts as rule selector
- **VALIDATED by TERO APPR WIRE book discovery**

### RULE 5 — Registration Rules
- In person or email; one registration per classification per member; processed before Wire Book 1 referral
- **System:** UNIQUE(member_id, classification) constraint
- **VALIDATED** by cross-classification data AND APN 45880.41 on 4 books

### RULE 6 — Re-Registration Triggers
- Required after: Short Call termination, Under Scale termination, 90 Day Rule, Turnarounds
- Must process by end of next working day or dropped from ALL books
- **System:** re-registration countdown window with automatic drop logic

### RULE 7 — Re-Sign (30-Day Cycle)
- Must re-sign every 30 days from registration or last re-sign; in person, fax, or email
- **System:** last_re_sign_date + re_sign_due_date on registrations; automated alert/drop
- **Note:** TRADESHOW Book 1 has a member registered since Jan 28, 2009 — re-signing every 30 days for ~17 years

### RULE 8 — Internet/Email Bidding Rules
- Available 5:30 PM – 7:00 AM Pacific; check in by 3:00 PM day of dispatch; reject after bid = counted as quit; 2nd rejection in 12 months = lose bidding privileges for 1 year
- **System:** bidding_infractions table with privilege_revoked_until field

### RULE 9 — Short Calls
- ≤10 business days; max 2 per registration cycle; calls ≤3 working days NOT counted toward limit; laid off during short call = registration restored; Friday end = work weekend, report Monday
- **System:** short_call_count, duration classification logic, conditional restoration

### RULE 10 — Check Marks (Penalty System)
- 2 allowed; 3rd = rolled off that book; separate per area book (Seattle, Bremerton, Pt. Angeles); max 1 per book per day
- **System:** check_marks table per member per book; independent counters
- **VALIDATED** by cross-regional registration data

### RULE 11 — No Check Mark Exceptions
- Specialty skills not in CBA, MOU jobsites, start times before 6 AM, under scale, short calls, employer rejections, various location requests
- **System:** generates_checkmark boolean pre-calculated on job_requests; exclusion rule evaluation

### RULE 12 — Quit or Discharge
- Rolled off ALL books; cannot fill Foreperson-by-Name for SAME employer for 2 weeks
- **System:** blackout_periods table with per member-employer tracking

### RULE 13 — Foreperson By Name (Anti-Collusion)
- Cannot be filled by registrants who communicated with employer to generate request
- **System:** audit/flagging capability, self-attestation workflow

### RULE 14 — Exempt Status
- Military, union business, salting, medical, jury duty = exempt from check marks + re-sign; traveling/under scale = up to 6 months unless BM extends
- **System:** member_exemptions table with reason, dates, approval authority

---

## 7. ACTIVITY LIST — JOB REQUEST DATA MODEL

Confirmed fields from LaborPower web bid interface:

| Field | Example | Schema Mapping |
|---|---|---|
| Job Class | JRY WIRE | classification on job_requests |
| Book | Wire Seattle | book_id FK |
| Wage | $54.46/hr | wage_rate DECIMAL |
| Employer | ELECTRICAL SYSTEMS SOLUTIONS, INC. | employer_id FK |
| City | SEATTLE, WA | job location |
| Region | SEATTLE | region on job_requests |
| Request Date | 08/28/2019 | request_date |
| Start Date | 8/29/2019 | start_date |
| Start Time | 07:00 AM | start_time |
| Worksite | SHOP, 5216 45TH AVE SW | worksite_id FK |
| Report To | (may differ from worksite) | report_to fields |
| Positions | 1, 2 | positions_requested |
| Short Call | Yes/No | is_short_call |
| Checkmark | Yes/No | generates_checkmark |
| Requirements | "OSHA 30, Drug Test, No Tobacco..." | job_request_requirements junction |
| Comments | free text | comments TEXT |
| Bid | Bid/No Bid | web_bids table |

---

## 8. GAP ANALYSIS — UNIONCORE VS LABORPOWER

### Already Covered in UnionCore
Members, Organizations/Employers, Demographics, Audit trails, File storage, Status tracking

### Partially Covered — Needs Verification
Skills (need proper many-to-many), Job Classifications (member classification vs "Working As"), Employment History

### NOT Yet Modeled — 10 Major Gaps
1. Out-of-Work Book / Registration System (CORE MODULE)
2. Dispatch/Referral Transactions
3. Job Requests (employer-initiated with full lifecycle)
4. Worksites (physical locations, distinct from employers)
5. Travelers (members from other IBEW locals)
6. Web Bids / Job Bids (online bidding system)
7. COPE/PAC Checkoff (political action fund tracking)
8. Steward Assignments
9. Working Time Limits (90-day rule, short call duration)
10. Foreman Designation

---

## 9. PROPOSED & CORRECTED SCHEMA FOR REFERRAL/DISPATCH MODULE

*Incorporates all corrections from Volume 1 and Volume 2.*

### 9.1 registrations
```
registration_id         SERIAL PRIMARY KEY
member_id               INTEGER NOT NULL FK → members
book_id                 INTEGER NOT NULL FK → referral_books
book_priority_number    INTEGER NOT NULL CHECK (1–4)
applicant_priority_number  DECIMAL(10,2) NOT NULL     -- NOT INTEGER
registration_date       DATE NOT NULL                  -- Derived from FLOOR(APN)
status                  VARCHAR(20) DEFAULT 'ACTIVE'   -- ACTIVE/DROPPED/REFERRED/EXEMPT
last_re_sign_date       DATE
re_sign_due_date        DATE                           -- last_re_sign + 30 days
check_mark_count        INTEGER DEFAULT 0 CHECK (0–3)
short_call_count        INTEGER DEFAULT 0 CHECK (0–2)
drop_reason             VARCHAR(50)
dropped_date            DATE
UNIQUE(member_id, book_id, book_priority_number)
INDEX (book_id, book_priority_number, applicant_priority_number) WHERE status = 'ACTIVE'
```

### 9.2 referral_books (CORRECTED — Vol. 2)
```
book_id                 SERIAL PRIMARY KEY
book_name               VARCHAR(100) NOT NULL UNIQUE  -- Exact LaborPower name
classification          VARCHAR(50) NOT NULL           -- Logical grouping
contract_code           VARCHAR(50)                    -- NULLABLE: FK to contract types (NULL for Tradeshow/TERO)
region                  VARCHAR(50)                    -- NULL for non-regional
agreement_type          VARCHAR(20) DEFAULT 'STANDARD' -- STANDARD/PLA/CWA/TERO (NEW in Vol. 2)
work_level              VARCHAR(20) DEFAULT 'JOURNEYMAN' -- JOURNEYMAN/APPRENTICE (NEW in Vol. 2)
book_type               VARCHAR(20) DEFAULT 'PRIMARY'  -- PRIMARY/SUPPLEMENTAL (NEW in Vol. 2)
max_tiers               INTEGER DEFAULT 4
morning_sort_order      INTEGER                        -- Per Rule 2
is_active               BOOLEAN DEFAULT TRUE
web_bidding_enabled     BOOLEAN DEFAULT TRUE
```

### 9.3 employer_contracts
```
employer_contract_id    SERIAL PRIMARY KEY
organization_id         INTEGER NOT NULL FK → organizations
contract_code           VARCHAR(50) NOT NULL
-- Valid: WIREPERSON, SOUND & COMM, STOCKPERSON, LT FXT MAINT,
--        GROUP MARINE, GROUP TV & APPL, MARKET RECOVERY, RESIDENTIAL (8 codes)
effective_date          DATE
expiration_date         DATE
is_active               BOOLEAN DEFAULT TRUE
UNIQUE(organization_id, contract_code)
```

### 9.4 job_requests
```
request_id              SERIAL PRIMARY KEY
employer_id             FK → organizations
book_id                 FK → referral_books
worksite_id             FK → worksites
request_date, start_date, start_time
positions_requested, positions_filled
wage_rate               DECIMAL
is_short_call           BOOLEAN
short_call_days         INTEGER
generates_checkmark     BOOLEAN  -- Pre-calculated from Rule 11
agreement_type          VARCHAR  -- STANDARD/PLA/CWA/TERO
region, comments TEXT
status                  VARCHAR  -- OPEN/PARTIALLY_FILLED/FILLED/CANCELLED/EXPIRED
report_to_address       TEXT
cutoff_applied          BOOLEAN
created_by              FK → users
```

### 9.5 job_requirements (lookup + junction)
```
requirement_id          SERIAL PRIMARY KEY
name                    VARCHAR  -- "OSHA 30", "Drug Test", etc.
category                VARCHAR  -- CERTIFICATION/DOCUMENT/COMPLIANCE/RESTRICTION
Junction: job_request_requirements (request_id, requirement_id)
```

### 9.6 dispatches
```
dispatch_id             SERIAL PRIMARY KEY
registration_id         FK → registrations
job_request_id          FK → job_requests
member_id               FK → members
employer_id             FK → organizations
dispatch_date, dispatch_time
dispatch_type           VARCHAR  -- MORNING/EMERGENCY/WEB_BID
status                  VARCHAR  -- OFFERED/ACCEPTED/REJECTED/WORKING/TERMINATED/QUIT/NO_SHOW
working_as              VARCHAR  -- May differ from member classification
termination_date, termination_reason
is_short_call, short_call_end_date
is_foreman              BOOLEAN
```

### 9.7 web_bids
```
bid_id, member_id FK, job_request_id FK
bid_timestamp, action (BID/NO_BID/RETRACT)
result (DISPATCHED/NOT_SELECTED/REJECTED_BY_MEMBER)
```

### 9.8 check_marks
```
checkmark_id, member_id FK, book_id FK, job_request_id FK
checkmark_date, is_exception BOOLEAN, exception_reason
```

### 9.9 member_exemptions
```
exemption_id, member_id FK
reason (MILITARY/UNION_BUSINESS/SALTING/MEDICAL/JURY_DUTY/TRAVELING/UNDER_SCALE)
start_date, end_date, approved_by FK, requires_bm_approval BOOLEAN
```

### 9.10 bidding_infractions
```
infraction_id, member_id FK
infraction_date, infraction_type, related_dispatch_id FK
privilege_revoked_until DATE
```

### 9.11 worksites
```
worksite_id, employer_id FK
name, address_line1, address_line2, city, state, zip
region, report_to_name, report_to_address
is_active
```

### 9.12 blackout_periods
```
blackout_id, member_id FK, employer_id FK
reason (QUIT/DISCHARGE), start_date, end_date
restriction_type (FOREPERSON_BY_NAME)
```

### Summary of ALL Schema Corrections (Volumes 1 & 2)

| Item | Original Proposal | Corrected |
|---|---|---|
| APN data type | INTEGER | DECIMAL(10,2) |
| APN field name | position_number | applicant_priority_number |
| Unique constraint | (member_id, book_id) | (member_id, book_id, book_priority_number) |
| Book tier field | Not explicit | book_priority_number INTEGER (1–4) |
| referral_books.contract_code | NOT NULL | **NULLABLE** (Tradeshow, TERO have no contract) |
| referral_books.agreement_type | Not proposed | **NEW: VARCHAR(20) DEFAULT 'STANDARD'** |
| referral_books.work_level | Not proposed | **NEW: VARCHAR(20) DEFAULT 'JOURNEYMAN'** |
| referral_books.book_type | Not proposed | **NEW: VARCHAR(20) DEFAULT 'PRIMARY'** |
| employer_contracts domain | 7 contract codes | **8 codes (+ RESIDENTIAL)** |

---

## 10. REMAINING DATA GAPS (UPDATED)

### Priority 1 — BLOCKING (Before Schema DDL)
1. **REGLIST custom report with member identifiers** — member_id/card_number, member_name, book_name, book_priority_number, APN. MOST CRITICAL. APN 45880.41 on 4 books makes this urgent.
2. **RAW DISPATCH DATA custom report** — dispatch transaction structure unknown
3. **EMPLOYCONTRACT custom report** — need contract dates to explain 196 duplicate employer entries

### Priority 2 — IMPORTANT (Before Migration Scripts)
4. Complete book catalog — 8 of ~11 books confirmed from reg lists; 3 implied
5. **Book-to-contract mapping** — TECHNICIAN/TRADESHOW/UTILITY WORKER contract codes unknown (NEW GAP)
6. Sample member registration detail — re-sign dates, check marks, exemptions
7. Sample dispatch history — full lifecycle with timestamps
8. **TERO/PLA/CWA book catalog** — how many compound books exist? (NEW GAP)
9. **Duplicate employer resolution** — are dupes = multiple contracts, locations, or data quality? (NEW GAP)

### Priority 3 — CLARIFICATION (Before Business Logic)
10. 90-day rule definition (trigger, consequence, calendar vs business days)
11. "Too many days" rule threshold
12. Total referral region count
13. Book tier semantics — Book 3 = Travelers hypothesis strengthened but unconfirmed
14. **TRADESHOW dispatch rules** — no employer contract, how are referrals compensated? (NEW GAP)
15. **Apprentice book rules** — TERO APPR pattern, are there standard apprentice books? (NEW GAP)
16. **RESIDENTIAL vs WIREPERSON** — different rates? different dispatch procedures? (NEW GAP)

---

## 11. KEY DECISIONS & PRINCIPLES

- **"Schema is Law"** — Data integrity and auditability over rapid feature development
- **Jinja2 + HTMX over React/Vue** — Complexity management for part-time developer
- **Sync-don't-replace for QuickBooks** — Accounting stays in purpose-built tool
- **Service layer pattern** — API → Business Logic → Data Access
- **Demo-first for stakeholders** — Prove value before requesting sensitive data access
- **CSV export from LaborPower** — Confirmed extraction path; no vendor cooperation needed
- **One-time migration** — Import historical data, then new system going forward
- **7-year NLRA compliance** for audit trails on all member information changes

---

## 12. WHAT COMES NEXT

### Immediate Priority
- Export 3 remaining Priority 1 data (REGLIST with member IDs, RAW DISPATCH DATA, EMPLOYCONTRACT)
- Resolve blocking data gaps
- Lock schema DDL with all Vol. 1 + Vol. 2 corrections

### After Schema Lock
- Build field-by-field migration mapping (LaborPower → UnionCore)
- Create CSV import tooling (employers first, then registrations, then dispatch history)
- Begin frontend referral screens

### Parallel Work (Can Proceed Now)
- Frontend Week 1 scaffolding (login, dashboard, staff list)
- Demo environment setup (unioncore.ibew46.local on MacBook Pro M4)
- Confirm with dispatch staff: tier semantics, TERO/PLA/CWA catalog, RESIDENTIAL rules

---

*Continuity Document consolidated: February 2, 2026*
*Volumes 1 & 2 merged — all corrections applied inline*
*This document supersedes the original Continuity Document (Feb 3, 2026)*
*Previous session transcripts available in project thread history*
