# IP2A-Database-v2 — Instruction Document Creation Continuity

> **Created:** February 4, 2026
> **Purpose:** Paste this into a new Claude chat to resume work on IP2A-Database-v2
> **Scope:** Phase 7 instruction document creation — Weeks 20–25 complete, Week 26 pending

---

## Project Context

**Project:** IP2A-Database-v2 (UnionCore) — workplace organization operations management platform for IBEW Local 46
**Current Version:** v0.9.5-alpha (Feature-Complete Weeks 1–19, Phase 7 Foundation Weeks 20–22)
**Owner:** Xerxes (Union Business Rep, IBEW Local 46)
**GitHub:** theace26

**What UnionCore replaces:** 3 legacy systems at IBEW Local 46:
- **LaborPower** — referral/dispatch (being replaced, NOT integrated)
- **Access Database** — member records
- **QuickBooks** — dues (sync, not replace)

**User base:** ~40 staff + ~4,000 members

### Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, **FastAPI**, SQLAlchemy 2.x |
| Frontend | **Jinja2 + HTMX + Alpine.js + DaisyUI** (Tailwind CSS) |
| Database | PostgreSQL 16 |
| Deployment | **Railway** (cloud PaaS) |
| Payments | **Stripe** (Checkout Sessions + Webhooks) |
| Monitoring | **Sentry** (NOT Grafana/Loki) |
| PDF Export | WeasyPrint |
| Excel Export | openpyxl |
| PWA | Service Worker (offline support, Week 18) |
| Analytics | Chart.js (Week 19) |
| Testing | pytest + httpx (~490+ tests) |
| Linting | ruff |

> **⚠️ CRITICAL — Tech stack correction:** Some older planning docs (PHASE7_CONTINUITY_DOC_ADDENDUM, instruction creation continuity doc from Feb 3) incorrectly stated **Flask**. The project uses **FastAPI**. The Known Pitfalls list in those docs was INVERTED (said "❌ FastAPI → ✅ Flask" when it should be the opposite). All instruction documents created in THIS session (Weeks 23–25) use the correct stack. The Weeks 20–22 instruction docs also had this error — it was caught and corrected during the Wk20–22 implementation session.

### Key Metrics (Post-Weeks 20–22 Implementation)
- ~490+ tests, 32 ORM models (26 existing + 6 Phase 7), ~150 API endpoints, **15 ADRs** (ADR-015 added Feb 4)
- Phase 7: 6 models, 19 enums, 6 schema files, 2 services, 11-book seeds, 20+ model tests
- Documentation update project: ALL 5 batches complete
- Phase 7 instruction docs: Weeks 20–25 complete, **Week 26 pending**

---

## What Was Done This Session

### Instruction Documents Created

Three Phase 7 weekly instruction documents were created (Weeks 23–25). These are session-primer files that get pasted into new Claude chats to provide full context for each development week.

| Document | Lines | Status | Scope |
|----------|-------|--------|-------|
| WEEK_23_INSTRUCTIONS.md | 693 | ✅ Created & delivered | Dispatch Services — LaborRequestService, JobBidService, DispatchService |
| WEEK_24_INSTRUCTIONS.md | 580 | ✅ Created & delivered | Queue Management — QueueService, EnforcementService, analytics |
| WEEK_25_INSTRUCTIONS.md | 974 | ✅ Created, **NOT YET delivered** | API Endpoints — Routers for all Phase 7 services |
| WEEK_26_INSTRUCTIONS.md | — | ❌ **Not yet created** | Frontend — Books & Registration UI |

> **⚠️ Week 25 was fully created but needs to be delivered to user.** It exists on Claude's side but wasn't copied to outputs before the session ended. Ask Claude to present it in the next session, or recreate it following the conventions below.

### Session Also Included

- Scanned 8 uploaded documents: CLAUDE.md, CHANGELOG.md, IP2A_BACKEND_ROADMAP.md, IP2A_MILESTONE_CHECKLIST.md, PHASE7_CONTINUITY_DOC.md, 2026-02-04-phase7-weeks20-22.md (session log), ADR-015-referral-dispatch-architecture.md, decisions/README.md
- Updated Claude memory: 15 ADRs (was 14), session log reference, Wk23-26 doc creation status
- Identified and corrected Flask/FastAPI error in older continuity docs

---

## Week 23 Summary — Dispatch Services (10–12 hrs, 3 sessions)

| Session | Focus | Key Deliverables |
|---------|-------|-----------------|
| 23A | LaborRequestService (3–4 hrs) | Create/cancel/expire requests, cutoff enforcement (Rule 3), morning ordering (Rule 2), check mark determination (Rule 11), agreement type filtering (Rule 4) |
| 23B | JobBidService (3–4 hrs) | Place/withdraw/accept/reject bids, bidding window validation (Rule 8), suspension tracking (2 rejections in 12 months = 1-year suspension), infraction recording |
| 23C | DispatchService (3–4 hrs) | Core dispatch workflow, dispatch_from_queue (FIFO by APN, Book 1→2→3), dispatch_by_name (Rule 13 anti-collusion), terminate (quit/discharge = Rule 12 all-books rolloff + blackout, RIF, short call end = Rule 9 position restoration) |

**Business rules completed:** After Week 23, **all 14 business rules** have service-layer implementations.
**Test target:** ~540–560 total (+50–70 from ~490+)

---

## Week 24 Summary — Queue Management & Enforcement (10–12 hrs, 3 sessions)

| Session | Focus | Key Deliverables |
|---------|-------|-----------------|
| 24A | QueueService core (3–4 hrs) | Queue snapshots, multi-book queues, next-eligible selection (skips exempt/blackout/suspended, Book 1→2→3 priority), wait time estimation, queue depth analytics |
| 24B | EnforcementService (3–4 hrs) | Daily enforcement batch: re-sign deadline rolloffs (30-day), re-sign reminders (7-day warning), expired request/exemption/blackout/suspension cleanup, dry-run mode for admin preview |
| 24C | Analytics & integration tests (3–4 hrs) | Book utilization stats, dispatch rates, classification summaries, member queue status, 10+ end-to-end integration tests covering full lifecycle |

**New pitfall added:** Queue position is **derived** from APN via `ROW_NUMBER()` — NEVER stored as a field.
**Test target:** ~590–620 total (+50–60)

---

## Week 25 Summary — API Endpoints (10–12 hrs, 3 sessions)

| Session | Focus | Key Deliverables |
|---------|-------|-----------------|
| 25A | Book & Registration API (3–4 hrs) | `referral_book_router.py` + `book_registration_router.py` — CRUD, queue queries, re-sign, resign, eligibility checks |
| 25B | LaborRequest & Bid API (3–4 hrs) | `labor_request_router.py` + `job_bid_router.py` — Request CRUD, bid submission, bid window validation, request fulfillment |
| 25C | Dispatch & Admin API (3–4 hrs) | `dispatch_router.py` + `enforcement_router.py` + `queue_router.py` — Dispatch creation, termination, queue snapshots, enforcement triggers, analytics endpoints |

**Follows existing router patterns** from Weeks 1–19 (FastAPI APIRouter, Depends for auth, HTTPException in routers only).
**Test target:** ~660–700 total (+70–80)

---

## What's Next — Remaining Instruction Documents

| Week | Focus | Status | Priority |
|------|-------|--------|----------|
| 20 | Schema Reconciliation & Core Models | ✅ Instructions created (prior session) | — |
| 21 | Dispatch Models & Activity Tracking | ✅ Instructions created (prior session) | — |
| 22 | Registration Services & Business Rules | ✅ Instructions created (prior session) | — |
| 23 | Dispatch Services | ✅ Instructions created & delivered | — |
| 24 | Queue Management & Enforcement | ✅ Instructions created & delivered | — |
| 25 | API Endpoints | ✅ Instructions created, **needs delivery** | — |
| **26** | **Frontend — Books & Registration UI** | **❌ Not yet created** | **HIGH — Next to create** |
| 27 | Frontend — Dispatch Workflow UI | 🔜 Pending | MEDIUM |
| 28 | Frontend — Reports Navigation & Dashboard | 🔜 Pending | MEDIUM |
| 29–30 | Report Sprint 1: P0 Critical Reports (16 reports) | 🔜 Pending | LOWER |
| 30–31 | Report Sprint 2: P1 High Priority Reports (33 reports) | 🔜 Pending | LOWER |
| 32+ | Report Sprint 3: P2/P3 Reports (29 reports) + Integration | 🔜 Pending | LOWER |

### Week 26 Should Cover (Frontend — Books & Registration UI)

Following ADR-002 (Jinja2 + HTMX + Alpine.js) and ADR-010/ADR-011 (list/detail/form patterns):

- **Session 26A:** Referral landing page with book status overview + Book list page with registration counts per tier
- **Session 26B:** Book detail page with registrant list (queue view) + Registration workflow UI (add member, re-sign, resign)
- **Session 26C:** Queue visualization (position, wait time), member registration status across all books, sidebar navigation update (Referral & Dispatch section)

**Key frontend patterns to reference:**
- DaisyUI components: tables, badges, modals, steps, stats cards
- HTMX for partial updates: `hx-get`, `hx-post`, `hx-swap`, `hx-trigger`
- Alpine.js for client-side interactivity: modals, dropdowns, form validation
- Combined frontend service pattern (e.g., `DispatchFrontendService`) to assemble data for templates
- PWA considerations from Week 18 (offline support for dispatch window)
- Existing patterns: `staff_service.py` (Week 3), `dues_frontend_service.py` (Week 10) as references

---

## Established Conventions (Apply to All Instruction Docs)

### Document Structure Pattern

Every instruction doc follows this structure:
1. Header block (version, status, project version, phase, estimated hours)
2. Purpose statement (paste-into-new-chat context)
3. Project context (tech stack, metrics — condensed)
4. Working copy & workflow paths
5. Prerequisites checklist (verify prior weeks)
6. What already exists (services, models from prior weeks)
7. Week scope with per-session breakdown
8. Code snippets showing expected service/router structure
9. Test scenario tables with targets
10. Architecture reminders
11. Session checklist (before/after each session)
12. Week completion criteria
13. What comes after (next weeks table)
14. Related documents table
15. End-of-session documentation mandate
16. Known pitfalls (carry forward list — CORRECTED to show FastAPI, not Flask)
17. Version footer

### Service Layer Convention

```python
class SomeService:
    @staticmethod
    def method_name(...) -> ReturnType:
        """Docstring with business rules."""
        # Services own db.session commit/rollback
        # Services raise domain exceptions (ValueError, custom), NOT HTTP exceptions
        # Routers/blueprints handle HTTP status codes
```

### Router Convention (FastAPI)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.routers.dependencies.auth_cookie import get_current_user_cookie

router = APIRouter(prefix="/referral", tags=["referral"])

@router.get("/books")
async def list_books(db: Session = Depends(get_db),
                     current_user = Depends(get_current_user_cookie)):
    """List all referral books."""
    ...
```

### Test Target Progression

| After Week | Expected Total Tests |
|------------|---------------------|
| 19 (baseline) | ~470 |
| 22 (Phase 7 foundation) | ~490+ |
| 23 | ~540–560 |
| 24 | ~590–620 |
| 25 | ~660–700 |
| 26 | ~730–760 (estimated) |

### Header Block Template
```markdown
# Week NN Instructions — Phase 7: [Title]

> **Document Created:** February 4, 2026
> **Last Updated:** February 4, 2026
> **Version:** 1.0
> **Status:** Active — Ready for implementation (after Week NN-1 completes)
> **Project Version:** v0.9.5-alpha (Feature-Complete Weeks 1–19, Phase 7 Weeks 20–NN-1)
> **Phase:** 7 — Referral & Dispatch System
> **Estimated Hours:** X–Y hours across N sessions
```

---

## Working Copy Locations

- **Working copy (OneDrive):** `D:\OneDrive\Documents\Claude.ai\IP2A-Database-v2\`
- **Live project:** `C:\Users\Xerxes\Projects\IP2A-Database-v2\`
- **Workflow:** Claude outputs files → Xerxes manually copies to live project
- **Branch:** `develop` at v0.9.5-alpha (main needs merge from develop)

---

## Phase 7 Related Documents

| Document | Location |
|----------|----------|
| Week 20 Instructions | `docs/instructions/WEEK_20_INSTRUCTIONS.md` |
| Week 21 Instructions | `docs/instructions/WEEK_21_INSTRUCTIONS.md` |
| Week 22 Instructions | `docs/instructions/WEEK_22_INSTRUCTIONS.md` |
| Week 23 Instructions | `docs/instructions/WEEK_23_INSTRUCTIONS.md` |
| Week 24 Instructions | `docs/instructions/WEEK_24_INSTRUCTIONS.md` |
| Week 25 Instructions | `docs/instructions/WEEK_25_INSTRUCTIONS.md` |
| Phase 7 Continuity Doc | `docs/phase7/PHASE7_CONTINUITY_DOC.md` |
| Phase 7 Continuity Addendum | `docs/phase7/PHASE7_CONTINUITY_DOC_ADDENDUM.md` |
| Phase 7 Schema Decisions | `docs/phase7/PHASE7_SCHEMA_DECISIONS.md` |
| Implementation Plan v2 | `docs/phase7/PHASE7_IMPLEMENTATION_PLAN_v2.md` |
| Referral & Dispatch Plan | `docs/phase7/PHASE7_REFERRAL_DISPATCH_PLAN.md` |
| LaborPower Gap Analysis | `docs/phase7/LABORPOWER_GAP_ANALYSIS.md` |
| LaborPower Implementation Plan | `docs/phase7/LABORPOWER_IMPLEMENTATION_PLAN.md` |
| Referral Reports Inventory | `docs/phase7/LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` |
| Local 46 Referral Books | `docs/phase7/LOCAL46_REFERRAL_BOOKS.md` |
| ADR-015 (Referral Architecture) | `docs/decisions/ADR-015-referral-dispatch-architecture.md` |
| ADR README (15 ADRs) | `docs/decisions/README.md` |
| Backend Roadmap v3.1 | `docs/IP2A_BACKEND_ROADMAP.md` |
| Milestone Checklist | `docs/IP2A_MILESTONE_CHECKLIST.md` |
| Session Log (Wk20–22) | `docs/session-logs/2026-02-04-phase7-weeks20-22.md` |

---

## Known Pitfalls (Carry Forward — CORRECTED)

- ❌ Flask / flask run / Blueprints → ✅ **FastAPI / uvicorn / APIRouter**
- ❌ Grafana / Loki → ✅ **Sentry** (ADR-007)
- ❌ Missing DaisyUI references → ✅ Always mention DaisyUI with frontend stack
- ❌ `is_locked` → ✅ `locked_until` (datetime, not boolean)
- ❌ 7 contract codes → ✅ **8** (RESIDENTIAL is the 8th)
- ❌ 80–120 hrs Phase 7 → ✅ **100–150 hrs**
- ❌ Week 15 "missing" → ✅ Intentionally skipped (14→16)
- ❌ APN as INTEGER → ✅ **DECIMAL(10,2)** — preserves FIFO ordering
- ❌ LaborPower tier ordering → ✅ **INVERTED** in LaborPower — verify with dispatch staff
- ❌ Services raising HTTP exceptions → ✅ Services raise **domain exceptions** (ValueError, custom). Routers handle HTTP.
- ❌ 14 ADRs → ✅ **15 ADRs** (ADR-015 added February 4, 2026)
- ❌ Queue position as stored field → ✅ **Derived** from APN via `ROW_NUMBER()`. NEVER store position.
- ❌ Old continuity docs said "Flask" in pitfalls → ✅ **Those docs were wrong.** Project is FastAPI. Corrected in all Wk23+ instruction docs.

---

## End-of-Session Rule

> **MANDATORY:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

---

*Continuity Document — Phase 7 Instruction Document Creation (Session 2)*
*Created: February 4, 2026*
*Weeks 20–25 Instructions Complete, Week 26 Pending*
