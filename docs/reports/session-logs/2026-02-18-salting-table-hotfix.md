# Session Log: SALTing Table Hotfix — Bugs #037, #038, #039

**Date:** 2026-02-18
**Session Type:** P1 Hotfix
**Spoke:** Spoke 3: Infrastructure (Cross-Cutting UI)
**Duration:** ~1 hour
**Version:** v0.9.26-alpha (no version bump — hotfix only)

---

## Objective

Fix three related bugs on the SALTing Activities table that were introduced during or following the sortable headers rollout. The table was unusable after any sort click.

---

## Bugs Fixed

### Bug #037 — HTMX Sort Click Returns Full Page Into Table Body (P1)

**Root cause:** The sortable header macro uses a relative URL `?sort=column&order=dir`. On `/operations/salting`, HTMX resolved this to the full-page route `/operations/salting?sort=...`. That route had no HTMX detection and returned the complete `index.html` page, which HTMX swapped into `<tbody id="table-body">`, causing total layout collapse.

**Fix:** Updated `salting_list_page` route to accept sort/order params and detect `HX-Request + HX-Target==table-body`, returning only the `_table_body.html` partial. Also updated `index.html` to inject sort state into the initial HTMX load URL for refresh persistence.

### Bug #038 — Header Text Invisible Without Hover (Medium)

**Root cause:** Macro `<th>` lacked a permanent text color class. `custom.css` sets `color: #ffffff` but Tailwind CDN can override it. White text on DaisyUI "light" theme's `base-200` background is invisible.

**Fix:** Added `text-white` explicitly to macro `<th>` base class and the non-sortable "Actions" `<th>` in `_table.html`.

### Bug #039 — Sticky Header Not Working (Medium)

**Root cause:** Card wrapper div had `overflow-hidden`. `overflow: hidden` on any ancestor of a sticky element traps it within the clipping context, preventing `position: sticky` from working.

**Fix:** Removed `overflow-hidden` from the card wrapper in `index.html`.

---

## Files Changed

| File | Change |
|------|--------|
| `src/routers/operations_frontend.py` | Added sort/order params + HTMX detection to `salting_list_page` route |
| `src/templates/operations/salting/index.html` | Removed `overflow-hidden` from card; injected `current_sort`/`current_order` into initial HTMX load URL |
| `src/templates/components/_sortable_th.html` | Added `text-white` to `<th>` base class |
| `src/templates/operations/salting/partials/_table.html` | Added `text-white` to non-sortable Actions `<th>` |

---

## Files Created

| File | Purpose |
|------|---------|
| `docs/table-sortable-rollout.md` | Rollout tracker for sortable headers across all tables; includes per-table status, pattern documentation, and critical rules |
| `docs/reports/session-logs/2026-02-18-salting-table-hotfix.md` | This file |

---

## Test Results

- `test_operations_frontend.py`: **21/21 passed** ✅
- Zero regressions from changes

---

## Patterns Established / Reinforced

1. **Full-page route must handle HTMX sort requests.** The sortable header macro uses relative URLs, so the full-page route (not just the search endpoint) must detect `HX-Request + HX-Target==table-body` and return the partial.

2. **`overflow-hidden` on card ancestors breaks sticky.** Card wrappers for tables should be `class="card bg-base-100 shadow"` with no overflow modifier. `overflow-x-auto` on the inner table wrapper div is safe for horizontal scroll.

3. **Explicit `text-white` on `<th>` beats CSS rule in CDN context.** Don't rely solely on `custom.css` for text color when using Tailwind CDN Play — add the class directly to the element.

---

## Cross-Spoke Impact

The `_sortable_th.html` macro change (Bug #038) affects ALL tables that use sortable headers (Benevolence, Grievances, Students, Members, Staff). All of those tables now have white header text. This is purely additive — no breakage.

The Bug #037 route pattern must be applied to each remaining table when sortable headers are rolled out to them (Referral Books, Dues, Dispatch, Audit Log). Documented in `docs/table-sortable-rollout.md`.

---

## Next Steps

- Roll out sortable headers to remaining tables (Referral Books, Dues, Dispatch, Audit Log)
- Each rollout now requires the full-page route to handle HTMX sort partial (Bug #037 pattern)
- Stakeholder demo prep
- Phase 7 data collection (blocked on LaborPower access)
