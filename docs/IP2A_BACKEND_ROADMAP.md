# UnionCore — Development Roadmap

> **Document Created:** January 27, 2026
> **Last Updated:** February 4, 2026
> **Version:** 5.0
> **Status:** Phase 7 IN PROGRESS (v0.9.8-alpha) — Weeks 20-27 Complete (Services + API + Frontend)
> **For:** Claude Code implementation sessions
> **Time Budget:** 5-10 hours/week (estimates include 50% buffer)
> **Development Model:** Hub/Spoke (see below)

---

## Sprint Weeks vs Calendar Weeks

> **Important:** "Week" numbers in this document (Week 20, Week 25, etc.) are **sprint numbers**, not calendar weeks. At 5-10 hours/week development pace, each sprint takes **1-2 calendar weeks** to complete. Do not assume sprint numbers map to specific dates. Effort estimates assume a 50% buffer for testing, debugging, and documentation.

---

## Hub/Spoke Project Structure

Development planning uses a Hub/Spoke model organized across Claude AI projects. This does NOT affect the codebase — it controls how conversations and instruction documents are organized.

| Project | Scope | Status |
|---------|-------|--------|
| **Hub** | Strategy, architecture, cross-cutting decisions, roadmap, documentation | Active |
| **Spoke 2: Operations** | Dispatch/Referral, Pre-Apprenticeship, SALTing, Benevolence | Active — Phase 7 |
| **Spoke 1: Core Platform** | Members, Dues, Employers, Member Portal | Create when needed |
| **Spoke 3: Infrastructure** | Dashboard/UI, Reports, Documents, Import/Export, Logging | Create when needed |

All Phases through Week 19 were built under the original monolithic model (pre-Hub/Spoke). Spoke tags appear starting at Week 20.

---

## Executive Summary

| Phase | Focus | Duration | Hours | Status | Spoke |
|-------|-------|----------|-------|--------|-------|
| Phase 0 | Documentation & Structure | Week 1 | 5-8 hrs | ✅ Complete | *(pre-Hub/Spoke)* |
| Phase 1 | Foundation (Auth + Files) | Weeks 2-10 | 55-70 hrs | ✅ Complete | *(pre-Hub/Spoke)* |
| Phase 2 | Union Ops + Training | Weeks 11-18 | 55-70 hrs | ✅ Complete | *(pre-Hub/Spoke)* |
| Phase 3 | Documents (S3/MinIO) | Weeks 19-22 | 20-30 hrs | ✅ Complete | *(pre-Hub/Spoke)* |
| Phase 4 | Dues Tracking | Weeks 23-27 | 35-45 hrs | ✅ Complete | *(pre-Hub/Spoke)* |
| Phase 5 | Access DB Migration | TBD | 45-70 hrs | ⬜ Blocked (Awaiting Approval) | Hub (strategy) |
| Phase 6 | Frontend Build (Weeks 1-19) | Weeks 28-44 | 85-115 hrs | ✅ Complete | *(pre-Hub/Spoke)* |
| **Phase 7** | **Referral & Dispatch** | **Weeks 20-28+** | **100-150 hrs** | **🚧 IN PROGRESS — Weeks 20-27 Complete** | **Spoke 2** |

**Current Version:** v0.9.8-alpha (Phase 7 Backend + Frontend Complete)
**Total Tests:** 593 (568 passing, 25 blocked by Dispatch.bid bug — see Known Issues)
**Total API Endpoints:** ~228 (~178 existing + ~50 Phase 7)
**Total ORM Models:** 32 (26 existing + 6 Phase 7)
**Total ADRs:** 16

**Phase 7 Progress (Weeks 20-27) — Spoke 2:**
- 6 models: ReferralBook, BookRegistration, RegistrationActivity, LaborRequest, JobBid, Dispatch
- 19 enums in phase7_enums.py
- 7 services: ReferralBookService, BookRegistrationService, LaborRequestService, JobBidService, DispatchService, QueueService, EnforcementService
- 5 backend routers: referral_books_api (10), registration_api (10), labor_request_api (9), job_bid_api (8), dispatch_api (14) — ~51 endpoints
- 2 frontend routers: referral_frontend.py (17), dispatch_frontend.py (11) — 28 routes
- 11 page templates, 15 HTMX partials
- 51 Phase 7 tests (22 referral + 29 dispatch)
- 14 of 14 business rules implemented
- ADR-015: Phase 7 Foundation, ADR-016: Phase 7 Frontend UI Patterns

**Note on Phase 5:** Intentionally blocked until the Access DB owner approves. Phases 1-4 serve as proof-of-concept. Phase 5 begins only after demo and approval.

---

## Technology Decisions (Confirmed)

| Component | Choice | ADR |
|-----------|--------|-----|
| Database | PostgreSQL 16 | ADR-001 |
| Backend Framework | FastAPI + SQLAlchemy 2.x | — |
| Frontend | Jinja2 + HTMX + Alpine.js + DaisyUI | ADR-002 |
| Authentication | JWT (access + refresh tokens) + HTTP-only cookies | ADR-003 |
| File Storage | MinIO (dev) / B2 or S3 (prod) | ADR-004 |
| CSS Framework | Tailwind CSS + DaisyUI (CDN) | ADR-005 |
| Background Jobs | Abstract TaskService (FastAPI now, Celery-ready) | ADR-006 |
| Email | SendGrid | — |
| Observability | Sentry + Structured JSON Logging | ADR-007 |
| Audit Logging | PostgreSQL-based, role-filtered, NLRA compliant | ADR-008 |
| Migration Safety | Timestamped, validated, FK-aware | ADR-009 |
| Dues Frontend | Service-based patterns with HTMX | ADR-011 |
| Stripe Payments | Checkout Sessions, webhook verification | ADR-013 |
| Grant Compliance | Enrollment tracking, outcome reporting | ADR-014 |
| Phase 7 Foundation | Schema, models, enums, services | ADR-015 |
| Phase 7 Frontend | Frontend service wrapper, time-aware logic, HTMX auto-refresh | ADR-016 |
| Deployment | Railway (prod) + Render (backup) | — |

### Audit Logging Strategy

**CRITICAL: All member information changes MUST be audited for NLRA compliance.**

Two-tier logging architecture:

1. **Business Audit Trail (PostgreSQL `audit_logs` table)**
   - Legal compliance, accountability, "who did what"
   - 7-year retention (NLRA requirement)
   - Immutable (database triggers prevent UPDATE/DELETE)
   - Role-based access with field-level redaction
   - Archived to S3 Glacier after 3 years

2. **Technical/System Logs (Sentry + JSON Logging)**
   - Operations, debugging, performance monitoring
   - 30-90 day retention
   - For sysadmin/developer use only

**Tables requiring mandatory audit:**
- `members` — All member data changes
- `member_notes` — Staff notes on members
- `member_employments` — Employment history
- `students` — Training program participants
- `users` — System user accounts
- `dues_payments` — Financial transactions
- `grievances` — Legal/labor relations
- `benevolence_applications` — Financial assistance
- `registrations` — *Phase 7: out-of-work book registrations (Spoke 2)*
- `dispatches` — *Phase 7: referral/dispatch transactions (Spoke 2)*
- `check_marks` — *Phase 7: penalty system records (Spoke 2)*

---

## Completed Phases Summary

### Backend (Phases 0-4): ALL COMPLETE ✅ — *(pre-Hub/Spoke)*

| Phase | Models | Endpoints | Tests |
|-------|--------|-----------|-------|
| Phase 1: Auth (JWT, RBAC, Registration) | 4 | 13 | 52 |
| Phase 2a: Union Ops (SALT, Benevolence, Grievance) | 5 | 27 | 31 |
| Phase 2b: Training (Students, Courses, Grades) | 7 | ~35 | 33 |
| Phase 3: Documents (S3/MinIO) | 1 | 8 | 11 |
| Phase 4: Dues (Rates, Periods, Payments, Adjustments) | 4 | ~35 | 21 |
| **Subtotal (Backend Phases 0-4)** | **21** | **~120** | **148** |

### Phase 7 Backend: COMPLETE ✅ — Spoke 2

| Sprint | Focus | Services | Routers | Endpoints | Tests |
|--------|-------|----------|---------|-----------|-------|
| Weeks 20-21 | Models, Enums, Schemas | — | — | — | 20+ |
| Week 22 | Foundation Services | 2 | — | — | *(included above)* |
| Weeks 23-24 | Additional Services | 5 | — | — | *(included above)* |
| Week 25 | API Routers | — | 5 | ~51 | *(included above)* |
| **Subtotal (Phase 7 Backend)** | | **7** | **5** | **~51** | **20+** |

### Phase 7 Frontend: Weeks 26-27 COMPLETE ✅ — Spoke 2

| Sprint | Focus | Routes | Pages | Partials | Tests | Version |
|--------|-------|--------|-------|----------|-------|---------|
| Week 26 | Books & Registration UI | 17 | 5 | 8 | 22 | v0.9.7-alpha |
| Week 27 | Dispatch Workflow UI | 11 | 6 | 7 | 29 | v0.9.8-alpha |
| **Subtotal (Phase 7 Frontend)** | | **28** | **11** | **15** | **51** | |

### Frontend (Phase 6, Weeks 1-14): ALL COMPLETE ✅ — *(pre-Hub/Spoke)*

| Week | Focus | Tests | Version |
|------|-------|-------|---------|
| 1 | Setup + Login | 12 | v0.7.0 |
| 2 | Auth cookies + Dashboard | 10 | v0.7.1 |
| 3 | Staff management | 18 | v0.7.2 |
| 4 | Training landing | 19 | v0.7.3 |
| 5 | Members landing | 15 | v0.7.4 |
| 6 | Union operations | 21 | v0.7.5 |
| 8 | Reports & Export | 30 | v0.7.6 |
| 9 | Documents Frontend | 6 | v0.7.7 |
| 10 | Dues UI (complete) | 37 | v0.7.9 |
| 11 | Audit Infrastructure + Stripe | 19+25 | v0.8.0-alpha1 |
| 12 | Profile & Settings | — | v0.8.1-alpha |
| 13 | Entity Completion Audit | — | v0.8.2-alpha |
| 14 | Grant Compliance Reporting | ~20 | v0.9.0-alpha |

### Post-Launch (Phase 6+, Weeks 16-19): ALL COMPLETE ✅ — *(pre-Hub/Spoke)*

| Week | Focus | Tests | Version |
|------|-------|-------|---------|
| 16 | Production Hardening & Security | 32 | v0.9.1-alpha |
| 17 | Post-Launch Operations & Maintenance | 13 | v0.9.2-alpha |
| 18 | Mobile Optimization & PWA | 14 | v0.9.3-alpha |
| 19 | Analytics Dashboard & Report Builder | 19 | v0.9.4-alpha |

---

## Phase 7: Referral & Dispatch System — Spoke 2

**Goal:** Implement the out-of-work referral and dispatch system for IBEW Local 46, replacing LaborPower with a modern, auditable system built on verified data structures.

**Documentation:** `docs/phase7/`
**Master Reference:** `UnionCore_Continuity_Document_Consolidated.md`
**Spoke Owner:** Spoke 2 (Operations)

### 7.1 LaborPower Data Analysis Status

Two batches of production data have been extracted and analyzed from LaborPower's Custom Reports module. This analysis drives all schema decisions.

| Batch | Date | Files | Contents |
|-------|------|-------|----------|
| Batch 1 | Feb 2, 2026 | 12 | Wire SEA/BREM/PA + Technician + Utility Worker reg lists; 7 employer lists (WIREPERSON, S&C, STOCKPERSON, LFM, MARINE, TV&APPL, MARKET RECOVERY) |
| Batch 2 | Feb 2, 2026 | 12 | STOCKMAN + TRADESHOW + TERO APPR WIRE + Technician + Utility Worker reg lists; 7 employer lists (including **RESIDENTIAL** — new discovery) |
| **Total** | | **24 files** | 4,033 registration records across 8 books; ~843 unique employers across 8 contract codes; ~1,544 employer-contract relationships |

**Analysis Documents:**
- `LaborPower_Data_Analysis_Schema_Guidance_1.docx` — Volume 1 (Batch 1 findings)
- `LaborPower_Data_Analysis_Schema_Guidance_2.docx` — Volume 2 (Batch 2 findings + schema corrections)
- `UnionCore_Continuity_Document_Consolidated.md` — Master reference merging both volumes

### 7.2 Critical Schema Findings (8 Discoveries)

These findings were extracted from analyzing 24 production data exports and directly impact the data model. All are incorporated into the corrected schema in §7.5.

| # | Finding | Impact | Severity |
|---|---------|--------|----------|
| 1 | **APN = DECIMAL(10,2), NOT INTEGER** — Integer part is Excel serial date, decimal is secondary sort key (.23–.91). INTEGER would destroy dispatch ordering. | Column data type | 🔴 Critical |
| 2 | **Duplicate APNs within books** — Two members can share same APN. Cannot use APN as unique key. Must use UNIQUE(member_id, book_id, book_priority_number). | Unique constraint design | 🔴 Critical |
| 3 | **RESIDENTIAL = 8th contract code** — 259 employers, 80% also WIREPERSON, 52 residential-only shops. Completely missing from all prior documentation. | Enum domain expansion | 🟡 High |
| 4 | **Book Name ≠ Contract Code** — STOCKMAN book → STOCKPERSON contract. TECHNICIAN/TRADESHOW/UTILITY WORKER have NO matching contract code. Schema must separate book_name, classification, and contract_code. | Table design | 🔴 Critical |
| 5 | **TERO APPR WIRE = Compound book type** — Encodes agreement_type (TERO) + work_level (APPRENTICE) + classification (WIRE). Schema needs agreement_type, work_level, book_type columns. | 3 new columns on referral_books | 🟡 High |
| 6 | **Cross-regional registration** — 87% of Wire Book 1 members registered on ALL THREE regional books. registrations table will have ~3× rows vs unique Wire members. | Capacity planning | 🟢 Medium |
| 7 | **Cross-classification APN 45880.41** — One member on FOUR books simultaneously (Technician, TERO Appr Wire, Tradeshow, Utility Worker). Validates many-to-many model. | Schema validation | 🟢 Medium |
| 8 | **Inverted tier distributions** — STOCKMAN Book 3 = 8.6× Book 1; TECHNICIAN Book 3 > Book 1. Strengthens "Book 3 = Travelers from other IBEW locals" hypothesis. | Business logic | 🟢 Medium |

### 7.3 Complete Book Catalog (11 Known)

| Book Name | Classification | Region | Contract Code | Agreement | Work Level | Book Type | Source |
|-----------|---------------|--------|---------------|-----------|------------|-----------|--------|
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

**Employer Contract Codes (8 confirmed):** WIREPERSON, SOUND & COMM, STOCKPERSON, LT FXT MAINT, GROUP MARINE, GROUP TV & APPL, MARKET RECOVERY, RESIDENTIAL

### 7.4 Business Rules Summary (14 Rules from Referral Procedures)

Source: "IBEW Local 46 Referral Procedures" — Effective October 4, 2024, signed by Business Manager / Financial Secretary.

| Rule | Name | System Impact |
|------|------|---------------|
| 1 | Office Hours & Regions | Regions as entities with operating parameters |
| 2 | Morning Referral Processing Order | `morning_sort_order` field on `referral_books`; Wire 8:30 AM → S&C/Marine/Stock/LFM/Residential 9:00 AM → Tradeshow 9:30 AM |
| 3 | Labor Request Cutoff | Employer requests by 3 PM for next morning; web bids after 5:30 PM |
| 4 | Agreement Types (PLA/CWA/TERO) | `agreement_type` on job_requests AND referral_books as rule selector. **Validated by TERO APPR WIRE book.** |
| 5 | Registration Rules | One per classification per member. **Validated by cross-classification data + APN 45880.41 on 4 books.** |
| 6 | Re-Registration Triggers | Required after short call termination, under scale, 90-day rule, turnarounds. Must process by end of next working day or dropped from ALL books. |
| 7 | Re-Sign (30-Day Cycle) | Must re-sign every 30 days. Automated alert/drop logic. |
| 8 | Internet/Email Bidding | 5:30 PM – 7:00 AM window; 2nd rejection in 12 months = lose privileges 1 year. `bidding_infractions` table. |
| 9 | Short Calls | ≤10 business days; max 2 per cycle; ≤3 days not counted toward limit. |
| 10 | Check Marks (Penalty) | 2 allowed, 3rd = rolled off that book. Separate per area book. `check_marks` table. **Validated by cross-regional data.** |
| 11 | No Check Mark Exceptions | Specialty skills, MOU sites, early starts, under scale, short calls, employer rejections. Pre-calculated `generates_checkmark` boolean. |
| 12 | Quit or Discharge | Rolled off ALL books; 2-week foreperson-by-name blackout for same employer. `blackout_periods` table. |
| 13 | Foreperson By Name | Anti-collusion: cannot be filled by registrants who communicated with employer. Audit/flagging. |
| 14 | Exempt Status | Military, union business, salting, medical, jury duty = exempt. `member_exemptions` table. |

### 7.5 Corrected Data Model (6 Implemented Tables)

All corrections from Volumes 1 & 2 applied.

| # | Table | Purpose | Key Design Notes |
|---|-------|---------|-----------------|
| 1 | `referral_books` | Book definitions (11+ books) | `book_name` UNIQUE, `contract_code` NULLABLE, + `agreement_type`, `work_level`, `book_type` |
| 2 | `book_registrations` | Member out-of-work book entries | APN as DECIMAL(10,2), UNIQUE(member_id, book_id, book_priority_number), status tracking |
| 3 | `registration_activities` | Activity log for registrations | Re-sign, status changes, check marks |
| 4 | `labor_requests` | Employer labor requests | Full lifecycle: OPEN→FILLED/CANCELLED/EXPIRED, pre-calculated `generates_checkmark` |
| 5 | `job_bids` | Member bids on labor requests | Time-gated bidding, rejection tracking |
| 6 | `dispatches` | Referral transactions | Links registration → labor_request → member → employer |

**Schema Corrections Summary (from Volumes 1 & 2):**

| Item | Original Proposal | Corrected |
|------|-------------------|-----------|
| APN data type | INTEGER | DECIMAL(10,2) |
| APN field name | position_number | applicant_priority_number |
| Unique constraint | (member_id, book_id) | (member_id, book_id, book_priority_number) |
| Book tier field | Not explicit | book_priority_number INTEGER (1–4) |
| referral_books.contract_code | NOT NULL | **NULLABLE** (Tradeshow, TERO have no contract) |
| referral_books.agreement_type | Not proposed | **NEW:** VARCHAR(20) DEFAULT 'STANDARD' |
| referral_books.work_level | Not proposed | **NEW:** VARCHAR(20) DEFAULT 'JOURNEYMAN' |
| referral_books.book_type | Not proposed | **NEW:** VARCHAR(20) DEFAULT 'PRIMARY' |
| employer_contracts domain | 7 contract codes | **8 codes (+ RESIDENTIAL)** |

### 7.6 Remaining Data Gaps (16 Items)

**Note:** Schema was implemented with available data. These gaps affect import tooling and edge case handling.

#### Priority 1 — BLOCKING (For Import Tooling)

| # | Gap | Status | Why Blocking |
|---|-----|--------|--------------|
| 1 | REGLIST custom report with member identifiers | 🔴 STILL BLOCKING | member_id/card_number needed to resolve APN-to-member mapping |
| 2 | RAW DISPATCH DATA custom report | 🔴 STILL BLOCKING | Dispatch transaction structure for historical import |
| 3 | EMPLOYCONTRACT custom report | 🔴 STILL BLOCKING | Contract dates to explain 196 duplicate employer entries |

#### Priority 2 — IMPORTANT (Before Migration Scripts)

| # | Gap | Status | Notes |
|---|-----|--------|-------|
| 4 | Complete book catalog | 🟡 PARTIALLY RESOLVED | 8 of ~11 books confirmed from reg lists |
| 5 | Book-to-contract mapping | 🔴 NEW GAP | STOCKMAN→STOCKPERSON confirmed; others unknown |
| 6 | Sample member registration detail | 🔴 STILL NEEDED | Re-sign dates, check marks, exemptions |
| 7 | Sample dispatch history | 🔴 STILL NEEDED | Full lifecycle with timestamps |
| 8 | TERO/PLA/CWA catalog | 🔴 NEW GAP | Which agreements exist? |
| 9 | Duplicate employer resolution | 🔴 NEW GAP | How LaborPower handles name variations |

#### Priority 3 — CLARIFICATION (During Implementation)

| # | Gap | Status | Notes |
|---|-----|--------|-------|
| 10 | 90-day rule specifics | 🔴 STILL NEEDED | |
| 11 | "Too many days" threshold | 🔴 STILL NEEDED | |
| 12 | Total region count | 🔴 STILL NEEDED | |
| 13 | Tier semantics | 🟡 PARTIALLY RESOLVED | Book 3 = Travelers hypothesis |
| 14 | TRADESHOW specific rules | 🔴 STILL NEEDED | |
| 15 | Apprentice books | 🔴 NEW GAP | |
| 16 | RESIDENTIAL vs WIREPERSON | 🔴 NEW GAP | |

### 7.7 Implementation Status

| Sub-Phase | Hours Est. | Status | Spoke |
|-----------|------------|--------|-------|
| **7a: Data Collection** | 3-5 | ⛔ BLOCKED (LaborPower access) | Spoke 2 |
| **7b: Schema Finalization** | 10-15 | ✅ COMPLETE (Weeks 20-21) | Spoke 2 |
| **7c: Core Services + API** | 25-35 | ✅ COMPLETE (Weeks 22-25) | Spoke 2 |
| **7d: Import Tooling** | 15-20 | ⬜ Ready to Start | Spoke 2 |
| **7e: Frontend UI** | 20-30 | 🚧 IN PROGRESS (Weeks 26-27 Done, Week 28 Remaining) | Spoke 2 |
| **7f: Reports P0+P1** | 20-30 | ⬜ Ready to Start | Spoke 2 or 3 |
| **7g: Reports P2+P3** | 10-15 | ⬜ Blocked by 7f | Spoke 2 or 3 |

### 7.8 LaborPower Report Inventory

~78 de-duplicated reports (~91 raw across report tabs) organized by priority:

| Priority | Count | Examples |
|----------|-------|---------|
| P0 (Critical) | 16 | Dispatch logs, Book Status, Referral Activity |
| P1 (High) | 33 | Employment Tracking, Contractor Workforce |
| P2 (Medium) | 22 | Analytics, Historical Trends |
| P3 (Low) | 7 | Advanced Analytics, Projections |

**Full inventory:** `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md`

### 7.9 Key Planning Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Phase 7 Plan | `docs/phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md` | Full implementation plan |
| Implementation Plan v2 | `docs/phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md` | Technical details and data models |
| Session Continuity Doc | `docs/phase7/PHASE7_CONTINUITY_DOC.md` | Session handoff document |
| Local 46 Referral Books | `docs/phase7/LOCAL46_REFERRAL_BOOKS.md` | Referral book structure and seed data |
| LaborPower Gap Analysis | `docs/phase7/LABORPOWER_GAP_ANALYSIS.md` | Gap analysis vs LaborPower |
| Reports Inventory | `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` | 78 reports to build (raw: 91) |
| **Consolidated Continuity Doc** | `UnionCore_Continuity_Document_Consolidated.md` | Master reference — Volumes 1 & 2 merged |
| ADR-015 | `docs/decisions/ADR-015-phase7-foundation.md` | Phase 7 schema and service architecture |
| ADR-016 | `docs/decisions/ADR-016-phase7-frontend-ui-patterns.md` | Phase 7 frontend patterns |

---

## Known Issues

### Dispatch.bid Relationship Bug (CRITICAL)

**Status:** 🔴 Blocks 25 tests
**Location:** `src/models/dispatch.py`
**Error:** `Could not determine join condition between parent/child tables on relationship Dispatch.bid`
**Fix:** Add `foreign_keys` parameter to the `Dispatch.bid` relationship:
```python
bid = relationship("JobBid", foreign_keys=[bid_id], back_populates="dispatch")
```
**Impact:** 25 dispatch frontend tests blocked in `test_dispatch_frontend.py`. Once fixed, test count goes from 568 passing to 593 passing.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Time availability drops | Medium | High | Realistic estimates, flexible scope |
| Technical blockers | Low | Medium | Architecture docs, fallback options |
| Scope creep | Medium | Medium | Strict phase boundaries, defer to backlog |
| Data migration issues | Medium | High | Parallel testing, rollback plan |
| Access DB approval delayed | Medium | Low | Phase 5 is independent; system works without it |
| Audit compliance gap | Low | High | Week 11 completed audit infrastructure |
| LaborPower data format changes | Medium | Medium | Adapter pattern, versioned imports |
| Priority 1 data gaps persist | Medium | High | Schema can be refined; blocks import tooling |
| Unknown compound books | Medium | Medium | Schema designed for extensibility |
| Book↔Contract mapping gaps | High | Medium | Dispatch staff consultation required |
| Duplicate employer data quality | Medium | Medium | Deduplicate programmatically during import |
| Hub/Spoke coordination overhead | Low | Low | Clear ownership, handoff notes |

---

## Backlog (Future Phases)

**Completed (Originally Backlogged):**
- [x] Dues tracking module — ✅ Phase 4
- [x] Grievance tracking — ✅ Phase 2
- [x] Benevolence fund — ✅ Phase 2
- [x] SALTing activities module — ✅ Phase 2
- [x] Grant compliance reporting — ✅ Week 14
- [x] Production hardening — ✅ Week 16
- [x] Mobile/PWA support — ✅ Week 18
- [x] Analytics dashboard — ✅ Week 19

**Phase 8+ Candidates:**
- [ ] Member self-service portal (web + mobile)
- [ ] Multi-local support (other IBEW locals)
- [ ] LaborPower data import (for unified reporting)
- [ ] Mobile app (native iOS/Android)
- [ ] Celery + Redis upgrade (when scheduling needed)
- [ ] Advanced audit analytics (ML anomaly detection)
- [ ] Audit log export automation (scheduled compliance reports)
- [ ] QuickBooks integration for accounting sync
- [ ] Recurring Stripe subscriptions for dues auto-pay
- [ ] COPE/PAC Checkoff tracking (political action fund)
- [ ] Steward Assignment management
- [ ] Foreman Designation tracking

**Deliberately NOT Building:**
- LaborPower replacement *(REVISED: now building replacement — referral/dispatch is Phase 7)*
- QuickBooks replacement (integrate, don't replace)

---

## Session Handoff Notes

### For Claude Code Sessions

When starting a session, check:
1. Current milestone in progress
2. Last completed task
3. Any blockers documented
4. Branch status (`git branch --show-current`)
5. Which Spoke the instruction document originated from

Typical session goal: Complete 1-2 tasks from current milestone.

### Audit-Specific Reminders

**BEFORE making changes to member-related code:**
1. Verify the table is in `AUDITED_TABLES` in `audit_service.py`
2. Ensure service layer calls appropriate `log_*` function
3. Test that changes appear in audit trail
4. Verify old/new values are captured correctly

**BEFORE deploying to production:**
1. Verify `audit_logs` immutability trigger exists
2. Test that UPDATE/DELETE on `audit_logs` fails
3. Verify role-based redaction works
4. Test audit export for compliance officer role

### Phase 7-Specific Reminders (Spoke 2)

**BEFORE writing any Phase 7 code:**
1. Verify schema DDL matches Continuity Document §9 (with all Vol. 1 + Vol. 2 corrections)
2. Check that `registrations`, `dispatches`, and `check_marks` are in `AUDITED_TABLES`

**CRITICAL architecture notes for Phase 7:**
- **Member vs Student distinction:** `members` table is for dispatch/referral. `students` table is for training. Do not conflate. A member may also be a student, but dispatch qualifications come from member records.
- **Book Name ≠ Contract Code:** Always use separate fields. STOCKMAN book dispatches under STOCKPERSON contract.
- **APN is DECIMAL(10,2):** Never truncate to integer. The decimal part is critical for same-day dispatch ordering.

---

## 🔄 End-of-Session Documentation (MANDATORY)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session.

### Before Ending This Session:

1. **Scan `/docs/*`** — Review all documentation files
2. **Update existing docs** — Reflect changes, progress, and decisions
3. **Create new docs** — If needed for new components or concepts
4. **ADR Review** — Update or create Architecture Decision Records as necessary
5. **Session log entry** — Record what was accomplished
6. **Cross-Spoke check** — If this session touched shared files (`main.py`, `conftest.py`, base templates), note in session summary for Hub handoff

This ensures historical record-keeping and project continuity ("bus factor" protection).
See `docs/standards/END_OF_SESSION_DOCUMENTATION.md` for full checklist.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-27 | Initial roadmap created |
| 1.1 | 2026-01-28 | Updated backlog — marked Phase 2 and Phase 4 items as complete |
| 1.2 | 2026-01-29 | Added Week 11 (Audit Trail & Member History UI), ADR-008, audit strategy |
| 2.0 | 2026-02-02 | Comprehensive update — v0.9.4-alpha FEATURE-COMPLETE. All Weeks 1-19 marked complete. Added Phase 7 Referral & Dispatch plan. Updated technology decisions, risk register, and backlog. |
| 3.0 | 2026-02-03 | Major Phase 7 expansion incorporating LaborPower data analysis (24 files, 2 batches). Added: 8 critical schema findings, complete 11-book catalog, 14 business rules summary, corrected 12-table data model with 9 schema corrections, 16-item data gap list with priorities, revised sub-phase implementation plan (7a–7g), documentation update project status, 4 new risk register items. Updated effort estimate from 80-120 to 100-150 hrs. Updated backlog with 3 new Phase 8 candidates. Corrected LaborPower stance from "use their system" to "building replacement." |
| 4.0 | 2026-02-04 | Hub/Spoke migration. Added: Hub/Spoke project structure section, Spoke ownership tags on all phases and sub-phases, sprint vs calendar week clarification. Updated: Phase 7 state to Weeks 20-25 complete (7 services, 5 routers, ~51 endpoints). Reconciled version numbers (v0.9.6-alpha). Added Hub/Spoke coordination risk. Added cross-Spoke end-of-session check. |
| **5.0** | **2026-02-04** | **Weeks 26-27 complete. Added: Phase 7 Frontend section (28 routes, 11 pages, 15 partials, 51 tests), ADR-016 to technology decisions, Known Issues section (Dispatch.bid bug blocking 25 tests). Updated: version to v0.9.8-alpha, test count to 593, ADR count to 16, implementation status table. Removed all ⚠️ VERIFY markers.** |

---

*Document created: January 27, 2026*
*Last updated: February 4, 2026*
*Previous version: 4.0 (February 4, 2026)*
*Hub/Spoke Model: Added February 2026*
