# UnionCore — Week 43: Flatten Operations Sidebar Menu
**Spoke:** Spoke 3: Infrastructure (Cross-Cutting UI)
**Phase:** UI Enhancement Bundle — Item 1 of 5
**Estimated Effort:** 1–2 hours
**Prerequisites:** Git status clean, on a feature branch, app runs locally
**Source:** Hub Handoff Document (February 10, 2026)

---

## Context

The sidebar currently groups SALTing, Benevolence, and Grievances under a "Union Operations" section header. This grouping is an artificial organizational container — RBAC is the real access control mechanism. Flattening the sidebar makes it role-driven rather than category-driven.

**This is a sidebar-only visual change. Do NOT change URL routing structure.**

---

## Pre-Flight Checklist

- [ ] `git status` is clean
- [ ] Create and checkout branch: `git checkout -b feature/flatten-sidebar`
- [ ] App starts without errors: `docker compose up -d` (or however the dev environment starts)
- [ ] Record current test count: `pytest --tb=short -q 2>&1 | tail -5` — note the number
- [ ] Confirm you can access the app in browser at `http://localhost:8000`

---

## Step 1: Discover Current Sidebar Structure

**Do this before writing any code.**

Read the sidebar template:

```bash
cat src/templates/components/_sidebar.html
```

Document what you find:
1. How are sidebar items structured? (`<li>`, `<a>`, DaisyUI `menu` classes?)
2. Is there a `<li class="menu-title">Union Operations</li>` or similar grouping header?
3. Are SALTing/Benevolence/Grievances in a `<details>` expandable section or just nested `<li>` items?
4. What permission check pattern is used? (`{% if has_permission(...) %}`, `{% if current_user.role in [...] %}`, or something else?)
5. What are the current URLs for each item? (`/operations/salting`, `/salting`, etc.)
6. Is there an active-state highlight pattern? (e.g., `{% if request.url.path.startswith('/operations/salting') %}active{% endif %}`)

Also check for a mobile menu duplicate:

```bash
cat src/templates/components/_navbar.html
```

Look for any mobile hamburger menu that duplicates sidebar items. If it exists, it needs the same changes.

**Record your findings as comments at the top of your working notes. You'll need them.**

---

## Step 2: Remove the Operations Grouping Header

Remove the `<li class="menu-title">Union Operations</li>` header (or whatever the actual grouping element is).

If the items are inside a `<details>` collapsible section, unwrap them — remove the `<details>`, `<summary>`, and any wrapper `<ul>` that exists solely for the collapsible group, but keep the individual `<li>` items and their content.

**Do NOT delete the individual sidebar items.** Only remove the grouping container.

---

## Step 3: Promote Items to Top Level

Move SALTing, Benevolence, and Grievances to be top-level sidebar items at the same indentation/nesting level as Members, Dues, Referral & Dispatch, etc.

Each promoted item must:
1. Follow the exact same HTML pattern as existing top-level items (same classes, same structure)
2. Keep its existing URL (do NOT change routes)
3. Keep its existing icon (if it has one)
4. Maintain its active-state highlighting logic

Target sidebar order (adjust based on what actually exists):

```
1. Dashboard
2. Members
3. Dues
4. Referral & Dispatch
5. Grievances
6. SALTing
7. Benevolence
8. Training (if it exists)
9. Reports (if it exists)
10. (Admin section — Staff, Settings, etc.)
```

---

## Step 4: Apply RBAC Permission Checks

Wrap each promoted item in the appropriate permission check, using **the same pattern** already used by existing top-level items. Do not invent a new pattern.

Required visibility rules:

| Item | Visible to |
|------|-----------|
| SALTing | `admin`, `officer`, `organizer`, `developer` |
| Benevolence | `admin`, `officer`, `staff`, `developer` |
| Grievances | `admin`, `officer`, `staff`, `steward`, `developer` |

If the existing sidebar items use `{% if has_permission('some_permission') %}`, then figure out what permissions map to these roles and use the same function. If they use `{% if current_user.role in ['admin', 'officer'] %}`, use that pattern. **Match what's already there.**

If a `developer` role doesn't exist in the system yet (it will be added in a later item), include it in the role lists anyway — the check will simply never match until the role is added, which is harmless.

---

## Step 5: Handle Mobile Menu (If Applicable)

If Step 1 revealed a duplicate menu in `_navbar.html` (mobile hamburger menu), apply the exact same changes:
- Remove Operations grouping
- Promote items to top level
- Apply RBAC checks

---

## Step 6: Verify

Test each scenario manually:

1. **Login as admin** → All sidebar items visible, no "Operations" or "Union Operations" header
2. **Login as organizer** (if test accounts exist) → Only SALTing visible among the three promoted items
3. **Login as staff** → Benevolence and Grievances visible, SALTing NOT visible
4. **Login as steward** (if test account exists) → Only Grievances visible
5. **Login as member** → None of the three promoted items visible
6. **Click each promoted item** → Navigates to the correct page
7. **Active-state highlighting** → The correct sidebar item highlights when on its page
8. **Responsive** → On narrow viewport / mobile, sidebar (or mobile menu) still works correctly

If test accounts for specific roles don't exist, note this as a gap but verify with whatever accounts are available.

---

## Anti-Patterns to Avoid

- **DO NOT** change any URL routes. The URLs stay exactly as they are.
- **DO NOT** refactor the permission system. Use the existing pattern.
- **DO NOT** add new CSS classes. Use the same classes as existing top-level items.
- **DO NOT** remove the actual route handlers or Python code. This is a template-only change.
- **DO NOT** leave the "Union Operations" text anywhere in the sidebar, including as comments.

---

## Acceptance Criteria

- [ ] No "Operations" or "Union Operations" grouping header exists in the sidebar
- [ ] SALTing is a top-level sidebar item with correct RBAC check
- [ ] Benevolence is a top-level sidebar item with correct RBAC check
- [ ] Grievances is a top-level sidebar item with correct RBAC check
- [ ] Active-state highlighting works for each promoted item
- [ ] All existing tests still pass (run full test suite, compare count to pre-flight)
- [ ] Mobile menu (if it exists) matches desktop sidebar changes
- [ ] No URL changes were made

---

## File Manifest

**Modified files:**
- `src/templates/components/_sidebar.html` — primary change
- `src/templates/components/_navbar.html` — only if mobile menu duplicate exists

**Created files:**
- None

**Deleted files:**
- None

---

## Git Commit Message

```
feat(ui): flatten Operations sidebar menu into top-level items

- Remove "Union Operations" section grouping header
- Promote SALTing, Benevolence, Grievances to top-level sidebar items
- Apply per-item RBAC permission checks
- Maintain existing URL routing (no route changes)
- Preserve active-state highlighting for promoted items
- Spoke 3: Infrastructure (Cross-Cutting UI)
```

---

## Session Close-Out

After committing:

1. Update `CLAUDE.md` — increment patch version if appropriate, note sidebar change
2. Update `CHANGELOG.md` — add entry under current version
3. Update any docs under `/docs/` that reference the sidebar structure
4. **Cross-Spoke Impact Note:** This changes the sidebar for all users. No handoff note required unless the change broke something unexpected — the Hub authorized this change.

---

*Spoke 3: Infrastructure — Item 1 of UI Enhancement Bundle*
*UnionCore v0.9.16-alpha*
