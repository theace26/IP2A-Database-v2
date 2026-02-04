# Claude Code Instructions: Hub/Spoke File Operations & Document Deployment

**Created:** February 3, 2026
**Purpose:** Execute file system operations for the Hub/Spoke migration and deploy updated documentation
**Context:** UnionCore (IP2A-Database-v2) — IBEW Local 46
**Estimated Time:** 15-20 minutes
**Branch:** `develop`

---

## Pre-Flight

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
pytest -v --tb=short 2>&1 | tail -5  # Verify green, capture test count
```

> ⚠️ **CAPTURE THE TEST COUNT** from the pytest output. The Hub documents currently say "~490+ (verify with pytest)" because the actual post-Week 25 count has not been confirmed. Update all documents below with the real number.

---

## Phase 1: Create Historical Archive Directory

```bash
mkdir -p docs/historical
```

---

## Phase 2: Archive Old README Versions

The current `docs/README.md` is being replaced with an updated version that includes Hub/Spoke project structure documentation.

```bash
# Archive the current README with a descriptive name
cp docs/README.md docs/historical/docs_README_pre_hub_spoke_$(date +%Y%m%d).md

# Verify the archive exists
ls -la docs/historical/
```

> **Note:** The user may also have local copies of `docs_README_UPDATED.md`, `docs_README_UPDATED_v2.md`, and other variants from iterating across chat threads. If any of these exist in the repo root or docs/ directory, move them to `docs/historical/` as well:

```bash
# Only run these if the files exist — don't error if they don't
mv docs/docs_README_UPDATED.md docs/historical/ 2>/dev/null || true
mv docs/docs_README_UPDATED_v2.md docs/historical/ 2>/dev/null || true
mv docs_README_UPDATED.md docs/historical/ 2>/dev/null || true
mv docs_README_UPDATED_v2.md docs/historical/ 2>/dev/null || true
```

---

## Phase 3: Deploy Updated Documentation

The user will provide three updated files. Deploy them to the correct locations:

| Source File (provided by user) | Destination in Repo | What Changed |
|-------------------------------|---------------------|--------------|
| `hub_README_v1.md` | `docs/README.md` | Hub/Spoke section, updated status, sprint clarification |
| `IP2A_BACKEND_ROADMAP_v4.md` | `docs/IP2A_BACKEND_ROADMAP.md` | Hub/Spoke tags, Weeks 23-25, fixed version, sprint clarification |
| `IP2A_MILESTONE_CHECKLIST_v2.md` | `docs/IP2A_MILESTONE_CHECKLIST.md` | Hub/Spoke tags, Weeks 23-25, updated stats |

```bash
# Copy each file to its correct location
# (Adjust source paths based on where user places the files)
cp hub_README_v1.md docs/README.md
cp IP2A_BACKEND_ROADMAP_v4.md docs/IP2A_BACKEND_ROADMAP.md
cp IP2A_MILESTONE_CHECKLIST_v2.md docs/IP2A_MILESTONE_CHECKLIST.md
```

---

## Phase 4: Update CLAUDE.md with Hub/Spoke Awareness

Add the following section to `CLAUDE.md` **immediately after the TL;DR section** (after the first `---` separator following the TL;DR block, before the `## Current State` section).

### Content to Insert into CLAUDE.md

Insert this block between the TL;DR section and the `## Current State` section:

```markdown
---

## Development Model: Hub/Spoke

This project uses a **Hub/Spoke model** for planning and coordination via Claude AI projects (claude.ai). This does NOT affect the code architecture — it's about how development conversations are organized.

| Project | Scope | What Goes There |
|---------|-------|-----------------|
| **Hub** | Strategy, architecture, cross-cutting decisions, roadmap, docs | "How should we approach X?" |
| **Spoke 2: Operations** | Dispatch/Referral, Pre-Apprenticeship, SALTing, Benevolence | Phase 7 implementation, instruction docs |
| **Spoke 1: Core Platform** | Members, Dues, Employers, Member Portal | Create when needed |
| **Spoke 3: Infrastructure** | Dashboard/UI, Reports, Documents, Import/Export, Logging | Create when needed |

**What this means for you (Claude Code):**
- You operate directly on the codebase regardless of which Spoke produced the instruction document
- Instruction documents are created in Hub or Spoke projects and provided to you for execution
- If you encounter **cross-cutting concerns** (e.g., changes to `src/main.py`, shared test fixtures in `conftest.py`, or modifications to base templates), note them in your session summary so the user can create a handoff note for the Hub
- The Hub/Spoke model is for human/AI planning coordination, not code architecture. Do not create separate code directories for Spokes.

**Sprint Weeks ≠ Calendar Weeks:** Instruction document "weeks" (Week 20, Week 25, etc.) are sprint numbers, not calendar weeks. At 5-10 hours/week development pace, each sprint takes 1-2 calendar weeks to complete. Do not assume sprint numbers map to specific dates.
```

### Also Update the CLAUDE.md Header

Update the header block at the top of CLAUDE.md:

**Current:**
```
**Current Phase:** Phase 7 (Referral & Dispatch) IN PROGRESS — Weeks 20-25 Complete (Services + API)
```

**Change to:**
```
**Current Phase:** Phase 7 (Referral & Dispatch) IN PROGRESS — Weeks 20-25 Complete (Services + API) | Spoke 2
```

### Also Update the Version Footer

**Current:**
```
**Document Version:** 4.0
**Last Updated:** February 4, 2026
```

**Change to:**
```
**Document Version:** 5.0
**Last Updated:** [TODAY'S DATE]
**Previous Version:** 4.0 (February 4, 2026 — Phase 7 Weeks 20-25 detail added)
**Hub/Spoke Model:** Added February 2026
```

---

## Phase 5: Update Test Count (CRITICAL)

From the `pytest` output captured in Pre-Flight, update ALL of these locations with the actual test count:

1. **CLAUDE.md** — TL;DR section (`~490+ total tests` → actual number)
2. **CLAUDE.md** — Current State table (Backend tests, total)
3. **docs/IP2A_BACKEND_ROADMAP.md** — Executive Summary (`Total Tests` line)
4. **docs/IP2A_BACKEND_ROADMAP.md** — Phase 7 progress block
5. **docs/IP2A_MILESTONE_CHECKLIST.md** — Quick Stats section
6. **docs/README.md** — Current Status table (Total row)

Search for the marker text `⚠️ VERIFY` in all three new documents — every instance marks a number that needs the real pytest count.

```bash
grep -rn "VERIFY" docs/README.md docs/IP2A_BACKEND_ROADMAP.md docs/IP2A_MILESTONE_CHECKLIST.md
```

---

## Phase 6: Verification

```bash
# 1. Verify all files exist
ls -la docs/README.md docs/IP2A_BACKEND_ROADMAP.md docs/IP2A_MILESTONE_CHECKLIST.md CLAUDE.md

# 2. Verify historical archive
ls -la docs/historical/

# 3. Verify no broken internal links (spot check)
grep -c "Hub/Spoke" docs/README.md           # Should be > 0
grep -c "Hub/Spoke" docs/IP2A_BACKEND_ROADMAP.md  # Should be > 0
grep -c "Hub/Spoke" docs/IP2A_MILESTONE_CHECKLIST.md  # Should be > 0
grep -c "Hub/Spoke" CLAUDE.md                 # Should be > 0

# 4. Verify test count was updated (no remaining VERIFY markers)
grep -rn "VERIFY" docs/README.md docs/IP2A_BACKEND_ROADMAP.md docs/IP2A_MILESTONE_CHECKLIST.md CLAUDE.md
# Should return 0 results

# 5. All tests still pass
pytest -v --tb=short
```

---

## Phase 7: Commit

```bash
git add docs/README.md docs/IP2A_BACKEND_ROADMAP.md docs/IP2A_MILESTONE_CHECKLIST.md CLAUDE.md docs/historical/
git commit -m "docs: Hub/Spoke migration — updated Roadmap v4.0, Checklist v2.0, README, CLAUDE.md

- Added Hub/Spoke project structure sections to all documents
- Added Spoke ownership tags to all phases and weeks
- Updated Phase 7 state: Weeks 20-25 complete (7 services, 5 routers, ~51 endpoints)
- Added sprint vs calendar week clarification
- Archived pre-Hub/Spoke README to docs/historical/
- Fixed Roadmap version (v3.1 typo → v4.0)
- Reconciled version numbers across all documents
- Updated test counts to verified actuals
"
git push origin develop
```

---

## Post-Deployment: Spoke 2 State Update

After this commit, Spoke 2 (Operations) project instructions should be updated with the post-Week 25 state. The user should paste a handoff note into the Spoke 2 project with:

- Confirmed test count
- v0.9.6-alpha version
- Hub/Spoke model is now documented
- Weeks 23-25 are reflected in all project documents
- Next work for Spoke 2: Week 26 (Books & Registration UI)

---

*Claude Code Hub/Spoke FileOps Instructions — February 3, 2026*
