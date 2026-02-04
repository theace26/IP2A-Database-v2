# Phase 7 — Referral & Dispatch System — Continuity Document

> **Document Created:** February 3, 2026
> **Last Updated:** February 4, 2026
> **Version:** 3.0
> **Status:** Phase 7 IN PROGRESS — Weeks 20-25 Complete (Models, Enums, Schemas, 7 Services, 5 API Routers)
> **Project Version:** v0.9.6-alpha

---

## Purpose

This document provides session continuity context for Phase 7 implementation of the Referral & Dispatch system. Paste this into Claude Code sessions when beginning Phase 7 work.

---

## Implementation Progress (February 4, 2026)

### Weeks 20-22: COMPLETE

| Session | Focus | Status |
|---------|-------|--------|
| Week 20A | Schema Reconciliation & Enums | ✅ Complete |
| Week 20B | ReferralBook Model & Seeds | ✅ Complete |
| Week 20C | BookRegistration Model | ✅ Complete |
| Week 21A | LaborRequest & JobBid Models | ✅ Complete |
| Week 21B | Dispatch Model | ✅ Complete |
| Week 21C | RegistrationActivity Model | ✅ Complete |
| Week 22A | ReferralBookService | ✅ Complete |
| Week 22B | BookRegistrationService Core | ✅ Complete |
| Week 22C | Check Mark Logic & Roll-Off | ✅ Complete |

### Weeks 23-25: COMPLETE (February 4, 2026)

| Session | Focus | Status |
|---------|-------|--------|
| Week 23A | LaborRequestService | ✅ Complete |
| Week 23B | JobBidService | ✅ Complete |
| Week 23C | DispatchService | ✅ Complete |
| Week 24A | QueueService Core | ✅ Complete |
| Week 24B | EnforcementService | ✅ Complete |
| Week 24C | Analytics & Integration | ✅ Complete |
| Week 25A | Book & Registration API | ✅ Complete |
| Week 25B | LaborRequest & Bid API | ✅ Complete |
| Week 25C | Dispatch & Admin API | ✅ Complete |

### Implementation Artifacts Created

```
docs/phase7/PHASE7_SCHEMA_DECISIONS.md     # 5 pre-implementation decisions

src/db/enums/phase7_enums.py               # 19 Phase 7 enums

src/models/                                 # 6 Phase 7 models
├── referral_book.py
├── book_registration.py
├── registration_activity.py
├── labor_request.py
├── job_bid.py
└── dispatch.py

src/schemas/                                # 6 Phase 7 schema files
├── referral_book.py
├── book_registration.py
├── registration_activity.py
├── labor_request.py
├── job_bid.py
└── dispatch.py

src/services/                               # 7 Phase 7 services
├── referral_book_service.py                # Book CRUD, stats, settings
├── book_registration_service.py            # Registration, check marks, rolloff
├── labor_request_service.py                # Rules 2,3,4,11 - Request lifecycle
├── job_bid_service.py                      # Rule 8 - Bidding window, suspensions
├── dispatch_service.py                     # Rules 9,12,13 - Dispatch operations
├── queue_service.py                        # Queue snapshots, analytics
└── enforcement_service.py                  # Batch processing, re-sign enforcement

src/routers/                                # 5 Phase 7 API routers (~50 endpoints)
├── referral_books_api.py                   # Book management
├── registration_api.py                     # Registration workflow
├── labor_request_api.py                    # Request CRUD
├── job_bid_api.py                          # Bidding workflow
└── dispatch_api.py                         # Dispatch, queue, enforcement

src/seed/phase7_seed.py                     # 11 referral book seeds
src/tests/test_phase7_models.py             # 20+ model tests
```

### Key Design Decisions Made

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Separate JobBid model | Cleaner audit trail, rejection tracking for 1-year suspension |
| 2 | Per-book exempt status | On BookRegistration, not Member (more flexible) |
| 3 | Dual audit pattern | Both RegistrationActivity AND audit_logs (NLRA compliance) |
| 4 | APN as DECIMAL(10,2) | Preserves FIFO ordering from LaborPower |
| 5 | Field naming standardized | registration_number (APN), referral_start_time, etc. |

### Business Rules Implemented in Services (All 14 Complete)

| Rule | Description | Service |
|------|-------------|---------|
| 1 | Office Hours & Regions | ReferralBook model |
| 2 | Morning Referral Processing Order | LaborRequestService |
| 3 | Labor Request 3 PM Cutoff | LaborRequestService |
| 4 | Agreement Types (PLA/CWA/TERO) | LaborRequestService |
| 5 | One Registration Per Classification | BookRegistrationService |
| 6 | Re-Registration Triggers | BookRegistrationService |
| 7 | Re-Sign 30-Day Cycle | EnforcementService |
| 8 | Internet Bidding Window (5:30 PM - 7:00 AM) | JobBidService |
| 9 | Short Calls (≤10 days, restoration) | DispatchService |
| 10 | Check Marks (3 = rolloff) | EnforcementService |
| 11 | No Check Mark Exceptions | LaborRequestService |
| 12 | Quit/Discharge All-Books Rolloff | DispatchService |
| 13 | Foreperson By-Name Anti-Collusion | DispatchService |
| 14 | Exempt Status (7 reason types) | BookRegistrationService |

### Next Steps (Weeks 26+)

- Frontend UI (dispatch board, book management) — Week 26
- Dispatch workflow UI — Week 27
- Reports dashboard & navigation — Week 28
- Reports Sprint 1: P0 Critical (16 reports) — Weeks 29-30
- Reports Sprint 2: P1 High Priority (33 reports) — Weeks 30-31
- Reports Sprint 3: P2/P3 (29 reports) — Week 32+

---

## Quick Reference — Phase 7 Scope

| Metric | Value |
|--------|-------|
| New Tables | 12 |
| Business Rules | 14 (from IBEW Local 46 Referral Procedures) |
| Reports to Build | 78 de-duplicated (91 raw) |
| Known Books | 11 (8 with data exports, 3 implied) |
| Unique Employers | ~843 across 8 contract codes |
| Implementation Hours | 100-150 estimated |
| Sub-Phases | 7a through 7g |

---

## Current Project State (v0.9.4-alpha Baseline)

### What's Already Built

| Feature | Version | Tests |
|---------|---------|-------|
| Member management (CRUD, profiles, search) | v0.7.0+ | ~125 |
| Dues tracking & payments | v0.7.9 | 37 |
| Stripe integration (Checkout Sessions + webhooks) | v0.8.0-alpha1 | 25 |
| Audit logging (NLRA 7-year, immutability trigger) | v0.8.0-alpha1 | 19 |
| Grant compliance reporting | v0.9.0-alpha | ~20 |
| Production hardening (Sentry, security headers) | v0.9.1-alpha | 32 |
| Admin metrics & backup scripts | v0.9.2-alpha | 13 |
| Mobile PWA (offline, service worker) | v0.9.3-alpha | 14 |
| Analytics dashboard (Chart.js, report builder) | v0.9.4-alpha | 19 |
| **Phase 7 foundation (models, enums, services)** | **v0.9.5-alpha** | **20+** |
| **Total** | **v0.9.5-alpha** | **~490+** |

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy ORM (32 models: 26 existing + 6 Phase 7) |
| Frontend | Jinja2 + HTMX + Alpine.js |
| UI Framework | DaisyUI (on Tailwind CSS) |
| Database | PostgreSQL 16 (Railway) |
| Payments | Stripe (Checkout Sessions + webhooks) |
| Auth | JWT + bcrypt + HTTP-only cookies |
| Monitoring | Sentry (see ADR-007) |
| Logging | Structured JSON logging |
| Reports | WeasyPrint (PDF), openpyxl (Excel), Chart.js |
| Mobile | PWA (service worker, offline support) |
| Testing | pytest + httpx |

---

## LaborPower Data Analysis Summary

### Registration Lists — 8 Books, 4,033 Total Records

| Book Name | Total | Tier Pattern |
|-----------|-------|-------------|
| WIRE SEATTLE | 1,186 | Normal |
| WIRE BREMERTON | 1,115 | Normal |
| WIRE PT ANGELES | 1,100 | Normal |
| TRADESHOW | 315 | Normal (94.6% Book 1) |
| TECHNICIAN | 260 | **INVERTED** (B3 > B1) |
| STOCKMAN | 54 | **INVERTED** (B3 = 8.6× B1) |
| TERO APPR WIRE | 2 | Single tier |
| UTILITY WORKER | 1 | Single tier |

### Employer Lists — 8 Contract Codes, ~843 Unique Employers

| Contract Code | Unique Employers | Notes |
|---------------|-----------------|-------|
| WIREPERSON | 689 | Largest |
| SOUND & COMM | 300 | |
| **RESIDENTIAL** | **259** | **8th contract - missing from prior docs** |
| STOCKPERSON | 180 | Maps to STOCKMAN book |
| LT FXT MAINT | 92 | |
| GROUP MARINE | 21 | |
| GROUP TV & APPL | 2 | |
| MARKET RECOVERY | 1 | |

### 8 Critical Schema Findings

1. **APN = DECIMAL(10,2)** not INTEGER — integer truncation would break dispatch ordering
2. **Duplicate APNs** — need composite unique key (member_id, book_id, book_priority_number)
3. **RESIDENTIAL = 8th contract code** (259 employers) — missing from all prior documentation
4. **Book Name ≠ Contract Code** — STOCKMAN book → STOCKPERSON contract
5. **TERO APPR WIRE = compound book** — encodes agreement type + work level + classification
6. **Cross-regional registration** — 87% of Wire members on all 3 regional books
7. **APN 45880.41 on FOUR books** — validates many-to-many model
8. **Inverted tier distributions** — STOCKMAN Book 3 = 8.6× Book 1 (heavy travelers)

---

## Implementation Sub-Phases (7a–7g)

| Sub-Phase | Focus | Hours | Blocked By |
|-----------|-------|-------|------------|
| **7a** | Data Collection (3 Priority 1 exports) | 3-5 | LaborPower access |
| 7b | Schema Finalization (DDL + Alembic + seed) | 10-15 | 7a |
| 7c | Core Services + API (14 rules, CRUD, dispatch) | 25-35 | 7b |
| 7d | Import Tooling (CSV pipeline) | 15-20 | 7b |
| 7e | Frontend UI (books, dispatch board, web bidding) | 20-30 | 7c |
| 7f | Reports P0+P1 (49 reports) | 20-30 | 7c |
| 7g | Reports P2+P3 (29 reports) | 10-15 | 7f |

### Current Blockers (Priority 1 Data Gaps)

1. **REGLIST custom report with member identifiers** — member_id/card_number, name, book_name, book_priority_number, APN. MOST CRITICAL.
2. **RAW DISPATCH DATA custom report** — dispatch transaction structure unknown
3. **EMPLOYCONTRACT custom report** — need contract dates to explain 196 duplicate employer entries

---

## 14 Business Rules (Referral Procedures)

Source: IBEW Local 46 Referral Procedures, effective October 4, 2024

| Rule | Summary |
|------|---------|
| 1 | Office hours & regions (Kent 8-5, Bremerton 8-3) |
| 2 | Morning referral processing order by classification |
| 3 | Labor request cutoff (3 PM for next morning) |
| 4 | Agreement types (PLA, CWA, TERO) follow own terms |
| 5 | One registration per classification per member |
| 6 | Re-registration triggers (short call, under scale, 90-day, turnaround) |
| 7 | Re-sign required every 30 days |
| 8 | Internet bidding rules (5:30 PM – 7:00 AM, infractions) |
| 9 | Short calls (≤10 days, max 2 per cycle) |
| 10 | Check marks penalty system (2 allowed, 3rd = rolled off) |
| 11 | No check mark exceptions (specialty skills, MOUs, etc.) |
| 12 | Quit/discharge = rolled off all books |
| 13 | Foreperson-by-name anti-collusion |
| 14 | Exempt status (military, union business, medical, etc.) |

---

## Schema Summary (12 New Tables)

```sql
-- Core dispatch tables
registrations           -- Member-to-book registration tracking
referral_books          -- Book definitions with agreement_type, work_level
employer_contracts      -- Organization-to-contract relationships (8 codes)
job_requests           -- Employer labor requests with full lifecycle
dispatches             -- Dispatch transactions

-- Supporting tables
worksites              -- Physical job locations
web_bids               -- Online bidding records
check_marks            -- Penalty tracking per member per book
member_exemptions      -- Military, medical, union business exemptions
bidding_infractions    -- Internet bidding privilege revocation
blackout_periods       -- Quit/discharge restrictions
job_requirements       -- Lookup + junction for requirements
```

### Key Schema Rules

- **APN field:** `applicant_priority_number DECIMAL(10,2) NOT NULL`
- **Unique constraint:** `UNIQUE(member_id, book_id, book_priority_number)`
- **Index:** `(book_id, book_priority_number, applicant_priority_number) WHERE status = 'ACTIVE'`
- **contract_code nullable:** Tradeshow and TERO books have no contract

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [PHASE7_REFERRAL_DISPATCH_PLAN.md](PHASE7_REFERRAL_DISPATCH_PLAN.md) | Full implementation roadmap |
| [PHASE7_IMPLEMENTATION_PLAN_v2.md](PHASE7_IMPLEMENTATION_PLAN_v2.md) | Detailed technical plan |
| [LABORPOWER_GAP_ANALYSIS.md](LABORPOWER_GAP_ANALYSIS.md) | Feature gap assessment |
| [LABORPOWER_REFERRAL_REPORTS_INVENTORY.md](LABORPOWER_REFERRAL_REPORTS_INVENTORY.md) | 78 reports catalog |
| [LOCAL46_REFERRAL_BOOKS.md](LOCAL46_REFERRAL_BOOKS.md) | Seed data for books |
| [PHASE7_CONTINUITY_DOC_ADDENDUM.md](PHASE7_CONTINUITY_DOC_ADDENDUM.md) | Schedule reconciliation |

---

## Session Workflow Reminder

### Starting a Phase 7 Session

1. `git checkout develop`
2. `git pull origin develop`
3. Paste this document into Claude Code
4. Reference the specific sub-phase instruction document
5. Run tests: `pytest -v --tb=short`

### Ending a Phase 7 Session

> ⚠️ **MANDATORY:** Update *ANY* and *ALL* relevant documents to capture progress made this session.
> Scan `/docs/*` and make or create any relevant updates/documents.
> Do not forget about ADRs — update as necessary.

---

*Document Version: 2.0*
*Last Updated: February 4, 2026*
*Previous Version: 1.0 (February 3, 2026 — Initial creation)*
