# IP2A-Database-v2 — Documentation Update Continuity Document

> **Purpose:** Copy/paste this into a new Claude.ai chat to continue the documentation update project.
> **Created:** February 3, 2026
> **Last Updated:** February 3, 2026
> **Project:** IP2A-Database-v2 / UnionCore (Union operations management platform for IBEW Local 46)
> **Session Focus:** CLAUDE.md Update (Project Context Document)

---

## What We're Doing

Systematically updating ALL project documentation from outdated versions to reflect the current **v0.9.4-alpha FEATURE-COMPLETE** status. This session focuses on **CLAUDE.md** — the project context document that serves as the primary reference for both Claude Code and Claude.ai development sessions.

### Why This File Is Critical

CLAUDE.md (1,824 lines) is the most detailed per-week record of the project's development history. It serves double duty: (1) project context for Claude Code sessions, and (2) a comprehensive historical record of every implementation week. While CONTINUITY.md is the "paste to start a session" primer, CLAUDE.md is the "deep reference" for understanding what was built, when, how, and where.

### Working Copy vs Live Project

- **Working copy (for Claude.ai):** `D:\OneDrive\Documents\Claude.ai\IP2A-Database-v2\`
- **Live project:** `C:\Users\Xerxes\Projects\IP2A-Database-v2\`
- Claude works on copies → outputs files → user manually copies to live project

### File Naming Convention

- **No prefix** = current live version (e.g., `CLAUDE.md`)
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
- **Monitoring:** Sentry (NOT Grafana/Loki — see ADR-007)
- **Phase 7 Next:** Referral & Dispatch system (~78 de-duplicated reports, ~91 raw)
- **Branch Strategy:** `develop` at v0.9.4-alpha, `main` needs merge from develop

### Tech Stack (Authoritative — verify CLAUDE.md matches)

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy ORM (26 models) |
| Frontend | Jinja2 + HTMX + Alpine.js |
| UI Framework | DaisyUI (on Tailwind CSS) |
| Database | PostgreSQL 16 (Railway) |
| Payments | Stripe (Checkout Sessions + webhooks) |
| Auth | JWT + bcrypt + HTTP-only cookies + role-based access |
| Monitoring | Sentry (NOT Grafana/Loki — see ADR-007) |
| Logging | Structured JSON logging (stdlib) |
| Security | Security headers, CSP, rate limiting |
| Reports | WeasyPrint (PDF), openpyxl (Excel), Chart.js (dashboard) |
| Mobile | PWA (service worker, offline support, app manifest) |
| Deployment | Railway (prod), Render (backup) |
| Testing | pytest + httpx |
| Code Quality | Ruff, pre-commit hooks |
| Environment | Docker + Devcontainer |

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

### ✅ CONTINUITY.md (1 file)
Updated from v0.9.0-alpha to v0.9.4-alpha with Weeks 16-19 and Phase 7 context

---

## What Needs To Be Done This Session

### ⬜ Update CLAUDE.md

The user will upload the **current version** of CLAUDE.md. It is 1,824 lines and partially outdated — the top header is current (v0.9.4-alpha) but internal sections have inconsistencies and the bottom is stuck at v0.9.0-alpha.

### Audit of Issues Found in Current CLAUDE.md

The following issues were identified by comparing the current CLAUDE.md against the v0.9.4-alpha source of truth:

#### A. Inconsistent Version References

| Location | Current (WRONG) | Correct |
|----------|-----------------|---------|
| Line ~1653 (near "Version:" at bottom) | `v0.9.0-alpha` | `v0.9.4-alpha` |
| Line ~1655 | "Sessions Complete Today: Week 13 + Week 14" | Remove or update — misleading in a living document |
| Post-Week 10 section (line ~304) | "Next: Deployment Prep (Railway/Render)" | Already done — Railway deployed |

#### B. Phase 7 Section — Missing New Documents

The Phase 7 section at the bottom (lines ~1797-1824) lists 6 planning documents but is missing the following documents created during the documentation update project:

| Missing Document | Location |
|-----------------|----------|
| Schema Guidance Vol. 1 | `docs/phase7/LABORPOWER_DATA_ANALYSIS_SCHEMA_GUIDANCE.md` |
| Schema Guidance Vol. 2 | `docs/phase7/LABORPOWER_DATA_ANALYSIS_SCHEMA_GUIDANCE_VOL2.md` |
| Consolidated Continuity Document | `docs/phase7/UNIONCORE_CONTINUITY_DOCUMENT_CONSOLIDATED.md` |
| Phase 7 Continuity Doc Addendum | `docs/phase7/PHASE7_CONTINUITY_DOC_ADDENDUM.md` |
| Audit Architecture | `docs/architecture/AUDIT_ARCHITECTURE.md` |

The Phase 7 section should also include:
- LaborPower data analysis summary (24 files, 8 critical findings, 9 schema corrections)
- Known scope numbers (12 tables, 14 rules, 78 reports, 11 books, ~843 employers)
- Sub-phase breakdown (7a–7g, 100-150 hours)
- Current blockers (3 Priority 1 data gaps)
- Critical schema reminders (APN=DECIMAL, duplicate APNs, RESIDENTIAL 8th contract, Member≠Student, etc.)

#### C. Project Structure Tree — Missing Entries

The project structure tree (lines ~112-206) needs these additions:

```
docs/phase7/
    ├── LABORPOWER_DATA_ANALYSIS_SCHEMA_GUIDANCE.md      # NEW - Vol. 1
    ├── LABORPOWER_DATA_ANALYSIS_SCHEMA_GUIDANCE_VOL2.md # NEW - Vol. 2
    ├── UNIONCORE_CONTINUITY_DOCUMENT_CONSOLIDATED.md    # NEW - Master reference
    ├── PHASE7_CONTINUITY_DOC_ADDENDUM.md                # NEW - Addendum
    └── (existing files already listed)

docs/architecture/
    └── AUDIT_ARCHITECTURE.md                            # NEW - Audit architecture

scripts/                                                 # NEW directory
    ├── backup_database.sh                               # Week 17
    ├── verify_backup.sh                                 # Week 17
    ├── archive_audit_logs.sh                            # Week 17
    ├── cleanup_sessions.sh                              # Week 17
    └── crontab.example                                  # Week 17
```

#### D. "Current Phase" in TL;DR

The TL;DR section (line ~6) says:
> "Current Phase: FEATURE-COMPLETE (Weeks 1-19) — Phase 7 (Referral & Dispatch) Next"

This is **correct** but should be verified that the rest of the document is consistent with this framing.

#### E. ADR Count Discrepancy in Embedded Content

The Consolidated Continuity Document was embedded/excerpted in some sections. Line ~58 in that embedded section says "8 Architecture Decision Records (ADR-001 through ADR-008)" — this should be **14 ADRs (ADR-001 through ADR-014)**.

#### F. Tech Stack Discrepancy in Embedded Content

If any embedded section references "Grafana + Loki + Promtail for observability," this must be corrected to **Sentry** (ADR-007). The main CLAUDE.md body correctly references Sentry (line ~1672) but any older embedded or quoted sections may not.

#### G. "Frontend (Not Started)" in Embedded Content

If the CLAUDE.md contains any embedded/quoted section from the Consolidated Continuity Document that says "Frontend (Not Started — Phase 6)," this must be corrected. Frontend is **COMPLETE** through Week 19.

#### H. No Version Footer

CLAUDE.md has no version footer per established convention. One should be added.

#### I. No Documentation Update Project Status Section

Unlike docs_README.md (which now has the batch tracker), CLAUDE.md has no reference to the documentation update campaign. A brief pointer should be added.

---

### Specific Updates Required

**1. Fix Version References**
Update the bottom "Version:" line from v0.9.0-alpha to v0.9.4-alpha. Remove or reword "Sessions Complete Today: Week 13 + Week 14" since it's misleading in a document that has been updated through Week 19.

**2. Expand Phase 7 Section**
Add all missing documents to the Phase 7 key documents table. Add LaborPower data analysis summary. Add sub-phase breakdown. Add critical schema reminders. Add current blockers. This section should match what was added to docs_README.md at navigation level — not duplicate the Roadmap.

**3. Update Project Structure Tree**
Add missing entries for `docs/phase7/` new files, `docs/architecture/AUDIT_ARCHITECTURE.md`, and `scripts/` directory.

**4. Fix Embedded Content Discrepancies**
Search for and correct any instances of:
- "8 Architecture Decision Records" → "14 ADRs"
- "Grafana + Loki + Promtail" → "Sentry + Structured JSON Logging"
- "Frontend (Not Started)" → "Frontend COMPLETE (Weeks 1-19)"
- Any other content that contradicts the v0.9.4-alpha state

**5. Update Post-Week 10 "Next" Reference**
Line ~304 says "Next: Deployment Prep (Railway/Render)" — this should reflect that Railway deployment is already live. Change to reference Phase 7 as next.

**6. Add Version Footer**
Per established convention:
```
Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (February 2, 2026 — v0.9.4-alpha header but v0.9.0-alpha bottom, missing Phase 7 docs)
```

**7. Add End-of-Session Documentation Instruction**
Verify existing instruction is present and matches standard wording. The current file has an end-of-session section — verify its completeness.

**8. Add Documentation Update Project Reference**
Add a brief note (similar to what's in docs_README.md) pointing to the documentation update project status tracker so readers know the doc update campaign status.

**9. Review All Per-Week Sections for Accuracy**
The per-week sections (Weeks 1-19) are the historical record. Verify that:
- All weeks are listed and none are missing
- Version numbers are correct per week
- Test counts per week are accurate
- "Files Created" and "Files Modified" lists are complete
- No "Next:" references point to already-completed work (except as historical record)

**10. Consolidate Inconsistent Date References**
The document says "Last Updated: February 2, 2026" at the top. If changes are made, update to February 3, 2026. Verify all date references within per-week sections are historically accurate (don't change historical dates — those record when the work was actually done).

---

### What NOT To Do

- **Do NOT remove per-week historical sections** — these are the authoritative record of what was built each week. They should be preserved even if some are verbose.
- **Do NOT consolidate weeks into summaries** — the per-week detail is intentional and serves as a reference when debugging or extending features built in specific weeks.
- **Do NOT change historical dates** — if a section says "January 30, 2026" for Week 10, that's when it was done. Don't change it.
- **Do NOT remove the "Files Created" / "Files Modified" lists** — these are essential for Claude Code to know where to find things.
- **Do NOT duplicate the Roadmap's §7.1–§7.9 subsections** — the CLAUDE.md Phase 7 section should be navigation-level, pointing to docs/phase7/ for detail.
- **Do NOT restructure the document** — maintain the existing section order. Adding new sections is fine; rearranging existing ones risks breaking the historical narrative.

### Key Principle

> CLAUDE.md serves as both a **session primer** and a **historical record**. The top sections (TL;DR, Current State, Tech Stack, Project Structure) provide context for new sessions. The per-week sections provide detailed history for debugging and extending specific features. The Phase 7 section provides forward-looking planning context. All three purposes must be served by a single coherent document.

---

## LaborPower Data Analysis Summary (Quick Reference)

Included here so the CLAUDE.md update can reference accurate numbers.

### Registration Lists — 8 Books, 4,033 Total Records

| Book Name | Total | Tier Pattern |
|-----------|-------|-------------|
| WIRE SEATTLE | 1,186 | Normal |
| WIRE BREMERTON | 1,115 | Normal |
| WIRE PT ANGELES | 1,100 | Normal |
| TRADESHOW | 315 | Normal (94.6% Book 1) |
| TECHNICIAN | 260 | INVERTED (B3 > B1) |
| STOCKMAN | 54 | INVERTED (B3 = 8.6× B1) |
| TERO APPR WIRE | 2 | Single tier |
| UTILITY WORKER | 1 | Single tier |

### Employer Lists — 8 Contract Codes, ~843 Unique Employers

WIREPERSON (689), SOUND & COMM (300), RESIDENTIAL (259 — new, missing from prior docs), STOCKPERSON (180), LT FXT MAINT (92), GROUP MARINE (21), GROUP TV & APPL (2), MARKET RECOVERY (1)

### 8 Critical Schema Findings

1. APN = DECIMAL(10,2) not INTEGER
2. Duplicate APNs — need composite unique key
3. RESIDENTIAL = 8th contract code (259 employers)
4. Book Name ≠ Contract Code
5. TERO APPR WIRE = compound book
6. Cross-regional registration (87% on all 3 Wire books)
7. APN 45880.41 on FOUR books — validates many-to-many
8. Inverted tier distributions — STOCKMAN B3 = 8.6× B1

### Implementation Sub-Phases (7a–7g, 100-150 hrs)

| Sub-Phase | Focus | Hours | Blocked By |
|-----------|-------|-------|------------|
| 7a | Data Collection (3 Priority 1 exports) | 3-5 | LaborPower access |
| 7b | Schema Finalization (DDL + Alembic + seed) | 10-15 | 7a |
| 7c | Core Services + API (14 rules, CRUD, dispatch) | 25-35 | 7b |
| 7d | Import Tooling (CSV pipeline) | 15-20 | 7b |
| 7e | Frontend UI (books, dispatch board, web bidding) | 20-30 | 7c |
| 7f | Reports P0+P1 (49 reports) | 20-30 | 7c |
| 7g | Reports P2+P3 (29 reports) | 10-15 | 7f |

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
11. **"Related Documents" tables** in Phase 7 docs
12. **Member ≠ Student reminder** where dispatch qualifications could be confused with JATC training
13. **Seed data integration notes** where new tables interact with registry-based seed ordering
14. **Schedule overlap notes** where report sprints overlap with Implementation Plan phases

### Known Pitfalls (From Earlier Batches — Watch For These)

| Issue | What To Look For |
|-------|-----------------|
| Grafana/Loki references | Should reference Sentry instead (ADR-007) |
| Missing DaisyUI | DaisyUI is the primary component library (ADR-005) |
| `is_locked` boolean | Correct pattern is `locked_until` datetime |
| "ADR-008" for audit | If referencing audit ADR number, it's ADR-012 (was mislabeled) |
| 7 contract codes | Correct count is 8 (RESIDENTIAL discovered in Batch 2) |
| 80-120 hour estimate | Correct Phase 7 estimate is 100-150 hours |
| "Use LaborPower" | Correct stance is "building replacement system" |
| Report count ambiguity | Always specify: 78 de-duplicated (91 raw) |
| Week 15 gap | Week 15 was intentionally skipped — weeks go 14→16 |

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
| Batch 5 | Standards, Guides, References, Runbooks, Instructions | TBD | ⬜ Pending |
| CONTINUITY.md | Claude Code session primer | 1 | ✅ Complete |
| **CLAUDE.md** | **Project context document** | **1** | **⬜ THIS SESSION** |

---

## Instructions for This Session

Upload the **current version** of `CLAUDE.md`. Then:

1. Review the file against the "Audit of Issues" section above — every listed issue must be addressed
2. Apply all 10 specific updates listed in "What Needs To Be Done This Session"
3. Maintain all 14 established conventions
4. Check against the "Known Pitfalls" table
5. Do NOT remove per-week historical sections or restructure the document
6. Do NOT duplicate Roadmap §7.1–§7.9 or Checklist task tables — point to docs/phase7/
7. Produce a single updated output file
8. Provide a summary of all changes made (additions, modifications, line count delta)

### Output Checklist

Before finalizing, verify the updated CLAUDE.md has:
- [ ] Header block — Last Updated date current, version v0.9.4-alpha
- [ ] TL;DR section accurate (version, test count, status, next phase)
- [ ] Tech Stack table matches authoritative list (Sentry NOT Grafana, DaisyUI present)
- [ ] Project Structure tree includes all new Phase 7 docs and scripts/ directory
- [ ] All per-week sections preserved and historically accurate
- [ ] Bottom "Version:" line updated to v0.9.4-alpha
- [ ] "Sessions Complete Today" line removed or reworded
- [ ] Phase 7 section expanded with all planning docs, schema findings, sub-phases, blockers
- [ ] No embedded content contradicts v0.9.4-alpha state (ADR count, frontend status, observability stack)
- [ ] Post-Week 10 "Next:" reference updated
- [ ] End-of-session documentation instruction present and correct
- [ ] Version footer added with previous version note
- [ ] Documentation update project reference added
- [ ] No Grafana/Loki references anywhere in the document
- [ ] No "8 ADRs" anywhere — should be "14 ADRs"
- [ ] No "Frontend (Not Started)" anywhere — should be "Frontend COMPLETE"

---

*Generated: February 3, 2026 (for CLAUDE.md update session)*
