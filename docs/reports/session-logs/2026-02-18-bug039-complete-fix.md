# Session Log: Bug #039 Complete Fix — Sticky Headers Across All 6 Tables

**Date:** 2026-02-18
**Branch:** develop
**Version:** v0.9.26-alpha
**Session Type:** Bug Fix (Follow-up to initial SALTing hotfix)
**Duration:** ~45 minutes

---

## Objective

Complete the fix for Bug #039 (sticky table headers not pinning to viewport) across all 6 sortable tables. The initial hotfix session (earlier today) removed `overflow-hidden` from the SALTing card wrapper, but sticky still did not work because a second overflow blocker (`overflow-x-auto` on the inner table wrapper div) remained on all 6 tables.

---

## Background

The first fix attempt removed `overflow-hidden` from the SALTing card wrapper. However, an instruction document flagged that the fix was incomplete: all 6 table wrapper divs still had `overflow-x-auto`, which per CSS spec forces `overflow-y: auto` — creating a vertical scroll context that traps `position: sticky` within the table wrapper rather than allowing it to stick relative to the viewport.

There are two independent overflow blockers:
1. `overflow-hidden` on card wrapper → immediately traps sticky
2. `overflow-x-auto` on table wrapper → forces `overflow-y: auto`, traps sticky within table scroll area

Both must be removed for `table-pin-rows` + `custom.css` sticky offset to work.

---

## Audit Findings

Ran an Explore agent to audit all 6 sortable tables. Confirmed:

| File | `overflow-x-auto`? | `overflow-hidden` on card? |
|------|--------------------|---------------------------|
| `operations/salting/partials/_table.html` | ✅ Present | ✅ Fixed in session 1 |
| `operations/benevolence/partials/_table.html` | ✅ Present | ✅ Present on index.html |
| `operations/grievances/partials/_table.html` | ✅ Present | ✅ Present on index.html |
| `training/students/partials/_table.html` | ✅ Present | ❌ Not present |
| `members/partials/_table.html` | ✅ Present | ✅ Present on index.html |
| `staff/partials/_table_body.html` | ✅ Present | ✅ Present on index.html |

Key finding: `_sortable_th.html` macro has NO `sticky top-32` on `<th>` elements — correct, uses `table-pin-rows` approach. The instruction doc described changing `top-32` to `top-16` in the macro, but this step was inapplicable and correctly skipped.

---

## Changes Made

### Step 1: Remove `overflow-x-auto` from 6 table wrapper divs

Changed `<div class="overflow-x-auto">` → `<div>` in:
- `src/templates/operations/salting/partials/_table.html`
- `src/templates/operations/benevolence/partials/_table.html`
- `src/templates/operations/grievances/partials/_table.html`
- `src/templates/training/students/partials/_table.html`
- `src/templates/members/partials/_table.html`
- `src/templates/staff/partials/_table_body.html`

### Step 2: Remove `overflow-hidden` from 4 remaining card wrappers

Changed `class="card bg-base-100 shadow overflow-hidden"` → `class="card bg-base-100 shadow"` in:
- `src/templates/operations/benevolence/index.html` (line 113)
- `src/templates/operations/grievances/index.html` (line 117)
- `src/templates/members/index.html` (line 113)
- `src/templates/staff/index.html` (line 109)

(SALTing was already fixed in session 1.)

---

## Tests Run

```
pytest src/tests/test_operations_frontend.py src/tests/test_member_frontend.py \
       src/tests/test_staff.py src/tests/test_training_frontend.py -v
```

**Result: 73/73 passed** (0 failures, 0 errors)

---

## Documentation Updated

- `docs/BUGS_LOG.md` — Updated Bug #039 entry: status → "RESOLVED (required two fix attempts)", added "Fix Attempt 1" and "Fix Attempt 2" sections, corrected incorrect Prevention note (the original entry incorrectly stated `overflow-x-auto` is "fine")
- `CHANGELOG.md` — Added entry under `[Unreleased]` for Bug #039 complete fix
- `docs/reports/session-logs/2026-02-18-bug039-complete-fix.md` — This file

---

## CSS Root Cause Reference

Per CSS specification (CSS Overflow Module Level 3):
> If an element has `overflow-x` set to anything other than `visible`, then `overflow-y` is computed as `auto` if it was specified as `visible`.

This means `overflow-x: auto` cannot be applied without implicitly creating a vertical scroll context. That context becomes the scroll boundary for any `position: sticky` descendants, defeating viewport-relative sticky positioning.

**Proof:** An element with `overflow-x: auto; overflow-y: visible` resolves to `overflow-x: auto; overflow-y: auto` in the browser.

There is no CSS workaround. The only solution is to not use `overflow-x: auto` as an ancestor of sticky elements.

---

## Known Limitation

Without `overflow-x-auto` on the table wrapper, wide tables may cause horizontal overflow visible at the card level rather than scrolling within the table card. In practice, all 6 affected tables fit within the typical viewport at `lg` breakpoints. If a future table is very wide, the solution is to implement horizontal scrolling at a level above the sticky boundary (e.g., on a page-level container), not on the immediate table wrapper.

---

## Next Steps

- Remaining sortable header rollout: Referral Books, Dues, Dispatch, Audit Log
- Template: do NOT add `overflow-x-auto` or `overflow-hidden` to any ancestor of a `table-pin-rows` table
- Pattern confirmed in `docs/table-sortable-rollout.md` Critical Rules section
