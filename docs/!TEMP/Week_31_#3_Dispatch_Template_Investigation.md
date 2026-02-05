# Claude Code Instruction Document: Week 31 — Dispatch Template Investigation

**Sprint:** Week 31 — Work Package 2
**Spoke:** Spoke 2 (Operations)
**Source:** Hub guidance → Spoke 2 generation, February 5, 2026
**Effort:** 1-2 hours (HARD CAP: 2 hours)
**Goal:** Investigate and fix (or document) 3 remaining dispatch frontend test failures
**Expected Result:** Either +3 passing tests OR Bug #030 documented
**Branch:** `develop`

---

## IMPORTANT: Read Before Starting

1. **Read `CLAUDE.md` first.** It is the project context document.
2. **TIME BOX: 2 hours maximum.** If the fix isn't obvious by hour 2, stop and document.
3. **These are NOT field name bugs.** Bug #029 (14 field name mismatches) is already fixed. These are template rendering or content issues.
4. **Two acceptable outcomes:** (A) Fix the tests, or (B) Document as Bug #030. Both are valid.
5. **Do NOT restructure templates or services** to make tests pass. If the template logic is fundamentally wrong, document it.

---

## Context

Bug #029 fixed 14 field name mismatches in `dispatch_frontend_service.py`, resolving the majority of dispatch frontend failures. Three tests survived that fix — they fail for different reasons.

### The 3 Failing Tests

| Test | File | Expected Content | Likely Issue |
|------|------|-----------------|--------------|
| `test_dashboard_shows_stats` | `test_dispatch_frontend.py` | "Today's Dispatches" text in HTML | Template not rendering stat cards |
| `test_cutoff_warning_shown` | `test_dispatch_frontend.py` | AM/PM time context in HTML | Time-aware logic not producing expected output |
| `test_dashboard_stats_calculation` | `test_dispatch_frontend.py` | Correct stat values in rendered HTML | Data binding between service and template |

---

## Phase 1: Diagnostic (30 minutes)

### Step 1.1: Confirm baseline

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
```

**If Work Package 1 (dues fix) was completed first:**
```bash
pytest src/tests/test_dispatch_frontend.py -v --tb=short
```

Confirm exactly 3 tests fail. Record their names.

### Step 1.2: Run each failing test individually with full output

```bash
# Test 1: Dashboard stats
pytest src/tests/test_dispatch_frontend.py::test_dashboard_shows_stats -v --tb=long 2>&1 | tee /tmp/dispatch_test1.txt

# Test 2: Cutoff warning
pytest src/tests/test_dispatch_frontend.py::test_cutoff_warning_shown -v --tb=long 2>&1 | tee /tmp/dispatch_test2.txt

# Test 3: Stats calculation
pytest src/tests/test_dispatch_frontend.py::test_dashboard_stats_calculation -v --tb=long 2>&1 | tee /tmp/dispatch_test3.txt
```

### Step 1.3: Extract what each test expects vs what it gets

For each test, identify:
1. **What HTTP endpoint is being called?** (e.g., `/dispatch/dashboard`)
2. **What does the test assert?** (e.g., `assert "Today's Dispatches" in response.text`)
3. **What does the response actually contain?** (Capture a snippet of `response.text`)
4. **Is the response a 200 OK?** (If 302 or 401, this is an auth issue, not a template issue)

```bash
# Read the test file to understand expectations
grep -A 20 "def test_dashboard_shows_stats" src/tests/test_dispatch_frontend.py
grep -A 20 "def test_cutoff_warning_shown" src/tests/test_dispatch_frontend.py
grep -A 20 "def test_dashboard_stats_calculation" src/tests/test_dispatch_frontend.py
```

### Step 1.4: Classify the failure type

For each of the 3 tests, determine which category it falls into:

| Category | Symptoms | Action |
|----------|----------|--------|
| **A: Auth issue** | 302 redirect to login, or 401 | Fix auth fixture (same pattern as Week 29 Phase 3) |
| **B: Template not receiving data** | 200 OK but expected text missing, template renders empty sections | Fix service method return values |
| **C: Template not rendering data** | 200 OK, data exists in context, but Jinja2 syntax wrong | Fix template variable references |
| **D: Test expectations wrong** | 200 OK, template renders correctly, but test asserts wrong string | Fix the test assertion |
| **E: Time-dependent** | Test passes at certain times, fails at others | Mock datetime in test |

---

## Phase 2: Investigation (45 minutes)

Work through these checks in order. Stop as soon as you find the root cause.

### Check 1: Auth Status (5 minutes)

```bash
# Is the response a 200 or a redirect?
grep -B 5 -A 15 "test_dashboard_shows_stats" src/tests/test_dispatch_frontend.py
```

If the test uses `client.get("/dispatch/dashboard")` without auth cookies, it will get 302.

**Compare with a PASSING dispatch test** to see how auth is set up:
```bash
grep -B 5 -A 10 "def test_" src/tests/test_dispatch_frontend.py | head -60
```

If auth is the issue → apply the same cookie fixture pattern from `test_referral_frontend.py` (which passes).

### Check 2: Service Return Values (15 minutes)

```bash
# Read the DispatchFrontendService dashboard method
grep -A 40 "def get_dashboard_stats\|def get_dashboard\|def dashboard" src/services/dispatch_frontend_service.py
```

Document:
- What keys does the method return?
- Does it return `today_dispatches` or `todays_dispatches` or `dispatches_today`?

Then check the template:
```bash
# What variables does the template use?
grep -E "\{\{.*dispatch\|today\|cutoff\|stat" src/templates/dispatch/dashboard.html
```

**Mismatch between service return keys and template variable names = root cause.**

### Check 3: Template Rendering (10 minutes)

```bash
# Read the full dashboard template
cat src/templates/dispatch/dashboard.html
```

Look for:
- `{{ stats.today_dispatches }}` or similar variable references
- Conditional blocks: `{% if stats %}` that might hide content when stats is empty
- Typos in variable names

### Check 4: Time-Aware Logic (10 minutes)

The dispatch system has time-gated features (5:30 PM - 7:00 AM bidding window, 3:00 PM cutoff). If `test_cutoff_warning_shown` expects AM/PM text, the service may be computing time context differently than the test expects.

```bash
# Check how time context is determined
grep -A 20 "cutoff\|time_context\|is_morning\|is_afternoon" src/services/dispatch_frontend_service.py
```

If the service uses `datetime.now()` without mocking, tests will behave differently at different times of day.

**If time-dependent:** The fix is to mock `datetime.now()` in the test, not to change the service:

```python
from unittest.mock import patch
from datetime import datetime

@patch('src.services.dispatch_frontend_service.datetime')
def test_cutoff_warning_shown(mock_dt, auth_client):
    mock_dt.now.return_value = datetime(2026, 2, 5, 14, 30)  # 2:30 PM — before cutoff
    mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
    response = auth_client.get("/dispatch/dashboard")
    assert "3:00 PM" in response.text  # or whatever the expected cutoff text is
```

### Check 5: Test Assertion Accuracy (5 minutes)

If the template renders correctly but the test asserts the wrong string:

```bash
# What exact string does the test look for?
grep -E "assert.*in.*response\|assert.*text\|assertIn" src/tests/test_dispatch_frontend.py | grep -i "dispatch\|cutoff\|stat"
```

Compare the asserted string against what actually appears in the template HTML. Case sensitivity, extra whitespace, HTML entities — all common gotchas.

---

## Phase 3: Fix or Document (30 minutes)

### Path A: Fix Found → Apply and Verify

1. Apply the fix (template variable name, auth fixture, datetime mock, or test assertion)
2. Run the individual test: `pytest src/tests/test_dispatch_frontend.py::test_name -v`
3. Run all dispatch tests: `pytest src/tests/test_dispatch_frontend.py -v`
4. Run full suite: `pytest -v --tb=short 2>&1 | tail -20`
5. Confirm no regressions

**Commit:**
```bash
git add -A
git commit -m "fix(dispatch): resolve 3 template test failures (Week 31 WP2)

- [describe what was wrong and what was fixed]
- Test results: X/558 passing (Y%), up from 521/558 (93.4%)
"
git push origin develop
```

### Path B: Structural Issue → Document as Bug #030

If the investigation reveals a problem that would require significant refactoring (>2 hours), document it:

**Create file:** `docs/bugs/BUG-030-dispatch-template-rendering.md`

```markdown
# Bug #030: Dispatch Dashboard Template Rendering Issues

**Filed:** [date]
**Sprint:** Week 31
**Severity:** Low — does not affect user-facing functionality
**Status:** Open
**Blocks:** 3 tests in test_dispatch_frontend.py

## Failing Tests

1. `test_dashboard_shows_stats` — [description of failure]
2. `test_cutoff_warning_shown` — [description of failure]
3. `test_dashboard_stats_calculation` — [description of failure]

## Root Cause

[What you found during investigation]

## Why This Is Not a Quick Fix

[Explain the structural issue]

## Proposed Fix

[What needs to change and estimated effort]

## Impact

- 3 tests remain failing
- Dashboard renders [correctly/incorrectly] for actual users
- [Does this affect any user-facing functionality?]

## Files Involved

- `src/services/dispatch_frontend_service.py`
- `src/templates/dispatch/dashboard.html`
- `src/tests/test_dispatch_frontend.py`
```

**Commit:**
```bash
git add docs/bugs/BUG-030-dispatch-template-rendering.md
git commit -m "docs: add Bug #030 — dispatch template rendering issues (3 tests)

- Investigated 3 remaining dispatch frontend test failures
- Root cause: [brief description]
- Documented for future fix — does not block user-facing functionality
"
git push origin develop
```

---

## Phase 4: Documentation (10 minutes)

Regardless of Path A or Path B:

### Step 4.1: Update CLAUDE.md

- Update test counts (if Path A fixed tests)
- Update "Remaining Issues" section
- If Bug #030 created, reference it

### Step 4.2: Update CHANGELOG.md

```markdown
### Fixed (or ### Documented)
- Dispatch dashboard template tests — [fixed/documented as Bug #030] (3 tests, Week 31 WP2)
```

### Step 4.3: Session summary for Hub handoff

At the end, provide a brief summary:

```
Week 31 WP2 Results:
- Tests investigated: 3
- Tests fixed: [0 or 3]
- Bug filed: [Bug #030 or N/A]
- Time spent: [X minutes]
- Pass rate: [current]
- Cross-cutting concerns: [any changes to conftest.py, base templates, etc.]
```

---

## Files Expected to Change

**If fixed (Path A):**
```
src/tests/test_dispatch_frontend.py    — Test fixes (auth, assertions, mocks)
src/services/dispatch_frontend_service.py  — Service fixes (if data binding issue)
src/templates/dispatch/dashboard.html  — Template fixes (if rendering issue)
CLAUDE.md                              — Updated test counts
CHANGELOG.md                          — Fix entry
```

**If documented (Path B):**
```
docs/bugs/BUG-030-dispatch-template-rendering.md  — New bug report
CLAUDE.md                                          — Updated remaining issues
CHANGELOG.md                                       — Documentation entry
```

---

## Acceptance Criteria

- [ ] All 3 tests investigated (root cause identified)
- [ ] Either fixed (all 3 pass) OR documented (Bug #030 filed)
- [ ] No regressions from investigation
- [ ] CLAUDE.md updated
- [ ] CHANGELOG.md updated
- [ ] Committed to develop branch
- [ ] Time spent ≤ 2 hours
- [ ] Session summary written for Hub handoff

---

## Troubleshooting

**If more than 3 dispatch tests are failing:**
The baseline may have shifted. Focus only on the 3 described in this doc. If additional failures exist, they're a different issue — note them but don't investigate in this work package.

**If the auth fixture pattern doesn't match Week 29:**
The dispatch frontend was built in Week 27 (after the referral frontend in Week 26). Check if `dispatch_frontend.py` router uses the same auth dependency as `referral_frontend.py`. If not, that's the issue.

**If time-aware tests are inherently flaky:**
The right fix is mocking, not changing the time logic. Flag this pattern for Hub — it may affect future time-dependent features across all Spokes.

---

**End of Instruction Document**
*Generated by Spoke 2 — February 5, 2026*
*For execution via Claude Code*
*HARD CAP: 2 hours execution time*
