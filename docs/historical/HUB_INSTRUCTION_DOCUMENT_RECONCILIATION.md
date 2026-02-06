# Hub Claude Code Instructions: Document Reconciliation

**Source:** Hub
**Executor:** Claude Code (direct execution)
**Date:** February 5, 2026
**Priority:** MEDIUM — Execute AFTER Week 35 Stripe Removal & Bug Squash completes
**Estimated Effort:** 1-2 hours
**Prerequisite:** Week 35 bug squash is complete and final test numbers are known

---

## Purpose

Project documentation has drifted. Multiple documents report different test counts, ADR counts, version numbers, and phase statuses. This instruction reconciles ALL project documentation to reflect the true current state of the codebase.

**Why this matters:** CLAUDE.md is the single source of truth. When Claude Code or Claude AI sessions start, they read CLAUDE.md first. If it's wrong, every session starts with bad assumptions. This has already caused issues (Bug #026, #027, #028 — all schema drift that went undetected partly because docs didn't match reality).

---

## Pre-Flight: Gather Ground Truth

Before editing ANY document, gather the actual current state from the codebase. Do NOT trust any existing document — verify everything from source.

### Step 1: Test Metrics

```bash
# Run full test suite and capture
pytest -v --tb=short 2>&1 | tee /tmp/reconciliation_test_output.txt

# Extract counts
echo "=== TEST GROUND TRUTH ==="
echo "Total: $(grep -c '::' /tmp/reconciliation_test_output.txt)"
echo "Passed: $(grep -c 'PASSED' /tmp/reconciliation_test_output.txt)"
echo "Failed: $(grep -c 'FAILED' /tmp/reconciliation_test_output.txt)"
echo "Errors: $(grep -c 'ERROR' /tmp/reconciliation_test_output.txt)"
echo "Skipped: $(grep -c 'SKIPPED' /tmp/reconciliation_test_output.txt)"

# Calculate pass rate
# Pass rate = PASSED / (Total - Skipped) * 100
```

Record these numbers. They are the ONLY numbers that go into documents.

### Step 2: Endpoint Count

```bash
# Count API endpoints (grep for route decorators)
echo "=== ENDPOINT COUNT ==="
grep -rn "@router\.\(get\|post\|put\|patch\|delete\)" src/routers/ | wc -l

# Alternative: check FastAPI auto-generated routes
# Start server briefly and hit /docs or /openapi.json
```

### Step 3: Model Count

```bash
# Count SQLAlchemy models (classes that inherit from Base)
echo "=== MODEL COUNT ==="
grep -rn "class.*Base)" src/models/ | grep -v "test" | grep -v "__pycache__" | wc -l

# List them
grep -rn "class.*Base)" src/models/ | grep -v "test" | grep -v "__pycache__"
```

### Step 4: ADR Count

```bash
# Count ADR files
echo "=== ADR COUNT ==="
ls docs/decisions/ADR-*.md 2>/dev/null | wc -l
ls docs/decisions/ADR-*.md 2>/dev/null
```

### Step 5: Version Check

```bash
# Check if version is defined anywhere in code
echo "=== VERSION ==="
grep -rn "version" src/main.py | head -5
grep -rn "__version__" src/ | head -5
cat pyproject.toml 2>/dev/null | grep version | head -3
```

### Step 6: Stripe Removal Verification

```bash
# Confirm Stripe is gone (should be zero results after Week 35)
echo "=== STRIPE CHECK ==="
grep -ri "stripe" src/ | wc -l
grep -ri "stripe" requirements.txt 2>/dev/null | wc -l
```

### Step 7: Skipped Test Inventory

```bash
# List every skipped test with its reason
echo "=== SKIPPED TESTS ==="
grep -rn "pytest.mark.skip" src/tests/ 
grep -rn "skipIf\|skipUnless" src/tests/
```

---

## Document Update Sequence

Update documents in this exact order. Each document may reference numbers from earlier documents, so order matters.

### Document 1: CLAUDE.md (Source of Truth)

**Location:** `CLAUDE.md` (project root)

**Fields to reconcile (update ALL of these):**

1. **TL;DR section → Status line:**
   - Update test count: `XXX total tests (XXX passing, XXX skipped [reasons], ~XX% pass rate, Week XX as of [date])`
   - Update endpoint count: `~XXX API endpoints`
   - Update model count: `XX models`
   - Update ADR count: `XX ADRs`
   - Remove ALL Stripe references (e.g., "27 Stripe" in skip counts, "Stripe Payments LIVE", "migrating to Square")
   - Replace with: "Square payment integration planned (ADR-018, Phase 8)"

2. **TL;DR → Stack line:**
   - Remove `Stripe (migrating to Square)` from the stack list

3. **TL;DR → Current line:**
   - Update week number and report count

4. **Current State → Backend table:**
   - Update Phase 7 row with current test counts (passing vs errors)
   - Update Total row

5. **Current State → Frontend Tests table:**
   - Remove any Stripe test row
   - Verify all other rows match actual test file contents

6. **Tech Stack table:**
   - Remove any Stripe row
   - Add note about Square being Phase 8

7. **Phase 7 section:**
   - Update "Weeks 20-XX complete" to reflect current week
   - Update report count (e.g., "14 of 78 reports" or whatever is current)

8. **Document Version footer:**
   - Bump version number (5.0 → 5.1 or 6.0)
   - Update date

**Known stale data in current CLAUDE.md v5.0:**
- Line 20: Says "648 total tests (541+ passing..." — verify against ground truth
- Line 20: Says "35 skipped [27 Stripe + 5 setup + 3 S3]" — Stripe count should be 0 after removal
- Line 16: Says "Stripe Payments LIVE (migrating to Square per ADR-018)" — remove Stripe reference
- Line 18: Stack includes "Stripe (migrating to Square)" — remove
- Line 59: Phase 7 backend shows "20 (7 passing, 13 errors)" — likely stale from pre-Week 28

### Document 2: CHANGELOG.md

**Location:** `CHANGELOG.md` (project root)

Add a new entry at the top under `[Unreleased]`:

```markdown
### Changed (Week 35 — [DATE])
- **Stripe Removal** — Removed all Stripe code, tests, configuration per ADR-018
  * Removed: [X] Stripe test files, [X] source files, Stripe SDK from requirements
  * Retained: All dues tracking models, services, routes, and tests (payment-gateway agnostic)
  * ADR-018 updated: Status → "In Progress — Stripe Removed, Square Phase A Pending"

### Fixed (Week 35 — [DATE])
- **Bug Squash Sprint** — Test pass rate improved from XX% to XX%
  * [List each fix category with count, e.g., "Fixed 4 fixture enum mismatches"]
  * [List any new bugs documented]
  * Final: XXX total tests, XXX passing, XX skipped, XX% pass rate
```

Update the `[Unreleased]` header comment with new test counts and version.

### Document 3: IP2A_BACKEND_ROADMAP.md

**Location:** `docs/IP2A_BACKEND_ROADMAP.md`

**Fields to reconcile:**
- Executive Summary table: Tests, Endpoints, Models, ADRs
- Phase Overview table: Phase 7 status, add Phase 8 note about Stripe removal
- Phase 8 section: Update to reflect Stripe already removed, Square is greenfield
- Technology Decisions table: Remove Stripe row, add Square (Planned) row
- Known Issues section: Update or remove based on current state
- Version History: Add new entry
- Bump document version (v4.0 → v5.0)

### Document 4: IP2A_MILESTONE_CHECKLIST.md

**Location:** `docs/IP2A_MILESTONE_CHECKLIST.md`

**Fields to reconcile:**
- Quick Stats table: All metrics
- Week 35 section: Add with Stripe removal + bug squash tasks
- Test Categories Remaining: Update with post-squash reality
- Known Issues: Update or remove Dispatch.bid bug if fixed
- Phase 8 section: Update Stripe status
- Immediate Next Steps: Refresh priority list
- Bump document version (v2.0 → v3.0)

### Document 5: BUGS_LOG.md

**Location:** `docs/bugs/BUGS_LOG.md` (or wherever it lives)

**Actions:**
- Add entries for any NEW bugs discovered during Week 35 bug squash
- Verify all existing "RESOLVED" bugs are actually resolved (spot-check 2-3)
- If Bug #031 (Dues Test Collisions) was fixed in Week 35, update its status
- Add Bug #032 (or next number): "Stripe Code Removal" — document what was removed for historical record

### Document 6: docs/decisions/ADR-018*.md

**Location:** `docs/decisions/ADR-018*.md`

**Actions:**
- Update Status from "Accepted" to "In Progress"
- Add section: "Stripe Removal (Week 35)"
  - Date of removal
  - What was removed (files, tests, config)
  - What was retained (dues tracking layer)
- Confirm Square Phase A trigger: "After Phase 7 stabilizes"

---

## Cross-Reference Validation

After updating all documents, verify consistency:

```bash
# All documents should report the same test count
echo "=== CROSS-REFERENCE CHECK ==="
grep -n "total tests\|passing\|pass rate" CLAUDE.md
grep -n "total tests\|passing\|pass rate" docs/IP2A_BACKEND_ROADMAP.md
grep -n "total tests\|passing\|pass rate" docs/IP2A_MILESTONE_CHECKLIST.md
grep -n "Total Tests\|Passing\|Pass Rate" CLAUDE.md docs/IP2A_BACKEND_ROADMAP.md docs/IP2A_MILESTONE_CHECKLIST.md

# No document should mention Stripe (after removal)
grep -ri "stripe" CLAUDE.md docs/IP2A_BACKEND_ROADMAP.md docs/IP2A_MILESTONE_CHECKLIST.md

# ADR count should match across all docs
grep -n "ADR" CLAUDE.md | grep -i "count\|total\|18\|19\|20"
```

If ANY discrepancy is found, the ground truth from Step 1-7 wins. Documents conform to reality, not the other way around.

---

## Completion Criteria

- [ ] All 6 documents updated with ground truth numbers
- [ ] Zero Stripe references in CLAUDE.md, Roadmap, or Checklist (except historical/changelog entries)
- [ ] Cross-reference validation passes (same numbers in all docs)
- [ ] ADR-018 updated with Stripe removal record
- [ ] CHANGELOG has Week 35 entry
- [ ] All document version numbers bumped
- [ ] All "Last Updated" dates reflect today's date
- [ ] Git commit with message: `docs: Week 35 document reconciliation — stripe removal, test metrics, version sync`

---

## Session Notes

- This is a HUB task executed by Claude Code. It touches shared project documents, not module-specific code.
- If Claude Code discovers discrepancies between documents and reality that suggest code issues (not just doc drift), STOP and document the finding. Do not fix code bugs during a documentation task.
- This instruction doc should be executed AFTER Week 35 Stripe removal and bug squash are complete. Running it before will just create docs that need updating again.

---

*Hub Claude Code Instruction — Document Reconciliation — February 5, 2026*
