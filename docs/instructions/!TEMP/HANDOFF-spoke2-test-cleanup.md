# Hub → Spoke 2 Handoff: Post-Diagnostic Test Cleanup

**Handoff Type:** Hub Decision → Spoke Implementation
**Date:** February 5, 2026
**From:** Hub Project
**To:** Spoke 2 (Operations)
**Priority:** Immediate — next Claude Code session

---

## What Happened

The test verification diagnostic (Feb 5, 2026) brought the suite from 68% → 84% passing (495/590). Three categories of remaining failures were escalated to the Hub for architectural decisions. Those decisions are now made.

**Reference:** `docs/reports/session-logs/2026-02-05-test-verification-diagnostic-report.md`

---

## Hub Decisions (3)

### Decision 1: Stripe Tests (30 failures) → SKIP-MARK AS DEAD CODE

**Rationale:** Stripe is being replaced by Square (ADR-018, accepted Feb 5, 2026). All Stripe-specific tests are deprecated. No point configuring Stripe sandbox keys or building mocks for code that's being removed.

**What Spoke 2 should instruct Claude Code to do:**
- Add module-level `pytestmark = pytest.mark.skip(reason="Stripe deprecated — migrating to Square (ADR-018). Remove with Square migration.")` to all Stripe test files
- Do NOT delete the files — they serve as reference for Square test implementation
- Verify skipped tests don't count against pass rate

**Files affected:**
- `src/tests/test_stripe_integration.py`
- `src/tests/test_stripe_frontend.py`

---

### Decision 2: Phase 7 Tables (19 errors) → APPLY MIGRATIONS

**Rationale:** The Phase 7 tables are defined, the services and APIs are written, the tests are correct — the tables just don't physically exist in the database yet. Apply the migrations.

**What Spoke 2 should instruct Claude Code to do:**
- Check current Alembic migration state (`alembic current`)
- Apply pending migrations (`alembic upgrade head`)
- Verify Phase 7 tables exist: `referral_books`, `book_registrations`/`registrations`, `registration_activity`, `labor_requests`/`job_requests`, `job_bids`/`web_bids`, `dispatches`
- Re-run Phase 7 tests and report results
- **If migrations fail:** STOP. Do not force-create tables. Document the error and escalate back to Hub.

---

### Decision 3: Miscellaneous Frontend Tests (17 failures) → INVESTIGATE AND FIX

**Rationale:** These are legitimate failures, not blocked by anything architectural. They likely have the same root causes as the fixes already applied (schema drift, stale fixtures, enum mismatches).

**What Spoke 2 should instruct Claude Code to do:**
- Run each failing test file individually with `--tb=long`
- Categorize each failure (schema drift, missing fixture, stale route, actual bug, blocked by Phase 7 tables)
- Fix what's fixable
- Do NOT modify business logic to make tests pass — flag those for Hub review
- Document everything in session log

**Files to investigate:**
- `src/tests/test_frontend.py` (2 failures)
- `src/tests/test_members.py` (1 failure)
- `src/tests/test_setup.py` (4 failures)
- `src/tests/test_audit_frontend.py` (4 failures)

---

## ADR-018 Staging

The Hub has produced `ADR-018-square-payment-integration.md`. Include in the Claude Code instruction: copy this file to `docs/decisions/ADR-018-square-payment-integration.md`, update ADR-013 status to "Superseded by ADR-018", and update `docs/decisions/README.md` with the new entry.

**The ADR-018 file will be provided to the Spoke session separately** (user will upload or paste it).

---

## Expected Outcome After Spoke Execution

| Metric | Before | Expected After |
|--------|--------|----------------|
| Passed | 495 | 530-560+ |
| Failed | 65 | 10-20 |
| Errors | 30 | 0-5 |
| Skipped | 0 | ~30 (Stripe) |
| Pass Rate | 84% | 90%+ |

---

## End-of-Session Requirements for Claude Code

- Update test counts in `CLAUDE.md`
- Create session log in `docs/reports/session-logs/`
- Stage ADR-018 in `docs/decisions/`
- Mark ADR-013 as superseded
- Update `docs/decisions/README.md`
- Commit with descriptive message

---

## Scope Boundaries — Tell Claude Code These Explicitly

**DO:**
- Skip-mark Stripe tests
- Apply Phase 7 migrations
- Fix miscellaneous frontend test failures
- Update documentation and test counts
- Stage ADR-018

**DO NOT:**
- Write any Square integration code
- Remove Stripe code (happens during Square migration later)
- Create new Phase 7 migrations
- Modify business logic to make tests pass
- Touch the grant services test failure (1 test — separate investigation)

---

**Spoke 2:** Use this handoff to generate a Claude Code instruction document with full codebase context. You have access to the actual file paths, service patterns, and test infrastructure that the Hub does not.
