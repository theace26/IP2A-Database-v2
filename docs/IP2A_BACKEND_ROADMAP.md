# UnionCore Backend Roadmap

**Document Purpose:** Master development plan with phases, milestones, and strategic context
**Version:** v5.0
**Last Updated:** February 6, 2026
**Project Version:** v0.9.10-alpha

---

## Executive Summary

UnionCore is a comprehensive union management platform for IBEW Local 46, replacing three fragmented legacy systems (LaborPower, Access Database, manual processes) with a unified, auditable system. QuickBooks integration is maintained for accounting (sync-don't-replace philosophy).

| Metric | Value |
|--------|-------|
| **Users** | ~4,000 external (members, stewards, applicants) + ~40 internal (staff, officers) |
| **Tests** | 621 total (~596 passing, 98.5% pass rate, Week 35) |
| **Endpoints** | ~240+ |
| **Models** | 32 (26 core + 6 Phase 7) |
| **ADRs** | 18 |
| **Deployment** | Railway (live) |

### Phase Overview

| Phase | Description | Status | Owner |
|-------|-------------|--------|-------|
| 1-4 | Core Platform (Members, Auth, Training, Dues) | ✅ Complete | Spoke 1 |
| 5 | Access DB Migration | ⏸️ Blocked | Spoke 1 |
| 6 | Frontend (Weeks 1-19) | ✅ Complete | Spoke 3 |
| 7 | Referral & Dispatch (Weeks 20-35) | 🔄 In Progress | Spoke 2 |
| 8 | Square Payment Migration | 🔄 In Progress (Stripe removed Week 35) | Spoke 3 |

---

## Hub/Spoke Development Model

UnionCore uses a Hub/Spoke model for development planning. This is an organizational structure for Claude AI conversations, not a code architecture pattern.

### Project Assignments

| Project | Scope | Phases |
|---------|-------|--------|
| **Hub** | Strategy, architecture, ADRs, cross-cutting decisions | All |
| **Spoke 2: Operations** | Dispatch/Referral, Pre-Apprenticeship, SALTing | Phase 7 |
| **Spoke 1: Core Platform** | Members, Dues, Employers, Training | Phases 1-4, 5 |
| **Spoke 3: Infrastructure** | UI, Reports, Deployment, Monitoring | Phase 6, 8 |

### Key Principles

1. **CLAUDE.md is the single source of truth** for project state
2. **Claude Code executes all instruction documents** regardless of source Spoke
3. **Sprint weeks ≠ calendar weeks** — at 5-10 hrs/week, each sprint takes 1-2 calendar weeks
4. **Handoff notes bridge Spokes** since Claude cannot access cross-project conversations

---

## Governance Philosophy

**"The Schema is Law"** — data accuracy, auditability, and production safeguards above all else.

- 7-year NLRA record retention requirement
- All member data changes logged with who/what/when/old-value/new-value
- Audit logs are IMMUTABLE (no UPDATE or DELETE, ever)
- Two-tier logging: PostgreSQL for business audit, Grafana+Loki for operational monitoring
- Defense-in-depth security with JWT authentication and RBAC

---

## Phases 1-4: Core Platform — ✅ COMPLETE

### Phase 1: Organization & Members
- Organization, Member, Employment, MemberClassification models
- CRUD services and API endpoints
- Member search and filtering
- Employment history tracking

### Phase 2: Authentication & RBAC
- JWT with bcrypt password hashing
- Access tokens (15 min) + refresh tokens (7 days)
- Role hierarchy (Admin → Officer → Staff → Organizer → Instructor → Member → Applicant)
- Permission matrix enforcement
- Account lockout and password history

### Phase 3: Union Operations
- SALTing campaigns and contacts
- Benevolence Fund applications and disbursements
- Grievance filing and workflow
- Status tracking and audit trails

### Phase 4: Training Module
- Student enrollment and cohort management
- Course catalog and scheduling
- Grade recording and certificate generation
- Attendance tracking
- FERPA-adjacent access controls

### Phase 4b: Documents
- MinIO (dev) / S3 (prod) object storage
- Presigned URLs for secure access
- Lifecycle management tiers
- Entity-organized file structure (members/, students/, grievances/, grants/)

### Phase 4c: Dues
- Dues rates by member classification
- Dues periods (monthly/quarterly)
- Payment recording and tracking
- Adjustment workflow (waivers, credits, refunds)
- Overdue notifications

---

## Phase 5: Access DB Migration — ⏸️ BLOCKED

**Blocker:** Stakeholder approval pending for Market Recovery data access

### Strategy
- Frame UnionCore as complementary, not replacement
- Demonstrate proof-of-concept with test data before requesting production access
- Protect Access Database owner's role (her system, her baby)

### Tasks (When Unblocked)
1. Export Market Recovery data from Access
2. Map schema to UnionCore models
3. Build import pipeline
4. Validate and reconcile
5. Parallel run period
6. Cutover

---

## Phase 6: Frontend — ✅ COMPLETE

### Technology Stack
- Jinja2 templates (server-side rendering)
- HTMX (dynamic interactions without JavaScript complexity)
- Alpine.js (micro-interactions: dropdowns, toggles)
- Tailwind CSS + DaisyUI (styling via CDN, no build step)

### Weeks 1-19 Summary
| Week | Focus | Tests |
|------|-------|-------|
| 1 | Setup + Login | 10 |
| 2 | Auth Cookies + Dashboard | 8 |
| 3 | Staff Management | 18 |
| 4 | Training Landing | 19 |
| 5 | Members Landing | 15 |
| 6 | Union Operations | 21 |
| 8 | Reports & Export | 30 |
| 9 | Documents Frontend | 6 |
| 10 | Dues UI | 37 |
| 11 | Audit UI + Stripe | 15 |
| 12 | Profile & Settings | 8 |
| 14 | Grant Compliance | 12 |
| 16 | Production Hardening | 32 |
| 18 | Mobile PWA | 14 |
| 19 | Analytics Dashboard | 19 |

---

## Phase 7: Referral & Dispatch — 🔄 IN PROGRESS

**Owner:** Spoke 2: Operations
**Scope:** Replace LaborPower with modern, auditable dispatch system
**Estimated Total:** 100-150 hours across sub-phases 7a-7g

### What Phase 7 Replaces

LaborPower is the legacy dispatch system managing:
- Out-of-work registration lists (11 books)
- Labor request intake from employers
- Morning referral processing
- Web/email bidding
- Check mark (penalty) tracking
- Dispatch history

### Completed Work (Weeks 20-30)

**Models (6 new tables):**
- ReferralBook — Book definitions with contract codes and agreement types
- BookRegistration — Member out-of-work entries with APN (DECIMAL(10,2))
- LaborRequest — Employer labor requests with lifecycle management
- Dispatch — Referral transactions linking all entities
- JobBid — Internet bidding records
- RegistrationActivity — Audit trail for registration changes

**Services (7):**
- ReferralBookService, BookRegistrationService, LaborRequestService
- DispatchService, JobBidService, RegistrationActivityService
- DispatchBusinessRulesService (14 business rules)

**API Routers (5):**
- referral_books.py, book_registrations.py, labor_requests.py
- dispatches.py, job_bids.py
- ~50 new endpoints

**Frontend (13 pages, 15 partials):**
- Dispatch dashboard with live stats
- Labor request list and detail views
- Morning referral processing page with time guards
- Active dispatches tracking
- Queue management with book tabs
- Enforcement dashboard (suspensions, violations)

**Migration:**
- Phase 7 Alembic migration applied (6 tables)
- All relationships verified

### Business Rules Implemented (14)

| # | Rule | Implementation |
|---|------|----------------|
| 1 | Office Hours & Regions | Region entities with operating parameters |
| 2 | Morning Referral Order | Wire 8:30 AM → S&C 9:00 AM → Tradeshow 9:30 AM |
| 3 | Labor Request Cutoff | 3 PM for next morning; web bids after 5:30 PM |
| 4 | Agreement Types | PLA/CWA/TERO on requests and books |
| 5 | Registration Rules | One per classification per member |
| 6 | Re-Registration Triggers | Short call, under scale, 90-day, turnarounds |
| 7 | Re-Sign 30-Day Cycle | Automated alert/drop logic |
| 8 | Internet/Email Bidding | 5:30 PM – 7:00 AM window; 2 rejections = 1 year ban |
| 9 | Short Calls | ≤10 days; max 2 per cycle; ≤3 days don't count |
| 10 | Check Marks | 2 allowed, 3rd = rolled off book |
| 11 | No Check Mark Exceptions | Specialty skills, MOU, early starts |
| 12 | Quit or Discharge | Rolled off ALL books; 2-week blackout |
| 13 | Foreperson By Name | Anti-collusion enforcement |
| 14 | Exempt Status | Military, union, salting, medical, jury |

### Sub-Phases 7a-7g (Remaining Work)

| Sub-Phase | Focus | Hours | Status |
|-----------|-------|-------|--------|
| 7a | Data Collection — 3 LaborPower exports | 3-5 | ⛔ Blocked |
| 7b | Schema Finalization — DDL, migrations | 10-15 | Ready when 7a done |
| 7c | Core Services + API — 14 rules, CRUD | 25-35 | After 7b |
| 7d | Import Tooling — CSV pipeline | 15-20 | Parallel with 7c |
| 7e | Frontend UI — dispatch board, bidding | 20-30 | After 7c |
| 7f | Reports P0+P1 — 49 critical reports | 20-30 | After 7c |
| 7g | Reports P2+P3 — 29 lower priority | 10-15 | After 7f |

### LaborPower Report Inventory (~78 reports)

| Priority | Count | Examples |
|----------|-------|----------|
| P0 (Critical) | 16 | Out-of-work lists, dispatch logs |
| P1 (High) | 33 | Registration history, check marks |
| P2 (Medium) | 22 | Analytics, trend reports |
| P3 (Low) | 7 | Projections, ad-hoc queries |

---

## Phase 8: Square Payment Migration — 📋 PLANNED

**Reference:** ADR-018
**Trigger:** After Phase 7 stabilizes
**Rationale:** Square already used at union hall; consolidate payment processing

### Sub-Phases
- **Phase A:** Online Payments (Square Web Payments SDK)
- **Phase B:** Terminal/POS Integration
- **Phase C:** Invoice Generation

### Migration Steps
1. Create Square developer account
2. Implement Square Web Payments SDK
3. Update dues payment flow
4. Migrate existing Stripe webhooks
5. Remove Stripe skip markers from tests
6. Archive Stripe code
7. Update ADR-003 (Auth) and ADR-018

---

## Key Documents Reference

| Document | Location |
|----------|----------|
| Project Context | `CLAUDE.md` |
| Milestone Checklist | `docs/IP2A_MILESTONE_CHECKLIST.md` |
| Phase 7 Consolidated | `docs/phase7/UnionCore_Continuity_Document_Consolidated.md` |
| LaborPower Gap Analysis | `docs/phase7/LABORPOWER_GAP_ANALYSIS.md` |
| Reports Inventory | `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` |
| ADRs | `docs/decisions/ADR-*.md` |

---

## Timeline Expectations

**Developer Context:** Part-time volunteer project, 5-10 hours/week

| Phase | Estimated Duration |
|-------|-------------------|
| Phase 7 completion | 3-4 months |
| Phase 8 (Square) | 1-2 months |
| Full LaborPower parity | 6-8 months |

**Sprint weeks ≠ calendar weeks.** Instruction documents reference "Week 30" etc. as sprint numbers. At 5-10 hrs/week, each sprint takes 1-2 calendar weeks to complete.

---

*UnionCore Backend Roadmap — v4.0 — February 5, 2026*
