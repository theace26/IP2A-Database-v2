# IP2A-Database-v2 — Documentation Update Continuity Document

> **Purpose:** Copy/paste this into a new Claude.ai chat to continue the documentation update project.
> **Created:** February 3, 2026
> **Last Updated:** February 3, 2026
> **Project:** IP2A-Database-v2 / UnionCore (Union operations management platform for IBEW Local 46)
> **Session Focus:** Batch 5 — Standards, Guides, References, Runbooks & Instructions (FINAL BATCH)

---

## What We're Doing

Systematically updating ALL project documentation from outdated versions to reflect the current **v0.9.4-alpha FEATURE-COMPLETE** status. This is the **final batch** of the documentation update campaign. After this, the entire `docs/` tree will be current and consistent.

### Working Copy vs Live Project

- **Working copy (for Claude.ai):** `D:\OneDrive\Documents\Claude.ai\IP2A-Database-v2\`
- **Live project:** `C:\Users\Xerxes\Projects\IP2A-Database-v2\`
- Claude works on copies → outputs files → user manually copies to live project

### File Naming Convention

- **No prefix** = current live version
- **`_UPDATED` suffix** = intermediate iteration from earlier session
- **`outdated_-_` prefix** = older reference version for comparison

When multiple versions exist, compare ALL versions to determine which is most current, then produce a single consolidated output.

---

## Current Project State (The "Source of Truth")

- **Version:** v0.9.4-alpha — FEATURE-COMPLETE (Weeks 1-19)
- **Tests:** ~470 total (~200+ frontend, 165 backend, ~78 production, 25 Stripe)
- **API Endpoints:** ~150
- **ORM Models:** 26
- **ADRs:** 14
- **Deployment:** Railway (prod), Render (backup)
- **Payments:** Stripe live (Checkout Sessions + webhooks)
- **Mobile:** PWA with offline support and service worker
- **Analytics:** Chart.js dashboard with custom report builder
- **Phase 7 Next:** Referral & Dispatch system (~78 de-duplicated reports, ~91 raw)
- **Branch Strategy:** `develop` at v0.9.4-alpha, `main` needs merge from develop

### Tech Stack (verify guides/references match these)

| Layer | Technology |
|-------|-----------|
| Backend | Flask + SQLAlchemy ORM (26 models) |
| Frontend | Jinja2 + HTMX + Alpine.js |
| UI Framework | DaisyUI (on Tailwind CSS) |
| Database | PostgreSQL (Railway) |
| Payments | Stripe (Checkout Sessions + webhooks) |
| Auth | Flask-Login + session-based |
| Monitoring | Sentry (NOT Grafana/Loki — see ADR-007) |
| Logging | Structured logging (stdlib) |
| Security | Security headers, CSP, rate limiting |
| Reports | WeasyPrint (PDF), openpyxl (Excel), Chart.js (dashboard) |
| Mobile | PWA (service worker, offline support, app manifest) |
| Deployment | Railway (prod), Render (backup) |
| Testing | pytest + Playwright |

### Completed Weeks Summary

| Week | Focus | Tests | Version |
|------|-------|-------|---------|
| 1-9 | Core frontend (auth, dashboard, staff, training, members, ops, reports, docs) | ~125 | v0.7.0–v0.7.7 |
| 10 | Dues UI | 37 | v0.7.9 |
| 11 | Audit Infrastructure + Stripe | 19+25 | v0.8.0-alpha1 |
| 12 | Profile & Settings | — | v0.8.1-alpha |
| 13 | Entity Completion Audit | — | v0.8.2-alpha |
| 14 | Grant Compliance Reporting | ~20 | v0.9.0-alpha |
| 16 | Production Hardening (security headers, Sentry, structured logging, connection pooling) | 32 | v0.9.1-alpha |
| 17 | Post-Launch Ops (backup scripts, admin metrics, incident response runbook) | 13 | v0.9.2-alpha |
| 18 | Mobile PWA (service worker, offline support, app manifest) | 14 | v0.9.3-alpha |
| 19 | Analytics Dashboard (Chart.js, custom report builder) | 19 | v0.9.4-alpha |

---

## What Was Completed Before This Session

### ✅ Batch 1 — Core Project Files (3 files)
CHANGELOG.md, README.md, CONTRIBUTING.md

### ✅ Batch 2 — Architecture Docs (4 files)
SYSTEM_OVERVIEW.md, AUTH.md, FILE_STORAGE.md, SCALABILITY.md

### ✅ Batch 3 — ADRs (15 files)
ADR README + ADR-001 through ADR-014

### ✅ Batch 4a — Phase 7 Planning Part 1 (4 files)
GAP_ANALYSIS.md, IMPLEMENTATION_PLAN.md, REFERRAL_BOOKS.md, CONTINUITY_ADDENDUM.md

### ✅ Batch 4b — Phase 7 Planning Part 2 (4+ files)
REFERRAL_DISPATCH_PLAN.md, IMPL_PLAN_v2.md, REPORTS_INVENTORY.md, AUDIT_ARCHITECTURE.md
Plus NEW: PHASE7_CONTINUITY_DOC.md

### ✅ Roadmap v3.0 (1 file)
IP2A_BACKEND_ROADMAP.md — Phase 7 expanded with §7.1–§7.9 LaborPower subsections

### ✅ Milestone Checklist (1 file)
IP2A_MILESTONE_CHECKLIST.md — Phase 7 expanded from 17 to ~340 lines with sub-phases 7a–7g

### ✅ docs_README.md (1 file)
Updated to reference all new documents, Phase 7 navigation section, documentation update status tracker

---

## What Needs To Be Done This Session

### ⬜ Batch 5 — Standards, Guides, References, Runbooks & Instructions

This batch covers the remaining documentation directories. **The exact file list is unknown until the user uploads them.** The first step is always **discovery** — inventory what was uploaded, then plan the update order.

#### Expected Directories and File Categories

| Directory | Expected Content | Key Update Focus |
|-----------|-----------------|-----------------|
| `docs/standards/` | Coding standards, naming conventions, commit message format, testing standards | Verify they match actual codebase patterns (DaisyUI, HTMX, Alpine.js conventions) |
| `docs/guides/` | Developer onboarding, setup guides, deployment guides, feature implementation guides | Update for current stack (Stripe, PWA, analytics, Sentry), verify setup steps work |
| `docs/reference/` | API reference, model reference, enum reference, configuration reference | Verify against actual ~150 endpoints, 26 ORM models, current config structure |
| `docs/runbooks/` | Operational runbooks (deployment, incident response, backup/restore, monitoring) | Update with Week 17 scripts (backup, admin metrics, incident response runbook) |
| `docs/instructions/` | How-to instructions, workflow instructions, Claude Code session instructions | Add mandatory end-of-session documentation instruction prominently |

#### Splitting Strategy

If the total file count exceeds what can be processed in one session (roughly 8-10 files), split into:

- **Batch 5a:** `standards/` + `guides/` (developer-facing docs — likely need the most updating since they describe how-to workflows)
- **Batch 5b:** `reference/` + `runbooks/` + `instructions/` (operational docs — may need less narrative updating but more factual verification)

If files are small and few, do them all in one session.

#### Per-Category Update Expectations

**Standards Documents:**
- Add header blocks, session rules, version footers
- Verify coding style guides mention DaisyUI component patterns (ADR-005)
- Verify testing standards reflect current pytest + Playwright setup
- Check if enum conventions are documented (string enums with UPPERCASE values — established pattern)
- Verify commit message conventions match CHANGELOG entries

**Guide Documents:**
- Add header blocks, session rules, version footers
- Update setup/installation guides for current dependencies
- Verify deployment guide reflects Railway (primary) and Render (backup) — NOT Heroku or other platforms
- Add/update guide content for features shipped in Weeks 14-19:
  - Week 14: Grant Compliance Reporting (WeasyPrint PDF generation)
  - Week 16: Production Hardening (security headers, Sentry, structured logging, connection pooling)
  - Week 17: Post-Launch Ops (backup scripts, admin metrics, incident response)
  - Week 18: Mobile PWA (service worker, offline support)
  - Week 19: Analytics Dashboard (Chart.js, custom report builder)
- If a Stripe integration guide exists, verify it covers Checkout Sessions + webhooks (NOT legacy Charges API)

**Reference Documents:**
- Add header blocks, session rules, version footers
- Verify API endpoint lists match actual ~150 endpoints
- Verify model references match 26 ORM models
- Check that `locked_until` datetime pattern is correct wherever account lockout is mentioned (NOT `is_locked` boolean — see convention #7)
- If enum reference exists, verify all enums are current

**Runbook Documents:**
- Add header blocks, session rules, version footers
- Verify deployment runbook matches Railway deployment process
- Update incident response runbook with Week 17 additions (structured logging, Sentry integration)
- Verify backup/restore procedures match Week 17 backup scripts
- Add admin metrics dashboard references from Week 17
- If monitoring runbook references Grafana/Loki, redirect to Sentry (ADR-007)

**Instruction Documents:**
- Add header blocks, session rules, version footers
- **Mandatory:** Add the end-of-session documentation instruction prominently:
  > "Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary."
- If Claude Code session instructions exist, verify they reference the Phase 7 Continuity Doc as the session primer
- Verify any "getting started" instructions work with current project structure

---

## Known Pitfalls (From Earlier Batches — Watch For These)

These issues were found in Batches 1-4 and may recur in Batch 5 files:

| Issue | Where Found | What To Look For |
|-------|-------------|-----------------|
| Grafana/Loki references | ADR-007, possibly runbooks/guides | Should reference Sentry instead |
| Missing DaisyUI | ADR-005, possibly standards/guides | DaisyUI is the primary component library — should be mentioned |
| `is_locked` boolean | Various auth references | Correct pattern is `locked_until` datetime |
| "ADR-008" for audit | ADR-012 mislabel | Any reference to "ADR-008 Audit" should say ADR-012 |
| 7 contract codes | Pre-Batch 2 docs | Correct count is 8 (RESIDENTIAL was discovered in Batch 2 analysis) |
| 80-120 hour estimate | Older Phase 7 refs | Correct estimate is 100-150 hours |
| "Use LaborPower" | Backlog items | Correct stance is "building replacement system" |
| Report count ambiguity | Various | Always specify: 78 de-duplicated (91 raw) |
| Week 15 gap | Various | Week 15 was intentionally skipped — weeks go 14→16 |

---

## Established Conventions (Maintain These)

1. **Header blocks** with Document Created, Last Updated, Version, Status
2. **Implementation status tables** with ✅/🔜/❌ markers
3. **Cross-reference tables** linking related documents
4. **Mandatory end-of-session documentation instruction** in all docs
5. **Version footers** with previous version notes
6. **Baseline sections** showing existing v0.9.4-alpha capabilities
7. **Architecture integration notes** for Phase 7 features
8. **ADR cross-references** where decisions are related
9. **Consistent status markers** (✅ complete, 🔜 planned, ❌ rejected)
10. **ADR numbering correction** — ADR-012 was mislabeled as "ADR-008"; fixed with correction notice
11. **"Related Documents" tables** in Phase 7 docs to cross-link planning documents
12. **Member ≠ Student reminder** where dispatch qualifications could be confused with JATC training
13. **Seed data integration notes** where new tables interact with registry-based seed ordering
14. **Schedule overlap notes** where report sprints overlap with Implementation Plan phases

---

## Documentation Update Project — Overall Status

| Batch | Scope | Files | Status |
|-------|-------|-------|--------|
| Batch 1 | Core project files (CHANGELOG, README, CONTRIBUTING) | 3 | ✅ Complete |
| Batch 2 | Architecture docs (SYSTEM_OVERVIEW, AUTH, FILE_STORAGE, SCALABILITY) | 4 | ✅ Complete |
| Batch 3 | ADRs (README + ADR-001 through ADR-014) | 15 | ✅ Complete |
| Batch 4a | Phase 7 planning (GAP_ANALYSIS, IMPLEMENTATION_PLAN, REFERRAL_BOOKS, CONTINUITY_ADDENDUM) | 4 | ✅ Complete |
| Batch 4b | Phase 7 planning (REFERRAL_DISPATCH_PLAN, IMPL_PLAN_v2, REPORTS_INVENTORY, AUDIT_ARCHITECTURE) | 4 | ✅ Complete |
| Roadmap | IP2A_BACKEND_ROADMAP.md → v3.0 | 1 | ✅ Complete |
| Checklist | IP2A_MILESTONE_CHECKLIST.md | 1 | ✅ Complete |
| README | docs_README.md | 1 | ✅ Complete |
| **Batch 5** | **Standards, Guides, References, Runbooks, Instructions** | **TBD** | **⬜ THIS SESSION** |

### After Batch 5 — Project Wrap-Up

Once Batch 5 is complete, the documentation update project is **DONE**. Final steps:

1. **Final continuity doc** — Generate a brief completion summary with:
   - Total files updated across all batches
   - All issues found and fixed
   - Final convention list
   - Recommendation on documentation maintenance going forward (e.g., "update docs at end of every session" — the session rule should handle this)

2. **Update the Roadmap** — Mark the "Documentation Update Project Status" section as complete in IP2A_BACKEND_ROADMAP.md

3. **Update the Milestone Checklist** — Mark documentation update as complete

4. **Transition to Phase 7 implementation** — All planning docs are current; the Phase 7 Continuity Doc (`docs/phase7/PHASE7_CONTINUITY_DOC.md`) is the session primer for implementation work

---

## Instructions for This Session

### Step 1: Discovery

Upload everything from these directories:
- `docs/standards/*.md`
- `docs/guides/*.md`
- `docs/reference/*.md`
- `docs/runbooks/*.md`
- `docs/instructions/*.md`

If the total is too large, split by uploading `standards/` + `guides/` first (Batch 5a), then `reference/` + `runbooks/` + `instructions/` (Batch 5b).

### Step 2: Inventory

Before making any changes, list every uploaded file with:
- Current filename
- Apparent purpose
- Approximate version state (outdated/current/unknown)
- Priority for updating (High/Medium/Low based on how stale it appears)

### Step 3: Systematic Update

For each file, apply the standard update process:

> 1. Review the file against the current project state (v0.9.4-alpha, feature-complete Weeks 1-19, Railway deployed, ~470 tests, Phase 7 next)
> 2. Update content to reflect current reality
> 3. Add the mandatory end-of-session documentation instruction where appropriate:
>    `"Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan /docs/* and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary."`
> 4. Add header block, version footer, and cross-references per established conventions
> 5. Check against the "Known Pitfalls" table above
> 6. List all changed files as `/dir/file — description of change` so the user can update the live directory

### Step 4: Summary

After all files are processed, provide:
- Total files updated in this batch
- New issues found (if any)
- Files that may need Phase 7-specific updates later (once implementation starts)
- Confirmation that the documentation update project is complete

### Output Checklist (Per File)

Before finalizing each file, verify:
- [ ] Header block (Created, Updated, Version, Status)
- [ ] Content reflects v0.9.4-alpha feature-complete state
- [ ] No stale technology references (Grafana→Sentry, missing DaisyUI, etc.)
- [ ] End-of-session documentation instruction added
- [ ] Version footer with previous version note
- [ ] Cross-references to related docs where appropriate

---

*Generated: February 3, 2026 (for Batch 5 — final documentation update batch)*