# IP2A Database v2 (UnionCore) — Project Strategy & Game Plan

> **Document Created:** January 27, 2026
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Active — Strategic Planning (Updated to Reflect Current State)
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)

---

## Purpose

This document outlines the strategy for building IP2A Database v2 (UnionCore), a modular union data platform. It covers the project vision, phased approach, existing system integrations, technical architecture, and long-term roadmap.

**Project Owner:** Xerxes (Union Business Rep, IBEW Local 46)
**Repository:** <https://github.com/theace26/IP2A-Database-v2>

---

## Table of Contents

1. [Current State](#1-current-state)
2. [The Vision](#2-the-vision)
3. [Phase 1: Pre-Apprenticeship System](#3-phase-1-pre-apprenticeship-system)
4. [Phase 2+: Union Management Modules](#4-phase-2-union-management-modules)
5. [Existing Systems & Integration Strategy](#5-existing-systems--integration-strategy)
6. [Technical Architecture](#6-technical-architecture)
7. [Data Migration Strategy](#7-data-migration-strategy)
8. [Scaling Considerations](#8-scaling-considerations)
9. [Timeline & Milestones](#9-timeline--milestones)
10. [Key Decisions Made](#10-key-decisions-made)
11. [Open Questions](#11-open-questions)
12. [Reference Documents](#12-reference-documents)

---

## 1. Current State

### What's Been Built (v0.9.4-alpha — Feature-Complete)

After 19 weeks of intensive development, UnionCore has reached feature-complete status. The platform is deployed on Railway and actively serving its intended purpose.

| Component | Status | Notes |
|-----------|--------|-------|
| **Database Schema** | ✅ Complete | PostgreSQL 16, 26 ORM models, well-normalized |
| **Core Tables** | ✅ Complete | Members, Organizations, Students, Instructors, Locations, Cohorts |
| **File Attachments** | ✅ Complete | Document storage with metadata |
| **Audit Logging** | ✅ Complete | Full trail: READ, CREATE, UPDATE, DELETE ([ADR-012](../decisions/ADR-012-audit-logging.md)) |
| **Auto-Healing** | ✅ Complete | Self-repairing data integrity system |
| **CLI Tools** | ✅ Complete | `ip2adb` for seeding, integrity checks, load testing |
| **API Layer** | ✅ Complete | Flask + SQLAlchemy, ~150 endpoints |
| **Authentication** | ✅ Complete | Session-based auth with RBAC (Phase 3) |
| **Web UI** | ✅ Complete | Jinja2 + HTMX + Alpine.js + DaisyUI (Phases 5–6) |
| **Dues Tracking** | ✅ Complete | Full lifecycle: rates, periods, payments, adjustments (Phase 4 backend, Phase 6 Week 10 frontend) |
| **Payment Processing** | ✅ Complete | Stripe Checkout Sessions + Webhooks (Week 16) |
| **PWA** | ✅ Complete | Offline support, service worker (Week 18) |
| **Analytics Dashboards** | ✅ Complete | Chart.js visualizations (Week 19) |
| **Monitoring** | ✅ Complete | Sentry error tracking ([ADR-007](../decisions/ADR-007-monitoring-strategy.md)) |
| **PDF/Excel Export** | ✅ Complete | WeasyPrint PDFs, openpyxl Excel exports |
| **Deployment** | ✅ Complete | Railway (production) |

**Key Metrics:**
- ~470 tests (pytest)
- 26 ORM models
- ~150 API endpoints
- 14 Architecture Decision Records
- 19 weeks of development

### Stress Test Results (Validates Scalability)

- **515,356 records** processed in 10.5 minutes
- **84 MB** database size
- **818 records/second** throughput
- **4,537 issues** auto-detected and repaired (100% success rate)
- **Capacity:** Proven to handle 500K+ records easily

### Repository & Technical Stack

- **Repository:** <https://github.com/theace26/IP2A-Database-v2>
- **Database:** PostgreSQL 16
- **Backend:** Python 3.12, Flask, SQLAlchemy 2.x
- **Frontend:** Jinja2 templates, HTMX, Alpine.js, DaisyUI (Tailwind CSS)
- **Deployment:** Railway (cloud PaaS)
- **Payments:** Stripe (Checkout Sessions + Webhooks)
- **Monitoring:** Sentry
- **PDF Generation:** WeasyPrint
- **Excel Export:** openpyxl
- **Testing:** pytest (~470 tests)
- **Current Version:** v0.9.4-alpha

### What's Next: Phase 7 — Referral & Dispatch

Phase 7 will implement the referral and dispatch system, replacing LaborPower. Extensive analysis has been completed:

- 78 de-duplicated reports (from 91 raw LaborPower files)
- 12 new database tables planned
- 14 business rules identified
- 11 books (out-of-work lists)
- ~843 employers across 8 contract codes
- Sub-phases 7a–7g, estimated 100–150 hours
- 3 Priority 1 data gaps must be resolved before Phase 7a begins

See [Phase 7 Planning Documents](../phase7/) for full details.

---

## 2. The Vision

### The Problem

Currently operating with fragmented data across multiple systems:

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   LaborPower    │  │   LaborPower    │  │   Access DB     │  │   QuickBooks    │
│   (Referral/    │  │   (Dues         │  │   (Member       │  │   (Accounting)  │
│    Dispatch)    │  │    Collection)  │  │    Records)     │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
        │                    │                    │                    │
        └────────────────────┴────────────────────┴────────────────────┘
                                      │
                    No unified view, duplicate data entry,
                    manual reconciliation required
```

### The Solution

One modular database platform (UnionCore) with pluggable modules:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     UNIONCORE (IP2A DATABASE v2)                            │
│                      (Unified Data Platform)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│   │    CORE     │  │   PRE-APP   │  │    UNION    │  │  EXTERNAL   │      │
│   │   TABLES    │  │   MODULE    │  │   MODULES   │  │   SYNC      │      │
│   ├─────────────┤  ├─────────────┤  ├─────────────┤  ├─────────────┤      │
│   │ Users/Auth  │  │ Grants      │  │ Dues ✅     │  │ QuickBooks  │      │
│   │ Orgs        │  │ Students    │  │ Referrals 🔜│  │ (sync)      │      │
│   │ Audit Logs  │  │ Cohorts     │  │ Market Rec  │  │ Stripe ✅   │      │
│   │ Files       │  │ Certs       │  │ Grievances  │  │             │      │
│   │ Members     │  │ Placements  │  │ Benevolence │  │             │      │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
│         │                │                │                │                │
│         └────────────────┴────────────────┴────────────────┘                │
│                                 │                                           │
│                    Single source of truth                                   │
│                    Cross-module reporting                                   │
│                    Unified member journey                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Long-Term Potential

If the system proves successful:

1. Use internally at Local 46 (replacing 3 legacy systems)
2. Offer to other IBEW locals as alternative to LaborPower
3. Potentially commercialize as competing union management platform

---

## 3. Phase 1: Pre-Apprenticeship System

> **Status:** ✅ Complete — Phases 1–6 delivered the pre-apprenticeship foundation and full web UI.

### Why We Started Here

| Reason | Explanation |
|--------|-------------|
| **Contained scope** | Clear boundaries, limited users |
| **Lower stakes** | Won't break existing union operations if issues arise |
| **Real need** | Grant reporting is painful without proper tracking |
| **Proves concept** | Success here validates the approach |
| **Foundation** | Students become members—data follows them |

### Features Delivered

The following capabilities are implemented and tested:

- **Student Management** — Application/intake, demographics, contact info, eligibility, status tracking (APPLICANT → ENROLLED → ACTIVE → COMPLETED → PLACED)
- **Grant Management** — Sources, funding amounts/periods, reporting requirements, per-student cost tracking, enrollment caps
- **Cohort Management** — Class/session groupings, instructor/location assignments, schedule tracking, capacity management
- **Progress Tracking** — Curriculum completion, attendance, assessment scores, competency sign-offs
- **Certification Tracking** — OSHA 10/30, First Aid/CPR, Forklift, other industry certs, expiration tracking
- **Placement Tracking** — Apprenticeship applications, acceptance/rejection, employer placement, follow-up surveys
- **Reporting** — Demographics breakdown, completion rates, certification attainment, placement rates, cost per student, date range filtering, Excel/PDF export

### Schema (Implemented)

The following tables support the pre-apprenticeship module:

- `grants` — Grant source, funding, caps, reporting frequency
- `grant_enrollments` — Student-to-grant linkage with funding amounts
- `student_progress` — Enrollment, completion, attendance, grades
- `certifications` / `student_certifications` — Cert catalog and student cert records
- `placements` — Post-program employment tracking with follow-up
- `attendance` — Per-session attendance records

---

## 4. Phase 2+: Union Management Modules

These modules expand beyond pre-apprenticeship into full union operations:

### Module: Members (Foundation for Everything) — ✅ Complete

The `members` table is the single source of truth. Students link to members when they graduate to apprenticeship via `former_student_id`.

### Module: Dues Collection — ✅ Complete (Phase 4 + Phase 6 Week 10)

Full dues lifecycle implemented:

- **DuesRate** — Classification-based pricing with historical tracking
- **DuesPeriod** — Monthly billing cycles with close/open management
- **DuesPayment** — Payment records with status tracking (pending, paid, partial, overdue, waived)
- **DuesAdjustment** — Waivers, credits, hardship, corrections with approval workflow

Payment processing integrated via Stripe Checkout Sessions + Webhooks (Week 16).

See [Dues Tracking Guide](../guides/dues-tracking.md) and [ADR-008](../decisions/ADR-008-dues-tracking-system.md).

### Module: Referral/Dispatch — 🔜 Phase 7 (Next)

This is the next major module, replacing LaborPower's core referral/dispatch functionality:

- 12 new database tables designed
- 14 business rules documented from LaborPower analysis
- 11 out-of-work books across 8 contract codes
- ~843 employers to import
- Sub-phases 7a–7g planned, 100–150 hours estimated

Key tables: `out_of_work_list`, `referrals`, `job_calls`, `dispatch_records`, plus supporting tables for contract codes, classifications, and employer agreements.

See [Phase 7 Planning Documents](../phase7/) for complete specifications.

### Module: Market Recovery — 🔜 Future

Replaces the Access database for market recovery program tracking:

- Program definitions with subsidy rates and budgets
- Member assignments to employers/projects
- Weekly hours submission and approval workflow
- QuickBooks sync for payment processing

### Module: Grievances — 🔜 Future

Formal grievance tracking through multi-step processes:

- Grievance filing and case management
- Step progression (Step 1 → Step 2 → Step 3 → Arbitration)
- Representative assignments
- Resolution and settlement tracking

### Module: Benevolence Fund — 🔜 Future

Member assistance program management:

- Application intake and review
- Approval workflow with supporting documentation
- Payment processing and QuickBooks sync

---

## 5. Existing Systems & Integration Strategy

### Current Systems Inventory

| System | Purpose | Data Volume | Integration Plan | Status |
|--------|---------|-------------|------------------|--------|
| **LaborPower (Referral)** | Dispatch, job calls | ~4,000 members, ~843 employers | Phase 7: Build replacement | 🔜 Analysis complete |
| **LaborPower (Dues)** | Payment collection | ~4,000 members | Already replaced by Phase 4 | ✅ Replaced |
| **Access DB** | Member records | Unknown | Future: Replace entirely | 🔜 Planned |
| **QuickBooks** | Accounting | All financials | Ongoing sync (export/import, not replace) | 🔜 Sync planned |

### Integration Strategy

#### LaborPower

- **Analysis complete:** 24 files analyzed, 8 critical findings documented
- **Key findings:** APN stored as DECIMAL (not integer), RESIDENTIAL is the 8th contract code (not 7 total), inverted tier ordering
- **Strategy:** Build complete replacement (UnionCore), not integration
- **Phase 7:** Implements referral/dispatch replacement
- **3 Priority 1 data gaps** must be resolved before migration begins

#### Access Database

- **Strategy:** Full replacement
- **Process:** Export tables to CSV → map fields to UnionCore schema → import historical data → retire Access DB

#### QuickBooks

- **Strategy:** Sync, not replace
- **Direction:** UnionCore → QuickBooks (dues income, expenses); QuickBooks → UnionCore (payment cleared status)
- **Method:** CSV export/import initially, API integration later

---

## 6. Technical Architecture

### Current Stack (Implemented)

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Database** | PostgreSQL 16 | 26 ORM models, Railway-hosted |
| **Backend** | Python 3.12, Flask, SQLAlchemy 2.x | ~150 endpoints, service layer pattern |
| **Frontend** | Jinja2, HTMX, Alpine.js, DaisyUI | Server-rendered with progressive enhancement |
| **Deployment** | Railway | Cloud PaaS, CI/CD from GitHub |
| **Payments** | Stripe | Checkout Sessions + Webhooks (live) |
| **Monitoring** | Sentry | Error tracking and performance ([ADR-007](../decisions/ADR-007-monitoring-strategy.md)) |
| **PDF Export** | WeasyPrint | Report generation |
| **Excel Export** | openpyxl | Data export |
| **PWA** | Service Worker | Offline support (Week 18) |
| **Analytics** | Chart.js | Dashboard visualizations (Week 19) |
| **Testing** | pytest | ~470 tests |

### Modular Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│   Jinja2 Templates + HTMX + Alpine.js + DaisyUI                │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        ROUTE LAYER                               │
│   Flask Blueprints: /members  /dues  /students  /auth   ...    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                               │
│   member_service    dues_service    student_service    ...      │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
│   Member model      DuesPayment model    Student model    ...   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   SHARED INFRASTRUCTURE                          │
│   Audit Logging    Auth/RBAC    File Storage    Sentry          │
│   Stripe           WeasyPrint   openpyxl        Service Worker  │
└─────────────────────────────────────────────────────────────────┘
```

**Key principles:**

1. **Loose coupling:** Modules don't directly depend on each other
2. **Shared core:** Users, organizations, audit logs used by all
3. **Consistent patterns:** Every module follows same service-layer/Blueprint patterns
4. **Feature flags:** Modules can be enabled/disabled per installation

---

## 7. Data Migration Strategy

### Phase 1: Pre-Apprenticeship — ✅ Complete

- Manual entry and spreadsheet import
- Small volume, handled via seed scripts and web UI

### Phase 7: LaborPower Import (Next)

**Data to import:**

| Table | Source | Est. Records | Priority |
|-------|--------|--------------|----------|
| Members | LaborPower | ~4,000 active | Critical |
| Employers | LaborPower | ~843 | Critical |
| Employment history | LaborPower | ~50,000+ | High |
| Out-of-work list | LaborPower | Current list | Critical |
| Referral history | LaborPower | ~20,000+ | Medium |

**Import approach:**

```bash
# Preview import (no changes)
ip2adb import members --source laborpower --file members.csv --preview

# Execute import
ip2adb import members --source laborpower --file members.csv --execute

# Import with field mapping file
ip2adb import employers --source laborpower --file employers.csv --mapping employer_map.json

# Validate imported data
ip2adb integrity --tables members,organizations
```

### Future: Access DB Import

**Process:** Open Access database → export each table to CSV → map fields to UnionCore schema → import via CLI

---

## 8. Scaling Considerations

### Current Capacity

- **Tested:** 515K+ records at 818 records/second
- **Deployed on:** Railway (cloud PaaS with auto-scaling)
- **Current user base:** ~40 staff + ~4,000 members

### When to Scale

Scaling infrastructure should be added when you see:

- Connection pool exhaustion errors
- Response times > 500ms under normal load
- Database CPU consistently > 70%

### Scaling Path (For Reference)

| Phase | Trigger | Solution | Capacity |
|-------|---------|----------|----------|
| Current | N/A | Railway PostgreSQL | ~50 concurrent users |
| Scale 1 | Connection errors | Add PgBouncer | ~500 concurrent users |
| Scale 2 | Read bottleneck | Add read replicas | ~2,000 concurrent users |
| Scale 3 | Repeated queries | Add Redis cache | ~5,000 concurrent users |
| Scale 4 | CPU bottleneck | Multiple app servers | ~10,000+ concurrent users |

**Key point:** Don't implement scaling until needed. Build features first.

---

## 9. Timeline & Milestones

### Completed Development (Weeks 1–19)

| Phase | Weeks | Focus | Status |
|-------|-------|-------|--------|
| **Phase 1** | 1–4 | Core models, schema, CLI tools | ✅ Complete |
| **Phase 2** | 5–7 | Members, organizations, file attachments | ✅ Complete |
| **Phase 3** | 8–9 | Authentication, RBAC, session management | ✅ Complete |
| **Phase 4** | 10–11 | Dues tracking backend (rates, periods, payments, adjustments) | ✅ Complete |
| **Phase 5** | 12–13 | Frontend foundation (Jinja2 + HTMX + Alpine.js + DaisyUI) | ✅ Complete |
| **Phase 6** | 14–19 | Full frontend, Stripe, PWA, analytics, polish | ✅ Complete |

> **Note:** Week 15 was intentionally skipped in numbering (14 → 16). This is not an error.

### Upcoming Development

| Phase | Est. Duration | Focus | Status |
|-------|---------------|-------|--------|
| **Phase 7** | 100–150 hours | Referral & Dispatch (replace LaborPower) | 🔜 Analysis complete |
| **Phase 8** | TBD | Market Recovery (replace Access DB) | 🔜 Planned |
| **Phase 9** | TBD | Grievances module | 🔜 Planned |
| **Phase 10** | TBD | Benevolence Fund | 🔜 Planned |
| **Phase 11** | TBD | Member self-service portal | 🔜 Planned |

### Key Milestones

| Milestone | Status | Notes |
|-----------|--------|-------|
| **Auth working** | ✅ Complete | Session-based auth + RBAC (Phase 3) |
| **First grant tracked** | ✅ Complete | Grant + students in system |
| **First report generated** | ✅ Complete | PDF/Excel export working |
| **Dues system live** | ✅ Complete | Full lifecycle + Stripe payments |
| **Web UI complete** | ✅ Complete | All modules have frontend (Phase 6) |
| **PWA deployed** | ✅ Complete | Offline support (Week 18) |
| **Analytics dashboards** | ✅ Complete | Chart.js visualizations (Week 19) |
| **Production deployment** | ✅ Complete | Railway (live) |
| **LaborPower replaced** | 🔜 Phase 7 | Referral/dispatch system |
| **Access DB retired** | 🔜 Phase 8 | Market Recovery in UnionCore |
| **Member portal live** | 🔜 Phase 11 | Members can view own records |

---

## 10. Key Decisions Made

| Decision | Choice | Rationale | ADR |
|----------|--------|-----------|-----|
| **Start with pre-apprenticeship** | Yes | Lower stakes, proves concept, clear scope | — |
| **Combine LP + Access into one DB** | Yes | Single source of truth, unified reporting | — |
| **Keep QuickBooks separate** | Yes | Don't rebuild accounting, just sync | — |
| **Flask over FastAPI** | Flask | Server-rendered templates, simpler deployment, better Jinja2 integration | [ADR-001](../decisions/ADR-001-framework-selection.md) |
| **Jinja2 + HTMX + Alpine.js** | Yes | Progressive enhancement, no SPA complexity, excellent DX | [ADR-010](../decisions/ADR-010-frontend-architecture.md) |
| **DaisyUI for styling** | Yes | Tailwind-based, component library, consistent design | [ADR-010](../decisions/ADR-010-frontend-architecture.md) |
| **Stripe for payments** | Stripe | PCI compliance handled, Checkout Sessions + Webhooks | [ADR-009](../decisions/ADR-009-payment-processing.md) |
| **Sentry for monitoring** | Sentry | Error tracking, performance monitoring, Railway-compatible | [ADR-007](../decisions/ADR-007-monitoring-strategy.md) |
| **Railway for deployment** | Railway | Cloud PaaS, GitHub integration, managed PostgreSQL | [ADR-006](../decisions/ADR-006-deployment-strategy.md) |
| **Build modular architecture** | Yes | Add features without breaking existing | — |
| **Scale later, features first** | Yes | Current capacity sufficient | — |
| **Replace LaborPower (not integrate)** | Replace | Build better system informed by LP analysis | — |

---

## 11. Open Questions

### Resolved ✅

| Question | Resolution |
|----------|------------|
| What frontend framework? | Jinja2 + HTMX + Alpine.js + DaisyUI (server-rendered) |
| Self-hosted or cloud deployment? | Railway (cloud PaaS) |
| Backup strategy? | Railway managed PostgreSQL backups |
| What format can LaborPower export? | 24 files analyzed (CSV/report exports); 78 de-duplicated reports |
| Payment integration? | Stripe Checkout Sessions + Webhooks (live) |

### Still Open

- [ ] What tables exist in the Access database? (needed for Phase 8)
- [ ] Which QuickBooks version? (Desktop or Online — affects sync approach)
- [ ] What are the current grant reporting requirements? (for refinement)
- [ ] What's the approval workflow for Market Recovery hours? (for Phase 8)
- [ ] 3 Priority 1 data gaps for Phase 7 (must resolve before 7a)

### To Investigate

- [ ] Resolve 3 Priority 1 data gaps blocking Phase 7a
- [ ] Get Access database table/field inventory
- [ ] Document current Market Recovery workflow
- [ ] Evaluate QuickBooks API vs CSV sync

---

## 12. Reference Documents

### Architecture & Decisions

| Document | Location | Purpose |
|----------|----------|---------|
| **CLAUDE.md** | `/CLAUDE.md` | Project context for AI assistance |
| **System Overview** | `/docs/architecture/SYSTEM_OVERVIEW.md` | Architecture documentation |
| **ADR Index** | `/docs/decisions/README.md` | All 14 architecture decisions |
| **Milestone Checklist** | `/docs/IP2A_MILESTONE_CHECKLIST.md` | Task tracking |
| **Backend Roadmap** | `/docs/IP2A_BACKEND_ROADMAP.md` | Development plan (v3.0) |

### Phase 7 Planning

| Document | Location | Purpose |
|----------|----------|---------|
| **Phase 7 Overview** | `/docs/phase7/` | Referral/dispatch planning |
| **LaborPower Analysis** | `/docs/phase7/laborpower-analysis.md` | System analysis findings |

### Standards & Guides

| Document | Location | Purpose |
|----------|----------|---------|
| **Coding Standards** | `/docs/standards/coding-standards.md` | Code conventions |
| **Naming Conventions** | `/docs/standards/naming-conventions.md` | Naming patterns |
| **Testing Strategy** | `/docs/guides/testing-strategy.md` | Test approach |
| **Audit Logging** | `/docs/guides/audit-logging.md` | Audit standards |
| **End-of-Session Docs** | `/docs/guides/END_OF_SESSION_DOCUMENTATION.md` | Session documentation rules |

### Key Commands

```bash
# Development
flask run --debug               # Start development server
ip2adb seed                     # Populate test data
ip2adb integrity --repair       # Check and fix data integrity
ip2adb load --quick             # Quick performance test

# Testing
pytest -v                       # Run all ~470 tests
pytest --cov=src                # Run with coverage

# Deployment
git push origin develop         # Railway auto-deploys from develop
```

---

## Summary

**The Plan:**

1. ~~Build pre-apprenticeship system first~~ ✅ Complete
2. ~~Prove it works with real users~~ ✅ Deployed on Railway
3. Expand to union modules — **Phase 7 (Referral/Dispatch) is next**
4. Eventually run parallel to and replace LaborPower
5. Potentially commercialize for other locals

**The Approach:**

- Modular architecture — add features without breaking existing
- Start small, validate, expand
- Keep QuickBooks for accounting, sync data
- Integrate payment processing (Stripe ✅), don't build it

**The Reality:**

- 19 weeks of development completed (feature-complete)
- Phase 7 (Referral/Dispatch) estimated at 100–150 hours
- Each subsequent module: 2–3 months
- Building a LaborPower **replacement**, not just a supplement

**Next Steps:**

1. Resolve 3 Priority 1 data gaps blocking Phase 7a
2. Begin Phase 7a: schema + seed data for referral/dispatch
3. Get Access database inventory for Phase 8 planning
4. Evaluate QuickBooks sync approach

---

> **End-of-Session Rule:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

---

| Cross-Reference | Location |
|----------------|----------|
| ADR-001: Framework Selection | `/docs/decisions/ADR-001-framework-selection.md` |
| ADR-006: Deployment Strategy | `/docs/decisions/ADR-006-deployment-strategy.md` |
| ADR-007: Monitoring Strategy | `/docs/decisions/ADR-007-monitoring-strategy.md` |
| ADR-008: Dues Tracking System | `/docs/decisions/ADR-008-dues-tracking-system.md` |
| ADR-009: Payment Processing | `/docs/decisions/ADR-009-payment-processing.md` |
| ADR-010: Frontend Architecture | `/docs/decisions/ADR-010-frontend-architecture.md` |
| ADR-012: Audit Logging | `/docs/decisions/ADR-012-audit-logging.md` |
| Backend Roadmap v3.0 | `/docs/IP2A_BACKEND_ROADMAP.md` |
| Milestone Checklist | `/docs/IP2A_MILESTONE_CHECKLIST.md` |
| Phase 7 Planning | `/docs/phase7/` |

---

*Document Version: 2.0*
*Last Updated: February 3, 2026*
*Status: Active — Updated to reflect v0.9.4-alpha feature-complete state*
