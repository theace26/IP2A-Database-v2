# Bug #029: Phase 7 Model Field Name Mismatches

**Date Discovered:** 2026-02-05
**Date Fixed:** 2026-02-05
**Severity:** High (19 dispatch frontend tests blocked)
**Status:** ✅ FIXED — Commit `8480366`

## Symptoms

Dispatch frontend tests failed with multiple AttributeError exceptions:
- `AttributeError: type object 'Dispatch' has no attribute 'status'`
- `AttributeError: type object 'JobBid' has no attribute 'status'`
- `AttributeError: type object 'BookRegistration' has no attribute 'book_priority_number'`
- `AttributeError: type object 'JobBid' has no attribute 'bid_time'`

Affected methods in `src/services/dispatch_frontend_service.py`:
- `get_dashboard_stats()`
- `get_active_dispatches()`
- `get_pending_bids()`
- `get_request_detail()`
- `get_bids_for_request()`
- `get_queue_positions()`

Tests: 13/29 passing → 19 failures due to field name mismatches

## Root Cause Analysis

**What Happened:**
The `dispatch_frontend_service.py` file was written during Week 27 with incorrect field names that didn't match the Phase 7 model definitions. This was a copy-paste error or incorrect assumption about naming conventions.

**Field Name Mismatches (14 total):**

### 1. Dispatch Model
**Correct:** `dispatch_status` (defined in model, migration 3f0166296a87 line 215, schema)
**Incorrect:** `status` (used 3 times in service)

### 2. JobBid Model
**Correct:** `bid_status` (defined in model line 99)
**Incorrect:** `status` (used 2 times in service)

**Correct:** `bid_submitted_at` (defined in model line 80)
**Incorrect:** `bid_time` (used 3 times in service)

### 3. BookRegistration Model
**Correct:** `registration_number` (APN - DECIMAL(10,2), defined in model line 78)
**Incorrect:** `book_priority_number` (used 3 times in service - field doesn't exist)
**Incorrect:** `applicant_priority_number` (used 3 times in service - field doesn't exist)

**Note:** The service attempted to order by `book_priority_number, applicant_priority_number` but BookRegistration only has `registration_number` (the APN). The `book_number` field exists on ReferralBook, not BookRegistration.

## Solution

**Files Modified:**
- `src/services/dispatch_frontend_service.py` — 14 field name corrections

**Corrections Applied:**
```python
# Dispatch field name (3 occurrences)
Dispatch.status → Dispatch.dispatch_status

# JobBid status field (2 occurrences)
JobBid.status → JobBid.bid_status

# JobBid time field (3 occurrences)
JobBid.bid_time → JobBid.bid_submitted_at

# BookRegistration ordering (6 occurrences → 3 after simplification)
BookRegistration.book_priority_number → (removed)
BookRegistration.applicant_priority_number → BookRegistration.registration_number
```

**Ordering Logic:**
Changed from non-existent two-field ordering to single-field FIFO ordering by APN:
```python
# Before (WRONG):
.order_by(
    BookRegistration.book_priority_number,
    BookRegistration.applicant_priority_number
)

# After (CORRECT):
.order_by(
    BookRegistration.registration_number  # APN = FIFO ordering
)
```

## Impact

### Test Results
- **Dispatch frontend tests:** 13 → 26 passing (89.7% pass rate, +13 tests)
- **Full test suite:** 507 → 517 passing (+10 tests)
- **Pass rate improvement:** 90.9% → 92.7% (+1.8 percentage points)

### Tests Unblocked
- `test_dashboard_stats_calculation`
- `test_dashboard_shows_time_context`
- `test_morning_referral_renders`
- `test_morning_referral_shows_time_guards`
- `test_queue_renders`
- `test_queue_book_filter`
- `test_stats_partial_returns_html`
- `test_bid_queue_partial`
- `test_queue_table_partial`
- `test_time_context_includes_bidding_status`
- Plus 3 more tests unblocked in other suites

### Remaining Failures (3)
The following 3 failures are NOT field name bugs but template/content assertion issues (different class of bug):
- `test_dashboard_shows_stats` — Missing "Today's Dispatches" text in HTML
- `test_cutoff_warning_shown` — Missing time context (PM/AM) in HTML
- `test_dashboard_stats_calculation` — Template rendering issue

These require separate investigation into template data binding.

## Prevention

### Lessons Learned
1. **Always verify model attribute names** before referencing in service layer
2. **Prefixed columns** (`dispatch_status`, `bid_status`) are prone to being abbreviated incorrectly
3. **Non-existent fields** (`book_priority_number`) indicate misunderstanding of schema relationships
4. Field name mismatches are a **recurring theme**: Bugs #026, #027, #028, #029

### Pattern Recognition
This is the **4th occurrence** of field name mismatch bugs:
- **Bug #026:** `Member.general_notes` vs DB column `notes`
- **Bug #027:** `AuditLog.user_id` vs `changed_by`
- **Bug #028:** Test fixtures using obsolete enum string values
- **Bug #029:** Multiple Phase 7 model field name mismatches (this bug)

### Recommended Preventions
1. **Code Review Checklist:** Verify all `Model.attribute` references match model definitions
2. **Linter Rule:** ADR-017 should include validation of model field references in services
3. **CI Check:** Add grep scan: `grep -rn "Dispatch\.status[^_]" src/` should return 0 results
4. **Test Early:** Run service tests immediately after writing service methods
5. **Schema Reference:** Keep Phase 7 model field inventory document for quick reference

## Verification

### Pre-Fix Scan
```bash
grep -n "Dispatch\.status" src/services/dispatch_frontend_service.py
# 3 matches

grep -n "JobBid\.status" src/services/dispatch_frontend_service.py
# 2 matches

grep -n "JobBid\.bid_time" src/services/dispatch_frontend_service.py
# 3 matches

grep -n "book_priority_number\|applicant_priority_number" src/services/dispatch_frontend_service.py
# 6 matches
```

### Post-Fix Scan
```bash
# All scans return 0 results - no remaining incorrect field names
grep -rn "Dispatch\.status\|JobBid\.status\|JobBid\.bid_time\|book_priority_number\|applicant_priority_number" src/services/ src/routers/ src/tests/
# No output (clean)
```

## References

- **Commit:** `8480366` (February 5, 2026)
- **Instruction Document:** `docs/!TEMP/Week_30_Dispatch_Status_Fix.md`
- **Diagnostic Source:** Spoke 2 diagnostic session (February 5, 2026)
- **Related Bugs:** #026 (member column mapping), #027 (audit column names), #028 (enum values)
- **ADR Reference:** ADR-017 (Schema Drift Prevention Strategy)
- **Session Log:** Week 30 fix session

## Commit Message

```
fix(dispatch): correct Phase 7 model field name mismatches (Bug #029)

Bug #029: dispatch_frontend_service.py referenced incorrect field names for
Phase 7 models. Root cause: copy-paste errors during Week 27 frontend service
implementation.

Field name corrections (14 total):
- Dispatch.status → Dispatch.dispatch_status (3 occurrences)
- JobBid.status → JobBid.bid_status (2 occurrences)
- JobBid.bid_time → JobBid.bid_submitted_at (3 occurrences)
- BookRegistration.book_priority_number → registration_number (3 occurrences)
- BookRegistration.applicant_priority_number → registration_number (3 occurrences)

Impact:
- Dispatch frontend tests: 13 → 26 passing (89.7% pass rate)
- Full test suite: 507 → 517 passing (+10 tests, 92.7% pass rate)

No similar issues found in other service/router/test files.
```
