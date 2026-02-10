# Demo Seed Field Mismatch Fixes — February 9, 2026

## Session Summary

**Objective:** Fix demo seed data to display grievances, benevolence applications, and SALTing activities in demo UI

**Root Cause:** The `demo_seed.py` file was written from documentation rather than actual model definitions, resulting in extensive field name mismatches across multiple models.

**Duration:** ~3 hours
**Commits:** 14
**Files Fixed:** 1 (`src/db/demo_seed.py`)
**Bug IDs:** #030-#034

---

## Work Completed

### Phase 1: Initial Investigation

**Issue:** Docker container needed rebuild to pick up new grievances/benevolence/SALTing seed data.

**Discovery:** After 7 iterative fixes for different field mismatches, recognized pattern that `demo_seed.py` was written from documentation instead of actual SQLAlchemy models.

**Decision:** Created comprehensive mapping document (`docs/!TEMP/MODEL_FIELD_MAPPING.md`) to batch-fix all Student and FileAttachment issues.

### Phase 2: Student Model Fix (Bug #030)

**Problem:** demo_seed.py tried to create Student with `first_name`, `last_name`, `email`, `phone` fields that don't exist on Student model.

**Root Cause:** Student links to Member via `member_id` FK. Names/email/phone come from the linked Member record.

**Fix:**
1. Create Member first with name/email/phone
2. Link Student to Member via `member_id`
3. Changed `cohort_id` → `cohort` (string field, not FK)
4. Added required `application_date` field

**Commit:** `cb59609`

### Phase 3: FileAttachment Model Fix (Bug #030)

**Problem:** Used wrong field names: `filename`, `entity_type`, `entity_id`, `uploaded_at`, `uploaded_by`

**Actual Fields:**
- `file_name` (not filename)
- `record_type` (not entity_type)
- `record_id` (not entity_id)
- `file_path` (required, was missing)
- `created_at` (auto-set, not uploaded_at)
- NO `uploaded_by` field

**Fix:** Updated all field names and added required `file_path`.

**Commit:** `cb59609`

### Phase 4: DuesRate Model Fix (Bug #031)

**Problem:** Tried to use `rate_code`, `rate_name`, `is_active` fields that don't exist.

**Actual Fields:**
- `classification` (enum, required)
- `monthly_amount` (required)
- `effective_date` (required)
- `end_date` (nullable — NULL = active)
- `description` (nullable)

**Fix:**
1. Removed non-existent fields
2. Created 7 rates (one per classification)
3. Used `end_date IS NULL` to query active rates (not `is_active`)

**Commits:** `835b4a6`, `cb89067`, `3da0229`

### Phase 5: DuesPeriod Model Fix (Bug #032)

**Problem:** Used `year`, `month`, `period_name`, `start_date` fields.

**Actual Fields:**
- `period_year` (not year)
- `period_month` (not month)
- `due_date` (required, was missing)
- `grace_period_end` (required, was missing)
- `period_name` is a `@property`, not a database field

**Fix:**
1. Renamed fields
2. Added required `due_date` and `grace_period_end`
3. Updated all WHERE clauses to use `period_year`/`period_month`

**Commits:** `9f90cac`, `e80c87b`

### Phase 6: DuesPaymentMethod Enum Fix (Bug #033)

**Problem:** Used `BANK_TRANSFER` enum value that doesn't exist.

**Correct Value:** `ACH_TRANSFER`

**Commit:** `742d577`

### Phase 7: DuesPayment Model Fix (Bug #034)

**Problem:** Tried to use `rate_id` and `payment_status` fields.

**Actual Fields:**
- NO `rate_id` field (amount stored directly in `amount_due`)
- `status` (not payment_status)

**Fix:** Removed `rate_id`, renamed `payment_status` → `status`

**Commit:** `a336c28`

---

## Additional Work

### Square Payment Configuration

Added Square API environment variables to `.env.demo`:
- `SQUARE_ENVIRONMENT=sandbox`
- `SQUARE_ACCESS_TOKEN=`
- `SQUARE_APPLICATION_ID=`
- `SQUARE_LOCATION_ID=`
- `SQUARE_WEBHOOK_SIGNATURE_KEY=`

**Note:** `.env.demo` is gitignored — user must add their Square credentials manually.

### Dependency Verification

Confirmed required dependencies installed:
- ✅ **WeasyPrint 60.1** — PDF report generation
- ✅ **Square SDK 44.0.0.20260122** — Payment processing

---

## Bugs Documented

| Bug ID | Title | Commit |
|--------|-------|--------|
| #030 | Student & FileAttachment field mismatches | `cb59609` |
| #031 | DuesRate field mismatches (3 parts) | `835b4a6`, `cb89067`, `3da0229` |
| #032 | DuesPeriod field mismatches (2 parts) | `9f90cac`, `e80c87b` |
| #033 | DuesPaymentMethod enum value mismatch | `742d577` |
| #034 | DuesPayment field mismatches | `a336c28` |

---

## Next Steps

1. **Rebuild Docker image** with all fixes
2. **Test demo seed completion** — verify all phases complete without errors
3. **Verify union operations data** — confirm grievances/benevolence/SALTing appear in UI
4. **Add Square credentials** to `.env.demo` for payment testing
5. **Test PDF report generation** with WeasyPrint

---

## Lessons Learned

**Schema Drift Prevention:**
1. ALWAYS write seed code from actual model definitions, not documentation
2. Run full seed locally before committing
3. Use type hints and IDE autocomplete to catch field name errors
4. Consider adding schema validation tests to catch mismatches early

**Pattern Recognition:**
After 7+ iterative fixes, recognized that demo_seed.py had systemic issue (written from docs). Created comprehensive mapping document to batch-fix remaining issues.

---

## Files Modified

```
src/db/demo_seed.py                              # 14 commits, 100+ lines changed
deployment/.env.demo                             # Added Square config (not committed)
docs/!TEMP/MODEL_FIELD_MAPPING.md                # Created comprehensive mapping
docs/reports/session-logs/2026-02-09-demo-seed-field-fixes.md  # This file
docs/BUGS_LOG.md                                 # Updated with Bugs #030-#034
```

---

**Session End:** February 9, 2026, 22:30 PST
**Next Session:** Final demo seed testing and documentation
