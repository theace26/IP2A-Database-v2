# IP2A Database - Development Roadmap

> **Document Created:** January 27, 2026
> **Last Updated:** February 4, 2026
> **Version:** 3.1
> **Status:** Phase 7 IN PROGRESS (v0.9.5-alpha) — Weeks 20-22 Complete
> **For:** Claude Code implementation sessions
> **Time Budget:** 5-10 hours/week (estimates include 50% buffer)

---

## Executive Summary

| Phase | Focus | Duration | Hours | Status |
|-------|-------|----------|-------|--------|
| Phase 0 | Documentation & Structure | Week 1 | 5-8 hrs | ✅ Complete |
| Phase 1 | Foundation (Auth + Files) | Weeks 2-10 | 55-70 hrs | ✅ Complete |
| Phase 2 | Union Ops + Training | Weeks 11-18 | 55-70 hrs | ✅ Complete |
| Phase 3 | Documents (S3/MinIO) | Weeks 19-22 | 20-30 hrs | ✅ Complete |
| Phase 4 | Dues Tracking | Weeks 23-27 | 35-45 hrs | ✅ Complete |
| Phase 5 | Access DB Migration | TBD | 45-70 hrs | ⬜ Blocked (Awaiting Approval) |
| Phase 6 | Frontend Build (Weeks 1-14) | Weeks 28-40 | 60-80 hrs | ✅ Complete |
| Phase 6+ | Post-Launch (Weeks 16-19) | Weeks 41-44 | 25-35 hrs | ✅ Complete |
| **Phase 7** | **Referral & Dispatch** | **Weeks 20-22+** | **100-150 hrs** | **🚧 IN PROGRESS — Weeks 20-22 Complete** |

**Current Version:** v0.9.5-alpha (Phase 7 Foundation Complete)
**Total Tests:** ~490+ (~200+ frontend, 185+ backend, ~78 production, 25 Stripe)
**Total API Endpoints:** ~150
**Total ORM Models:** 32 (26 existing + 6 Phase 7)
**Total ADRs:** 14

**Phase 7 Progress (Weeks 20-22):**
- 6 models: ReferralBook, BookRegistration, RegistrationActivity, LaborRequest, JobBid, Dispatch
- 19 enums in phase7_enums.py
- 2 services: ReferralBookService, BookRegistrationService
- 20+ model tests
- Schema decisions documented in PHASE7_SCHEMA_DECISIONS.md

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
- `registrations` — *Phase 7: out-of-work book registrations*
- `dispatches` — *Phase 7: referral/dispatch transactions*
- `check_marks` — *Phase 7: penalty system records*

---

## Completed Phases Summary

### Backend (Phases 0-4): ALL COMPLETE ✅

| Phase | Models | Endpoints | Tests |
|-------|--------|-----------|-------|
| Phase 1: Auth (JWT, RBAC, Registration) | 4 | 13 | 52 |
| Phase 2a: Union Ops (SALT, Benevolence, Grievance) | 5 | 27 | 31 |
| Phase 2b: Training (Students, Courses, Grades) | 7 | ~35 | 33 |
| Phase 3: Documents (S3/MinIO) | 1 | 8 | 11 |
| Phase 4: Dues (Rates, Periods, Payments, Adjustments) | 4 | ~35 | 21 |
| **Phase 7: Referral & Dispatch (foundation)** | **6** | **—** | **20+** |
| **Total (including Phase 7 foundation)** | **31** | **~120** | **185+** |

### Frontend (Phase 6, Weeks 1-14): ALL COMPLETE ✅

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

### Post-Launch (Phase 6+, Weeks 16-19): ALL COMPLETE ✅

| Week | Focus | Tests | Version |
|------|-------|-------|---------|
| 16 | Production Hardening & Security | 32 | v0.9.1-alpha |
| 17 | Post-Launch Operations & Maintenance | 13 | v0.9.2-alpha |
| 18 | Mobile Optimization & PWA | 14 | v0.9.3-alpha |
| 19 | Analytics Dashboard & Report Builder | 19 | v0.9.4-alpha |

---

## Phase 7: Referral & Dispatch System (NEXT)

**Goal:** Implement the out-of-work referral and dispatch system for IBEW Local 46, replacing LaborPower with a modern, auditable system built on verified data structures.

**Documentation:** `docs/phase7/`
**Master Reference:** `UnionCore_Continuity_Document_Consolidated.md`

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

### 7.5 Corrected Data Model (12 New Tables)

All corrections from Volumes 1 & 2 applied. Full DDL in Continuity Document §9.

| # | Table | Purpose | Key Design Notes |
|---|-------|---------|-----------------|
| 1 | `referral_books` | Book definitions (11+ books) | `book_name` UNIQUE, `contract_code` NULLABLE, + `agreement_type`, `work_level`, `book_type` (Vol. 2 additions) |
| 2 | `registrations` | Member out-of-work book entries | APN as DECIMAL(10,2), UNIQUE(member_id, book_id, book_priority_number), status tracking, re-sign/check mark counters |
| 3 | `employer_contracts` | Employer-to-contract relationships | 8 contract codes including RESIDENTIAL, UNIQUE(organization_id, contract_code) |
| 4 | `job_requests` | Employer labor requests | Full lifecycle: OPEN→FILLED/CANCELLED/EXPIRED, pre-calculated `generates_checkmark`, agreement_type |
| 5 | `job_requirements` | Certification/compliance requirements | Junction table `job_request_requirements` for many-to-many |
| 6 | `dispatches` | Referral transactions | Links registration → job_request → member → employer; status lifecycle; short call tracking |
| 7 | `web_bids` | Online bidding records | BID/NO_BID/RETRACT actions; DISPATCHED/NOT_SELECTED/REJECTED results |
| 8 | `check_marks` | Penalty system records | Per member per book; exception tracking; Rule 10 enforcement |
| 9 | `member_exemptions` | Exempt status periods | 7 reason types; BM approval tracking; Rule 14 |
| 10 | `bidding_infractions` | Bidding privilege violations | Privilege revocation periods; Rule 8 enforcement |
| 11 | `worksites` | Physical job locations | Separate from employer entity; report-to address support |
| 12 | `blackout_periods` | Quit/discharge restrictions | Per member-employer; foreperson-by-name blocking; Rule 12 |

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

**⚠ Do NOT finalize schema DDL or begin migration code until Priority 1 gaps are resolved.**

#### Priority 1 — BLOCKING (Before Schema DDL)

| # | Gap | Status | Why Blocking |
|---|-----|--------|--------------|
| 1 | REGLIST custom report with member identifiers | 🔴 STILL BLOCKING | member_id/card_number needed to resolve APN-to-member mapping. APN 45880.41 on 4 books makes this urgent. |
| 2 | RAW DISPATCH DATA custom report | 🔴 STILL BLOCKING | Dispatch transaction structure unknown — need to validate dispatches table design |
| 3 | EMPLOYCONTRACT custom report | 🔴 STILL BLOCKING | Need contract dates to explain 196 duplicate employer entries |

#### Priority 2 — IMPORTANT (Before Migration Scripts)

| # | Gap | Status | Notes |
|---|-----|--------|-------|
| 4 | Complete book catalog | 🟡 PARTIALLY RESOLVED | 8 of ~11 books confirmed from reg lists; 3 implied from contract codes |
| 5 | Book-to-contract mapping | 🔴 NEW GAP | STOCKMAN→STOCKPERSON confirmed; TECHNICIAN/TRADESHOW/UTILITY WORKER mapping unknown |
| 6 | Sample member registration detail | 🔴 STILL NEEDED | Re-sign dates, check marks, exemptions |
| 7 | Sample dispatch history | 🔴 STILL NEEDED | Full lifecycle with timestamps |
| 8 | TERO/PLA/CWA book catalog | 🔴 NEW GAP | How many compound books exist? |
| 9 | Duplicate employer resolution | 🔴 NEW GAP | Are duplicates = multiple contracts, locations, or data quality? |

#### Priority 3 — CLARIFICATION (Before Business Logic)

| # | Gap | Status | Notes |
|---|-----|--------|-------|
| 10 | 90-day rule definition | 🔴 STILL NEEDED | Trigger, consequence, calendar vs business days |
| 11 | "Too many days" rule threshold | 🔴 STILL NEEDED | |
| 12 | Total referral region count | 🔴 STILL NEEDED | |
| 13 | Book tier semantics | 🟡 PARTIALLY RESOLVED | Book 3 = Travelers hypothesis strengthened by Stockman data |
| 14 | TRADESHOW dispatch rules | 🔴 NEW GAP | No employer contract — how are referrals compensated? |
| 15 | Apprentice book rules | 🔴 NEW GAP | TERO APPR pattern — are there standard apprentice books? |
| 16 | RESIDENTIAL vs WIREPERSON | 🔴 NEW GAP | Different wage rates? Different dispatch procedures? |

### 7.7 LaborPower Report Inventory

~78 de-duplicated reports (~91 raw across report tabs) organized by priority:

| Priority | Count | Examples |
|----------|-------|---------|
| P0 (Critical) | 16 | Dispatch logs, Book Status, Referral Activity |
| P1 (High) | 33 | Employment Tracking, Contractor Workforce |
| P2 (Medium) | 22 | Analytics, Historical Trends |
| P3 (Low) | 7 | Advanced Analytics, Projections |

**Full inventory:** `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md`

**Note on report counts:** Raw total across LaborPower tabs is 91 reports. After de-duplication (reports appearing in multiple tabs), the unique count is ~78. Both numbers are tracked in the inventory document.

### 7.8 Implementation Plan — Sub-Phases

| Sub-Phase | Tasks | Hours Est. | Blocked By |
|-----------|-------|------------|------------|
| **7a: Data Collection** | Export 3 remaining Priority 1 reports; resolve blocking gaps | 3-5 | LaborPower system access |
| **7b: Schema Finalization** | Lock DDL with all corrections; create Alembic migrations; seed referral_books + contract codes | 10-15 | Sub-phase 7a |
| **7c: Core Services + API** | Registration CRUD, dispatch logic, business rule engine (14 rules), check mark tracking, exemption management | 25-35 | Sub-phase 7b |
| **7d: Import Tooling** | CSV import pipeline: employers → registrations → dispatch history; field-by-field LaborPower→UnionCore mapping | 15-20 | Sub-phase 7b |
| **7e: Frontend UI** | Book management, dispatch board, registration screens, web bidding interface, member referral views | 20-30 | Sub-phase 7c |
| **7f: Reports (P0+P1)** | 49 critical/high priority reports using existing WeasyPrint + Chart.js infrastructure | 20-30 | Sub-phase 7c |
| **7g: Reports (P2+P3)** | 29 medium/low priority reports, advanced analytics, projections | 10-15 | Sub-phase 7f |
| **Total** | | **100-150 hrs** | |

**Integration with existing infrastructure:**
- WeasyPrint (PDF generation) — already used for report export
- Chart.js (dashboard) — already used in Week 19 analytics
- Audit logging — ALL dispatch/registration actions must flow through `audit_service`
- Stripe — potential future integration for employer dispatch fees
- PWA — dispatch notifications for members via service worker

### 7.9 Key Planning Documents

| Document | Purpose | Location |
|----------|---------|----------|
| Phase 7 Plan | Full implementation plan | `docs/phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md` |
| Implementation Plan v2 | Technical details and data models | `docs/phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md` |
| Session Continuity Doc | Session handoff document | `docs/phase7/PHASE7_CONTINUITY_DOC.md` |
| Local 46 Referral Books | Referral book structure and seed data | `docs/phase7/LOCAL46_REFERRAL_BOOKS.md` |
| LaborPower Gap Analysis | Gap analysis vs LaborPower | `docs/phase7/LABORPOWER_GAP_ANALYSIS.md` |
| Reports Inventory | 78+ reports to build (raw: 91) | `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` |
| **Consolidated Continuity Doc** | **Master reference — Volumes 1 & 2 merged** | `UnionCore_Continuity_Document_Consolidated.md` |
| Schema Guidance Vol. 1 | Batch 1 data analysis | `LaborPower_Data_Analysis_Schema_Guidance_1.docx` |
| Schema Guidance Vol. 2 | Batch 2 analysis + all corrections | `LaborPower_Data_Analysis_Schema_Guidance_2.docx` |

---

## Documentation Update Project Status

A comprehensive documentation update project has been systematically updating all project files from outdated versions (v0.7.8–v0.9.0) to reflect the current v0.9.4-alpha feature-complete status.

| Batch | Scope | Files | Status |
|-------|-------|-------|--------|
| Batch 1 | Core project files (CHANGELOG, README, CONTRIBUTING) | 3 | ✅ Complete |
| Batch 2 | Architecture docs (SYSTEM_OVERVIEW, AUTH, FILE_STORAGE, SCALABILITY) | 4 | ✅ Complete |
| Batch 3 | ADRs (README + ADR-001 through ADR-014) | 15 | ✅ Complete |
| Batch 4a | Phase 7 planning (GAP_ANALYSIS, IMPLEMENTATION_PLAN, REFERRAL_BOOKS, CONTINUITY_ADDENDUM) | 4 | ✅ Complete |
| Batch 4b | Phase 7 planning (REFERRAL_DISPATCH_PLAN, IMPL_PLAN_v2, REPORTS_INVENTORY, AUDIT_ARCHITECTURE) | 4 | ✅ Complete |
| Batch 5 | Standards, Guides, References, Runbooks, Instructions | TBD | ⬜ Pending |

**Established conventions:** Header blocks (Created, Updated, Version, Status), implementation status tables (✅/🔜/❌), cross-reference tables, mandatory end-of-session documentation instruction, version footers.

**Issues found and fixed:**
- ADR-012 internally mislabeled as "ADR-008" — corrected with prominent notice
- ADR-005 omitted DaisyUI — added as primary component library
- ADR-007 described Grafana/Loki but Sentry shipped — restructured to reflect reality
- Report inventory: raw count 91 vs de-duplicated 78 — both tracked
- Schema conflicts between planning documents — reconciled in Continuity Doc

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
| **Priority 1 data gaps persist** | **Medium** | **🔴 High** | **Cannot finalize schema without REGLIST, RAW DISPATCH, EMPLOYCONTRACT exports. Dispatch staff confirmation needed.** |
| **Unknown compound books** | **Medium** | **Medium** | **TERO APPR WIRE discovered; PLA/CWA books may exist. Schema designed for extensibility with agreement_type + work_level columns.** |
| **Book↔Contract mapping gaps** | **High** | **Medium** | **3 books have no known contract code. Dispatch staff consultation required before migration.** |
| **Duplicate employer data quality** | **Medium** | **Medium** | **196 duplicates across employer lists. Import strategy: ingest all, deduplicate programmatically with EMPLOYCONTRACT report.** |

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

### Phase 7-Specific Reminders

**BEFORE writing any Phase 7 code:**
1. Confirm all 3 Priority 1 data gaps have been resolved
2. Verify schema DDL matches Continuity Document §9 (with all Vol. 1 + Vol. 2 corrections)
3. Check that `registrations`, `dispatches`, and `check_marks` are in `AUDITED_TABLES`

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
| **3.0** | **2026-02-03** | **Major Phase 7 expansion incorporating LaborPower data analysis (24 files, 2 batches). Added: 8 critical schema findings, complete 11-book catalog, 14 business rules summary, corrected 12-table data model with 9 schema corrections, 16-item data gap list with priorities, revised sub-phase implementation plan (7a–7g), documentation update project status, 4 new risk register items. Updated effort estimate from 80-120 to 100-150 hrs. Updated backlog with 3 new Phase 8 candidates. Corrected LaborPower stance from "use their system" to "building replacement."** |

---

*Document created: January 27, 2026*
*Last updated: February 3, 2026*
*Previous version: 2.0 (February 2, 2026)*
