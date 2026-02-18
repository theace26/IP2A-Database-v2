# UnionCore — UI Enhancement Bundle: Consolidated Claude Code Instructions
**Spoke:** Spoke 3: Infrastructure (Cross-Cutting UI)
**Source:** Hub Handoff Document (February 10, 2026)
**Total Estimated Effort:** 10–16 hours across 3–4 sessions
**Version Baseline:** v0.9.16-alpha
**Related ADR:** ADR-019 (Developer Super Admin Role)

---

## Table of Contents

1. [Execution Overview](#execution-overview)
2. [Global Pre-Flight](#global-pre-flight)
3. [Global Scope Boundaries](#global-scope-boundaries)
4. [Item 1: Flatten Operations Sidebar Menu](#item-1-flatten-operations-sidebar-menu)
5. [Item 2: Developer Super Admin Role — Backend](#item-2-developer-super-admin-role--backend)
6. [Item 3: View As Toggle — Frontend](#item-3-view-as-toggle--frontend)
7. [Item 4: Replace Dashboard Cards](#item-4-replace-dashboard-cards)
8. [Item 5: Sortable + Sticky Table Headers](#item-5-sortable--sticky-table-headers)
9. [Cross-Spoke Handoff Notes](#cross-spoke-handoff-notes)
10. [Known Risks & Blockers](#known-risks--blockers)

---

## Execution Overview

### Dependency Graph

```
Item 1: Flatten Sidebar ──────────────────────┐
                                               │
Item 2: Developer Role Backend ──┐             ├─→ Item 4: Dashboard Cards
                                 │             │
Item 3: View As Frontend ────────┘             │
                                               │
Item 5: Sortable Headers ─────────────── (independent, parallel)
```

### Execution Order

| Step | Item | Dependencies | Est. Hours |
|------|------|-------------|------------|
| 1 | Item 1: Flatten sidebar | None | 1–2 |
| 2 | Item 2: Developer role backend | None | 2–3 |
| 3 | Item 3: View As toggle frontend | Item 2 | 2–3 |
| 4 | Item 4: Dashboard cards | Items 1 + 2 + 3 (for testing) | 2–3 |
| 5 | Item 5: Sortable headers — macro + first table | None | 1–1.5 |
| 6 | Item 5 (cont.): Apply to ALL remaining tables | Step 5 | 3–5 |

### Suggested Session Plan

**Session 1 (~4–5 hrs):** Item 1 (Flatten Sidebar) + Item 2 (Developer Role Backend). Commit after each.

**Session 2 (~4–5 hrs):** Item 3 (View As Frontend) + Item 4 (Dashboard Cards). Commit after each.

**Session 3 (~3–5 hrs):** Item 5 (Sortable Headers — macro + rollout to all tables). Commit per table.

---

## Global Pre-Flight

Before starting ANY item:

- [ ] `git status` is clean
- [ ] Current `CLAUDE.md` has been read — note version and project state
- [ ] Record current test count: `pytest --tb=short -q 2>&1 | tail -5`
- [ ] App starts without errors and is accessible at `http://localhost:8000`
- [ ] Docker services are running (if applicable)
- [ ] Create a feature branch for the item being worked on

---

## Global Scope Boundaries

These are non-negotiable constraints from the Hub:

- ❌ **DO NOT** change URL routing structure — sidebar changes are visual only
- ❌ **DO NOT** create new database models — use existing tables/services
- ❌ **DO NOT** implement client-side JavaScript sorting — use server-side HTMX
- ❌ **DO NOT** add Developer role to production seed data
- ❌ **DO NOT** refactor the permission system — add to it minimally
- ❌ **DO NOT** redesign the dashboard layout beyond the card changes described

---

# Item 1: Flatten Operations Sidebar Menu

**Branch:** `feature/flatten-sidebar`
**Estimated Effort:** 1–2 hours
**Prerequisites:** None

## Context

The sidebar currently groups SALTing, Benevolence, and Grievances under a "Union Operations" section header. This grouping is an artificial organizational container — RBAC is the real access control mechanism. Flattening the sidebar makes it role-driven rather than category-driven.

**This is a sidebar-only visual change. Do NOT change URL routing structure.**

## 1.1: Discover Current Sidebar Structure

**Do this before writing any code. This step is mandatory.**

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

**Record your findings. You'll need them.**

## 1.2: Remove the Operations Grouping Header

Remove the `<li class="menu-title">Union Operations</li>` header (or whatever the actual grouping element is).

If items are inside a `<details>` collapsible section, unwrap them — remove the `<details>`, `<summary>`, and any wrapper `<ul>` that exists solely for the collapsible group, but keep the individual `<li>` items and their content.

**Do NOT delete the individual sidebar items.** Only remove the grouping container.

## 1.3: Promote Items to Top Level

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

## 1.4: Apply RBAC Permission Checks

Wrap each promoted item in the appropriate permission check, using **the same pattern** already used by existing top-level items. Do not invent a new pattern.

| Item | Visible to |
|------|-----------|
| SALTing | `admin`, `officer`, `organizer`, `developer` |
| Benevolence | `admin`, `officer`, `staff`, `developer` |
| Grievances | `admin`, `officer`, `staff`, `steward`, `developer` |

If the existing sidebar items use `{% if has_permission('some_permission') %}`, then figure out what permissions map to these roles and use the same function. If they use `{% if current_user.role in ['admin', 'officer'] %}`, use that pattern. **Match what's already there.**

If a `developer` role doesn't exist in the system yet (it will be added in Item 2), include it in the role lists anyway — the check will simply never match until the role is added, which is harmless.

## 1.5: Handle Mobile Menu (If Applicable)

If Step 1.1 revealed a duplicate menu in `_navbar.html` (mobile hamburger menu), apply the exact same changes.

## 1.6: Verify

1. **Login as admin** → All sidebar items visible, no "Operations" or "Union Operations" header
2. **Login as organizer** (if test account exists) → Only SALTing visible among the three
3. **Login as staff** → Benevolence and Grievances visible, SALTing NOT visible
4. **Login as steward** (if test account exists) → Only Grievances visible
5. **Login as member** → None of the three promoted items visible
6. **Click each promoted item** → Navigates to the correct page
7. **Active-state highlighting** → The correct sidebar item highlights when on its page
8. **Responsive** → On narrow viewport / mobile, sidebar/mobile menu still works

If test accounts for specific roles don't exist, note this as a gap but verify with available accounts.

## Item 1 Anti-Patterns

- **DO NOT** change any URL routes. The URLs stay exactly as they are.
- **DO NOT** refactor the permission system. Use the existing pattern.
- **DO NOT** add new CSS classes. Use the same classes as existing top-level items.
- **DO NOT** remove actual route handlers or Python code. This is a template-only change.
- **DO NOT** leave "Union Operations" text anywhere in the sidebar, including as comments.

## Item 1 Acceptance Criteria

- [ ] No "Operations" or "Union Operations" grouping header in sidebar
- [ ] SALTing is a top-level sidebar item with correct RBAC check
- [ ] Benevolence is a top-level sidebar item with correct RBAC check
- [ ] Grievances is a top-level sidebar item with correct RBAC check
- [ ] Active-state highlighting works for each promoted item
- [ ] All existing tests still pass
- [ ] Mobile menu (if it exists) matches desktop sidebar changes
- [ ] No URL changes were made

## Item 1 File Manifest

**Modified:** `src/templates/components/_sidebar.html`, possibly `_navbar.html` (if mobile menu exists)
**Created:** None | **Deleted:** None

## Item 1 Git Commit

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

# Item 2: Developer Super Admin Role — Backend

**Branch:** `feature/developer-role`
**Estimated Effort:** 2–3 hours
**Prerequisites:** Item 1 committed and merged
**⚠️ Scope Note:** Backend role system is technically Spoke 1 territory, but assigned via Hub handoff. Proceed with implementation.

## Context

The Developer role (level 255) is an unrestricted super admin role for dev/demo environments only. It enables full access to every endpoint and UI element, plus a "View As" toggle to impersonate any business role for testing RBAC. Audit logging always records the real user identity, never the impersonated role.

**CRITICAL: The Developer role must NEVER be seeded in production data. Dev and demo seed data only.**

## 2.1: Discover the Role System

**Mandatory. Read every file involved in the role system before writing any code.**

```bash
# Find the role definition
grep -rn "role" src/models/ --include="*.py" -l
grep -rn "ROLE_LEVELS\|role_level\|RoleEnum\|UserRole" src/ --include="*.py" -l

# Find permission check functions
grep -rn "has_permission\|check_permission\|require_role\|role_required" src/ --include="*.py" -l

# Find hardcoded admin checks
grep -rn "role == .admin.\|role == \"admin\"\|== 'admin'\|== \"admin\"" src/ --include="*.py"
grep -rn "role_level >= 100" src/ --include="*.py"

# Find the auth middleware
grep -rn "middleware\|get_current_user\|authenticate" src/ --include="*.py" -l

# Find seed data scripts
find . -name "seed*.py" -o -name "*seed*" -o -name "fixtures*" | head -20
grep -rn "seed\|populate\|initial_data" src/ --include="*.py" -l

# Find session management
grep -rn "session\|cookie\|SessionMiddleware" src/ --include="*.py" -l
```

Read every file these searches turn up. Document:

1. **Role definition location** — where is the enum/model? What are the current roles and levels?
2. **Permission check function(s)** — what's the function signature? How does it evaluate permissions?
3. **Hardcoded admin checks** — list every file:line that checks for admin specifically
4. **Auth middleware** — how does the current user get attached to the request?
5. **Seed data location** — where are test/demo users created?
6. **Session infrastructure** — is `SessionMiddleware` (or equivalent) already configured? What session backend is used?

## 2.2: Add Developer Role to the Role System

Locate the role enum/model and add:

```python
DEVELOPER = "developer"  # Level 255
```

Update the role hierarchy/level mapping:

```python
ROLE_LEVELS = {
    # ... existing roles ...
    "developer": 255,  # NEW — dev/demo only, above all business roles
}
```

**Match the existing pattern exactly.** If roles are defined as an Enum class, add to the Enum. If they're a dict, add to the dict. If there's a database table, add the row.

## 2.3: Update Permission Checks

All permission check functions must recognize level 255 as unrestricted. Add a developer bypass as the first check in every permission function:

```python
# Pseudocode — adapt to actual function signature
def has_permission(user, permission):
    if user.role == "developer":
        return True  # Unrestricted access
    # ... existing permission logic ...
```

Then scan for and update every hardcoded admin check:

```bash
grep -rn "role == .admin.\|== 'admin'\|== \"admin\"" src/ --include="*.py"
grep -rn "role_level >= 100" src/ --include="*.py"
```

Each must also include `or role == 'developer'` or equivalent. If the centralized `has_permission()` function handles the bypass, these individual checks might already work — but **verify explicitly** by reading each one.

## 2.4: Add View As Session Middleware

Create middleware that:
1. Checks if the current user's role is `developer`
2. Reads a `viewing_as` value from the session
3. If `viewing_as` is set, injects it into the request context
4. Audit logging always uses the **real** user identity, never the impersonated role

```python
# Pseudocode — adapt to actual middleware pattern
async def view_as_middleware(request, call_next):
    if request.user and request.user.role == "developer":
        viewing_as = request.session.get("viewing_as", None)
        if viewing_as:
            request.state.effective_role = viewing_as
            request.state.is_impersonating = True
            request.state.viewing_as = viewing_as
        else:
            request.state.effective_role = "developer"
            request.state.is_impersonating = False
            request.state.viewing_as = None
    else:
        request.state.effective_role = getattr(request.user, 'role', None)
        request.state.is_impersonating = False
        request.state.viewing_as = None
    response = await call_next(request)
    return response
```

**Pre-requisite check:** If `SessionMiddleware` is not already configured, add it:

```python
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)
```

Add `SESSION_SECRET` to `.env.template` if it doesn't exist.

**Order matters:** The View As middleware must run **after** authentication middleware (so `request.user` exists). In Starlette/FastAPI, middleware runs in reverse registration order.

### Update Permission Checks to Use Effective Role

Permission checks should read from `effective_role` when evaluating **UI visibility and page access**, but NOT when logging audit events.

**Approach A (Recommended):** Update the permission function to read `effective_role`:

```python
def has_permission(request_or_user, permission):
    effective_role = getattr(getattr(request_or_user, 'state', None), 'effective_role', None)
    if effective_role:
        role = effective_role
    else:
        role = request_or_user.role

    # Developer (real, not impersonated) bypasses everything
    if role == "developer" and not getattr(request_or_user.state, 'is_impersonating', False):
        return True

    # Normal permission logic using role
    ...
```

**Approach B:** Update the template context to pass `effective_role` so templates can use `{% if effective_role in [...] %}`.

**Discover which approach fits the codebase** by reading how templates currently access user role info.

## 2.5: Add View As API Endpoints

Create a new router for developer-only endpoints.

**File:** `src/routers/dev_router.py` (or similar — match existing router file naming)

```
POST /api/v1/dev/view-as
Body: {"role": "organizer"} or {"role": null}
Response: 200 {"status": "ok", "viewing_as": "organizer"}
Guard: developer role only (403 for everyone else)

DELETE /api/v1/dev/view-as
Response: 200 {"status": "ok", "viewing_as": null}
Guard: developer role only
```

Implementation requirements:

1. **Guard with real role check** — use `request.user.role`, NOT `request.state.effective_role`
2. **Validate the target role** — only allow valid business roles (admin, officer, staff, organizer, instructor, steward, member, applicant). Reject "developer" as a View As target.
3. **Set/clear session value** — `request.session['viewing_as'] = role` or `del request.session['viewing_as']`
4. **Return simple JSON response**
5. **Non-developer users get 403** — hard 403, no information leakage

Register the router in `src/main.py`:

```python
from src.routers.dev_router import router as dev_router
app.include_router(dev_router, prefix="/api/v1/dev", tags=["developer"])
```

## 2.6: Update Seed Data

Add developer users to the seed scripts.

**Dev seed data:**
```python
{
    "email": "dev@ibew46.dev",
    "password": "dev-password-change-me",  # Use whatever password hashing the codebase uses
    "first_name": "Developer",
    "last_name": "Admin",
    "role": "developer",
    "is_active": True,
}
```

**Demo seed data** (if separate):
```python
{
    "email": "demo_dev@ibew46.demo",
    "password": "demo-dev-password",
    "first_name": "Dev",
    "last_name": "User",
    "role": "developer",
    "is_active": True,
}
```

**CRITICAL: Do NOT add a developer user to any production seed data.** If there's a production seed script or a conditional check like `if environment == 'production'`, the developer user must be excluded.

## 2.7: Write Tests

Create tests matching existing test patterns. File location should match the project's test organization.

**Required tests (minimum 8–12):**

```python
# Role system tests
def test_developer_role_exists():
    """Developer role is defined with level 255."""

def test_developer_role_has_highest_level():
    """Developer level (255) exceeds admin level (100)."""

def test_developer_bypasses_all_permissions():
    """Developer role passes every permission check."""

# View As endpoint tests
def test_view_as_set_role(developer_client):
    """POST /api/v1/dev/view-as sets viewing_as in session."""
    response = developer_client.post("/api/v1/dev/view-as", json={"role": "organizer"})
    assert response.status_code == 200

def test_view_as_clear_role(developer_client):
    """DELETE /api/v1/dev/view-as clears viewing_as from session."""
    response = developer_client.delete("/api/v1/dev/view-as")
    assert response.status_code == 200

def test_view_as_rejects_non_developer(admin_client):
    """Non-developer roles get 403 on View As endpoints."""
    response = admin_client.post("/api/v1/dev/view-as", json={"role": "member"})
    assert response.status_code == 403

def test_view_as_rejects_invalid_role(developer_client):
    """View As rejects invalid role names."""
    response = developer_client.post("/api/v1/dev/view-as", json={"role": "superuser"})
    assert response.status_code in [400, 422]

def test_view_as_rejects_developer_target(developer_client):
    """Cannot View As 'developer' — that's circular."""
    response = developer_client.post("/api/v1/dev/view-as", json={"role": "developer"})
    assert response.status_code in [400, 422]

# Middleware tests
def test_effective_role_default_is_real_role():
    """Without View As, effective_role equals the user's actual role."""

def test_effective_role_reflects_impersonation():
    """With View As set, effective_role matches the impersonated role."""

def test_audit_log_records_real_user_during_impersonation():
    """Audit events record the real developer user, not the impersonated role."""
```

Add `developer_user` and `developer_client` fixtures to `conftest.py`, following the same pattern as existing user/client fixtures.

## Item 2 Anti-Patterns

- **DO NOT** modify the User model's `role` field during impersonation. The session holds `viewing_as`; the user record is untouched.
- **DO NOT** create a separate "developer" database table. Developer is just another role value.
- **DO NOT** add developer users to production seed data.
- **DO NOT** skip the early-return optimization in permission checks — checking level 255 against every rule is wasteful.
- **DO NOT** log the impersonated role in audit events. Always log `request.user` (real identity).
- **DO NOT** allow View As to target "developer" — that's circular.
- **DO NOT** forget to validate that the target role in View As is a real role.

## Item 2 Acceptance Criteria

- [ ] Developer role exists in the role system with level 255
- [ ] Developer role passes all permission checks in the codebase
- [ ] `POST /api/v1/dev/view-as` sets session correctly
- [ ] `DELETE /api/v1/dev/view-as` clears session correctly
- [ ] Non-developer roles get 403 on `/api/v1/dev/view-as`
- [ ] Invalid/missing roles rejected with 400/422
- [ ] Audit logs record real user identity during impersonation
- [ ] Dev seed data includes developer user
- [ ] Production seed data does NOT include developer user
- [ ] Session middleware correctly sets `effective_role` and `is_impersonating`
- [ ] All existing tests still pass
- [ ] New tests written and passing (8–12 minimum)

## Item 2 File Manifest

**Created:**
- `src/middleware/view_as.py` (or integrated into existing middleware — match pattern)
- `src/routers/dev_router.py`
- `tests/test_developer_role.py` (or wherever test pattern dictates)

**Modified:**
- Role definition file (model/enum — location found in Step 2.1)
- Permission check function(s) — add developer bypass
- `src/main.py` — register dev_router, add session middleware if missing
- Seed data script(s) — add developer user
- `conftest.py` — add `developer_user` and `developer_client` fixtures
- `.env.template` — add `SESSION_SECRET` if session middleware was added

## Item 2 Git Commit

```
feat(auth): add Developer super admin role (level 255) with View As

- Add developer role to role system at level 255
- Developer bypasses all permission checks
- Add View As API endpoints (POST/DELETE /api/v1/dev/view-as)
- Add session middleware for effective role impersonation
- Audit logs always record real user identity
- Add developer user to dev/demo seed data (NOT production)
- Add comprehensive tests for role, endpoints, and impersonation
- Implements ADR-019
- Spoke 3: Infrastructure (via Hub handoff)
```

---

# Item 3: View As Toggle — Frontend

**Branch:** `feature/view-as-frontend`
**Estimated Effort:** 2–3 hours
**Prerequisites:** Item 2 (Developer Role Backend) committed and merged

## Context

The backend for the Developer role and View As API is already in place. This item adds the UI:
1. A "View As" dropdown in the top navbar, visible only to developer role users
2. A persistent warning banner when impersonation is active
3. Updated template permission checks to use `effective_role`

## 3.1: Discover Current Navbar & Template Context

**Mandatory discovery before writing code.**

```bash
# Read the navbar template
cat src/templates/components/_navbar.html

# Read the base template (where the banner will go)
cat src/templates/base.html

# Check how the template gets user info
grep -rn "current_user\|request.user\|effective_role" src/templates/ --include="*.html"
grep -rn "TemplateResponse\|template_context\|context" src/routers/ --include="*.py" | head -30

# Check if Alpine.js is loaded (for dropdown behavior)
grep -rn "alpine\|x-data\|x-show" src/templates/ --include="*.html" | head -10

# Check how DaisyUI dropdowns are used elsewhere
grep -rn "dropdown" src/templates/ --include="*.html" | head -10

# Check if the template context already includes effective_role
grep -rn "effective_role\|is_impersonating\|viewing_as" src/ --include="*.py"
```

Document:
1. **Navbar structure** — where do action items (user menu, logout) live?
2. **Template context** — how does `current_user` get to templates? Via middleware, dependency injection, or template globals?
3. **Dropdown pattern** — DaisyUI native (tabindex/focus), Alpine.js, or custom?
4. **Template context variables** — are `effective_role`, `is_impersonating`, `viewing_as` already available?

### Ensure Template Context Has Required Variables

If `effective_role`, `is_impersonating`, and `viewing_as` aren't already in the template context, add them. This depends on how the codebase passes context:

- **If using Jinja2 globals or context processors:** Add the variables to the global context function
- **If using a dependency that builds context:** Add them there
- **If each route passes context explicitly:** You'll need to add them to every `TemplateResponse` call (tedious but necessary)

## 3.2: Add the View As Dropdown to Navbar

Add a dropdown to the top navbar, visible ONLY to developer role. Use `current_user.role` (real role), NOT `effective_role`.

```html
{% if current_user.role == 'developer' %}
<div class="dropdown dropdown-end">
    <label tabindex="0" class="btn btn-sm btn-ghost gap-1">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
        {% if viewing_as %}
            Viewing as: {{ viewing_as | title }}
        {% else %}
            View As
        {% endif %}
    </label>
    <ul tabindex="0" class="dropdown-content z-[50] menu p-2 shadow bg-base-100 rounded-box w-52">
        <li><a hx-post="/api/v1/dev/view-as" hx-vals='{"role": null}' hx-swap="none"
               hx-on::after-request="window.location.reload()">Developer (Default)</a></li>
        <li class="menu-title"><span>Business Roles</span></li>
        <li><a hx-post="/api/v1/dev/view-as" hx-vals='{"role": "admin"}' hx-swap="none"
               hx-on::after-request="window.location.reload()">Admin</a></li>
        <li><a hx-post="/api/v1/dev/view-as" hx-vals='{"role": "officer"}' hx-swap="none"
               hx-on::after-request="window.location.reload()">Officer</a></li>
        <li><a hx-post="/api/v1/dev/view-as" hx-vals='{"role": "staff"}' hx-swap="none"
               hx-on::after-request="window.location.reload()">Staff</a></li>
        <li><a hx-post="/api/v1/dev/view-as" hx-vals='{"role": "organizer"}' hx-swap="none"
               hx-on::after-request="window.location.reload()">Organizer</a></li>
        <li><a hx-post="/api/v1/dev/view-as" hx-vals='{"role": "instructor"}' hx-swap="none"
               hx-on::after-request="window.location.reload()">Instructor</a></li>
        <li><a hx-post="/api/v1/dev/view-as" hx-vals='{"role": "steward"}' hx-swap="none"
               hx-on::after-request="window.location.reload()">Steward</a></li>
        <li><a hx-post="/api/v1/dev/view-as" hx-vals='{"role": "member"}' hx-swap="none"
               hx-on::after-request="window.location.reload()">Member</a></li>
        <li><a hx-post="/api/v1/dev/view-as" hx-vals='{"role": "applicant"}' hx-swap="none"
               hx-on::after-request="window.location.reload()">Applicant</a></li>
    </ul>
</div>
{% endif %}
```

**Adaptation notes:**
- If the codebase uses Alpine.js for dropdowns, add `x-data="{ open: false }"` and `@click="open = !open"` / `x-show="open"` / `@click.outside="open = false"`. If it uses DaisyUI's native `tabindex` pattern, use that instead. **Match existing dropdown patterns.**
- If `hx-on::after-request` doesn't work in the HTMX version used, fall back to `onclick="setTimeout(() => location.reload(), 200)"` or whatever fire-and-reload pattern the codebase uses.
- **Placement:** Near the user menu / logout button in the navbar's right section.

## 3.3: Add the Impersonation Warning Banner

In `base.html`, immediately after the navbar and before the main content area:

```html
{% if is_impersonating and viewing_as %}
<div class="alert alert-warning rounded-none flex justify-between items-center py-2 px-4 sticky top-[64px] z-40">
    <div class="flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <span>
            <strong>Developer View:</strong> Viewing as <strong>{{ viewing_as | title }}</strong> —
            Audit logs still record your real identity.
        </span>
    </div>
    <button class="btn btn-sm btn-ghost"
            hx-delete="/api/v1/dev/view-as"
            hx-swap="none"
            hx-on::after-request="window.location.reload()">
        ✕ Exit View As
    </button>
</div>
{% endif %}
```

**Adaptation notes:**
- The `top-[64px]` value must match the actual navbar height. Measure it in browser devtools. If it's 56px, 72px, etc. — use the real value.
- `z-40` should be below navbar z-index but above page content.
- If the banner causes sticky header position to shift for tables (Item 5), that's expected — Item 5 will account for it.

## 3.4: Update Template Permission Checks

**This is the most important and most tedious step.**

Every template permission check must use `effective_role` instead of `current_user.role` (except the View As dropdown visibility check in Step 3.2, which must always use `current_user.role`).

```bash
# Find all permission checks in templates
grep -rn "current_user.role\|has_permission\|user.role" src/templates/ --include="*.html"
```

For each occurrence:

```html
<!-- Before -->
{% if current_user.role in ['admin', 'officer'] %}

<!-- After -->
{% if effective_role in ['admin', 'officer'] %}
```

If `has_permission()` was updated in Item 2 to use `effective_role` from `request.state`, then template calls to `has_permission()` should already work correctly. **Verify by testing.**

**The ONE exception:** The View As dropdown visibility check must stay as `current_user.role == 'developer'`.

**Keep count of how many checks you update.** This is your regression surface.

## 3.5: Verify

### Developer — No Impersonation
1. Login as `dev@ibew46.dev` → View As dropdown visible, no banner, all items visible

### Developer → Admin
1. Select "Admin" → Banner appears, sidebar shows admin-level items

### Developer → Organizer
1. Select "Organizer" → Sidebar shows ONLY SALTing + limited items

### Developer → Staff
1. Select "Staff" → Sidebar shows Members, Dues, Grievances, Referral, Benevolence; SALTing NOT visible

### Developer → Applicant
1. Select "Applicant" → Sidebar shows minimal items, most pages restricted

### Exit Impersonation
1. Click "Exit View As" → Banner disappears, full developer access restored

### Non-Developer Cannot See Dropdown
1. Login as admin → View As dropdown NOT in the DOM (inspect element — completely absent, not just hidden)

### Audit Trail
1. While impersonating, perform a logged action → Audit log shows real developer user, NOT impersonated role

## Item 3 Anti-Patterns

- **DO NOT** use `effective_role` for the View As dropdown visibility — always use `current_user.role == 'developer'`
- **DO NOT** hide the dropdown with CSS for non-developers — use `{% if %}` so it's not in the DOM
- **DO NOT** forget the banner in `base.html` — it must appear on every page
- **DO NOT** use JavaScript to toggle sidebar items — page reload ensures server-side checks are respected
- **DO NOT** cache the effective role in JavaScript — always rely on server-side session

## Item 3 Acceptance Criteria

- [ ] View As dropdown visible in navbar for developer only
- [ ] View As dropdown NOT in DOM for non-developer roles
- [ ] Selecting a role → page reloads with impersonated role's view
- [ ] Warning banner appears during impersonation with correct role name
- [ ] "Exit View As" button works
- [ ] Sidebar items change to match impersonated role's permissions
- [ ] Page access restrictions match impersonated role
- [ ] Audit logs record real developer identity during impersonation
- [ ] All template permission checks use `effective_role` (except View As dropdown)
- [ ] All existing tests still pass

## Item 3 File Manifest

**Modified:**
- `src/templates/components/_navbar.html` — View As dropdown
- `src/templates/base.html` — impersonation warning banner
- `src/templates/components/_sidebar.html` — update permission checks to `effective_role`
- All other templates with permission checks — update to `effective_role`
- Template context helper/middleware (if needed) — add `effective_role`, `is_impersonating`, `viewing_as`

**Created:** None (unless a new partial is warranted for the banner)

## Item 3 Git Commit

```
feat(ui): add View As toggle for developer role impersonation

- Add View As dropdown to navbar (developer-only)
- Add impersonation warning banner to base template
- Update all template permission checks to use effective_role
- Page reloads on role switch for server-side consistency
- Spoke 3: Infrastructure (Cross-Cutting UI)
```

---

# Item 4: Replace Dashboard Cards

**Branch:** `feature/dashboard-cards`
**Estimated Effort:** 2–3 hours
**Prerequisites:** Items 1 + 2 + 3 committed (developer role needed for testing RBAC card visibility)
**⚠️ Scope Note:** Dashboard template layout belongs to Spoke 3. Service methods that query domain-specific data arguably belong to domain Spokes, but the Hub assigned all of it here. Queries stay in the DashboardService (aggregation layer), not domain-specific services.

## Context

The dashboard goes from 4 cards to 6 cards:
- ~~Active Members~~ → **REMOVE**
- **Open Dispatch Requests** (NEW)
- **Members on Book** (NEW)
- **Upcoming Expirations** (NEW)
- Active Students (KEEP)
- Pending Grievances (KEEP)
- Dues MTD (KEEP)

## 4.1: Discover Current Dashboard Implementation

**Mandatory. Read everything before writing anything.**

```bash
# Find dashboard template
find src/templates -name "*dashboard*" -o -name "*index*" | head -10
cat src/templates/dashboard/index.html  # or wherever it is

# Find dashboard route handler
grep -rn "dashboard\|@.*route.*'/'" src/routers/ --include="*.py"

# Find dashboard service
grep -rn "DashboardService\|dashboard_service\|get_dashboard\|get_stats" src/services/ --include="*.py" -l
cat src/services/dashboard_service.py  # or equivalent

# Find the models we need to query
grep -rn "labor_request\|LaborRequest\|dispatch_request\|DispatchRequest" src/models/ --include="*.py" -l
grep -rn "book_registration\|BookRegistration\|referral_registration" src/models/ --include="*.py" -l
grep -rn "certification\|Certification\|expir" src/models/ --include="*.py" -l

# Understand the current card HTML pattern
grep -A 20 "Active Members\|stat\|card" src/templates/dashboard/index.html | head -60

# Check what data the route passes to the template
grep -rn "def.*dashboard\|async def.*dashboard" src/routers/ --include="*.py" -A 30
```

Document:
1. **Dashboard template location** and current HTML structure for stat cards
2. **Dashboard service** — class name, method names, how stats are currently queried
3. **Route handler** — how data flows from service → route → template
4. **Card HTML pattern** — what DaisyUI classes are used? `card`, `stat`, custom?
5. **Available models** — do `LaborRequest`, `BookRegistration`, and `Certification` models exist? What are their actual names and status fields?
6. **Current card RBAC** — are existing cards wrapped in permission checks, or does everyone see all cards?

### Critical Discovery: Data Availability

For each new card, verify the data source exists:

```bash
# Open Dispatch Requests
grep -rn "class.*LaborRequest\|class.*DispatchRequest" src/models/ --include="*.py"
grep -rn "status.*open\|status.*pending" src/models/ --include="*.py"

# Members on Book
grep -rn "class.*BookRegistration\|class.*Registration" src/models/ --include="*.py"
grep -rn "status.*active" src/models/ --include="*.py" | grep -i "book\|registration\|referral"

# Upcoming Expirations
grep -rn "class.*Certification\|expir" src/models/ --include="*.py"
```

**If any model/table doesn't exist**, document this as a blocker. Stub the card with `0` and a code comment: `# TODO: Implement when [Model] is created (see Spoke [N])`. Do NOT create new models — that's out of scope.

## 4.2: Add Dashboard Service Methods

Add three new methods to the dashboard service (or create one if none exists). **Match existing code style exactly.**

```python
def get_open_dispatch_count(self, db: Session) -> int:
    """Count labor requests with open/pending status."""
    # Use actual model name and status field values from discovery
    return db.query(LaborRequest).filter(
        LaborRequest.status.in_(['open', 'pending'])
    ).count()

def get_members_on_book_count(self, db: Session) -> int:
    """Count active book registrations across all books."""
    return db.query(BookRegistration).filter(
        BookRegistration.status == 'active'
    ).count()

def get_upcoming_expirations_count(self, db: Session, days: int = 30) -> int:
    """Count certifications expiring within N days."""
    # If Certification model doesn't exist, stub:
    # return 0  # TODO: Implement when Certification model is created
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() + timedelta(days=days)
    return db.query(Certification).filter(
        Certification.expiration_date.between(datetime.utcnow(), cutoff)
    ).count()
```

**Adapt model names, field names, and status values to match what actually exists in the codebase.**

For any model that doesn't exist yet, create a stub method:

```python
def get_upcoming_expirations_count(self, db: Session, days: int = 30) -> int:
    """Stub: Returns 0 until Certification model is created (Spoke 1/2)."""
    return 0
```

## 4.3: Update the Dashboard Route Handler

Add calls to the new service methods and pass results to the template:

```python
# Add to existing dashboard route handler
open_dispatch_count = dashboard_service.get_open_dispatch_count(db)
members_on_book_count = dashboard_service.get_members_on_book_count(db)
upcoming_expirations_count = dashboard_service.get_upcoming_expirations_count(db)

# Add to existing context dict
context.update({
    "open_dispatch_count": open_dispatch_count,
    "members_on_book_count": members_on_book_count,
    "upcoming_expirations_count": upcoming_expirations_count,
})
```

**Match the existing pattern** for how the route calls service methods and passes data.

## 4.4: Update the Dashboard Template

### Remove Active Members Card

Delete the "Active Members" card entirely — both HTML and template logic.

### Create the New Card Layout

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

    {# Row 1: New operational cards #}
    {% if effective_role in ['admin', 'officer', 'staff', 'developer'] %}
    <div class="stat bg-base-100 shadow rounded-box p-4">
        <div class="stat-title">Open Dispatch Requests</div>
        <div class="stat-value">{{ open_dispatch_count }}</div>
        <div class="stat-desc">Awaiting dispatch</div>
    </div>
    {% endif %}

    {% if effective_role in ['admin', 'officer', 'staff', 'developer'] %}
    <div class="stat bg-base-100 shadow rounded-box p-4">
        <div class="stat-title">Members on Book</div>
        <div class="stat-value">{{ members_on_book_count }}</div>
        <div class="stat-desc">Active registrations</div>
    </div>
    {% endif %}

    {% if effective_role in ['admin', 'officer', 'staff', 'instructor', 'developer'] %}
    <div class="stat bg-base-100 shadow rounded-box p-4">
        <div class="stat-title">Upcoming Expirations</div>
        <div class="stat-value text-warning">{{ upcoming_expirations_count }}</div>
        <div class="stat-desc">Expiring within 30 days</div>
    </div>
    {% endif %}

    {# Row 2: Existing cards (KEEP existing markup, just add RBAC wrappers) #}
    {% if effective_role in ['admin', 'officer', 'staff', 'instructor', 'developer'] %}
    {# Active Students — keep existing #}
    {% endif %}

    {% if effective_role in ['admin', 'officer', 'staff', 'developer'] %}
    {# Pending Grievances — keep existing #}
    {% endif %}

    {% if effective_role in ['admin', 'officer', 'developer'] %}
    {# Dues MTD — keep existing #}
    {% endif %}
</div>
```

**CRITICAL: Match the existing card HTML pattern.** If existing cards use `<div class="card">` instead of `<div class="stat">`, follow their pattern. The above is a template — adapt classes, structure, and icons to match.

### Card RBAC Matrix

| Card | Visible to |
|------|-----------|
| Open Dispatch Requests | `admin`, `officer`, `staff`, `developer` |
| Members on Book | `admin`, `officer`, `staff`, `developer` |
| Upcoming Expirations | `admin`, `officer`, `staff`, `instructor`, `developer` |
| Active Students | `admin`, `officer`, `staff`, `instructor`, `developer` |
| Pending Grievances | `admin`, `officer`, `staff`, `developer` |
| Dues MTD | `admin`, `officer`, `developer` |

Use `effective_role` (not `current_user.role`) so View As impersonation works.

### Fix Subtitle Issues

If "Active Students" shows "+2690 this month" (seed data artifact), fix the subtitle to either:
- "In current cohorts"
- A real query of `created_at` within the current calendar month

## 4.5: Write Tests

```python
# Service method tests
def test_get_open_dispatch_count(db_session, dashboard_service):
    """Open dispatch count returns requests with open/pending status."""

def test_get_members_on_book_count(db_session, dashboard_service):
    """Members on book count returns active registrations."""

def test_get_upcoming_expirations_count(db_session, dashboard_service):
    """Upcoming expirations count returns certs expiring within 30 days."""

def test_get_upcoming_expirations_excludes_past(db_session, dashboard_service):
    """Already-expired certifications are not counted."""

def test_get_upcoming_expirations_excludes_far_future(db_session, dashboard_service):
    """Certifications expiring beyond 30 days are not counted."""

# Dashboard route tests
def test_dashboard_loads_for_admin(admin_client):
    """Dashboard loads successfully for admin role."""

def test_dashboard_contains_new_cards(admin_client):
    """Dashboard HTML contains the new card titles."""

def test_dashboard_no_active_members_card(admin_client):
    """Active Members card has been removed."""
    response = admin_client.get("/")
    assert "Active Members" not in response.text

def test_dashboard_card_rbac_organizer(organizer_client):
    """Organizer should not see dispatch or grievance cards."""
```

For stubbed methods, test that they return 0:

```python
def test_stubbed_expirations_returns_zero(db_session, dashboard_service):
    """Stubbed method returns 0 until Certification model exists."""
    assert dashboard_service.get_upcoming_expirations_count(db_session) == 0
```

## 4.6: Verify

1. **Login as developer (no impersonation)** → All 6 cards visible, correct counts
2. **View As Admin** → All 6 cards visible
3. **View As Staff** → 5 cards visible (Dues MTD hidden)
4. **View As Instructor** → 2 cards visible (Active Students + Upcoming Expirations)
5. **View As Organizer** → 0 or minimal cards
6. **View As Member** → 0 cards (or minimum)
7. **Responsive layout** → 3 cols desktop, 2 tablet, 1 mobile
8. **No "Active Members"** → Phrase should not appear anywhere on dashboard
9. **Card values** → Real numbers (or 0 if no data). No errors, no "undefined", no NaN.

## Item 4 Anti-Patterns

- **DO NOT** create new database models — stub with 0 if model doesn't exist
- **DO NOT** remove existing card data-fetching methods — only remove the Active Members card
- **DO NOT** hardcode card counts — always query from the database
- **DO NOT** show all cards to all roles — RBAC visibility is required

## Item 4 Acceptance Criteria

- [ ] "Active Members" card completely removed from dashboard
- [ ] "Open Dispatch Requests" card displays with correct count
- [ ] "Members on Book" card displays with correct count
- [ ] "Upcoming Expirations" card displays (0 if stubbed) with warning color
- [ ] All 6 cards visible for admin/developer
- [ ] Card visibility respects RBAC matrix per role
- [ ] Responsive grid layout (3/2/1 columns)
- [ ] Existing cards (Students, Grievances, Dues) unchanged
- [ ] All existing tests still pass
- [ ] New tests written and passing

## Item 4 File Manifest

**Modified:**
- `src/services/dashboard_service.py` (or equivalent) — add new query methods
- `src/templates/dashboard/index.html` — update card grid
- Dashboard route handler — pass new data to template

**Created:**
- Tests for new dashboard service methods

## Item 4 Git Commit

```
feat(dashboard): replace Active Members card with operational cards

- Remove Active Members dashboard card
- Add Open Dispatch Requests card (with RBAC)
- Add Members on Book card (with RBAC)
- Add Upcoming Expirations card (with RBAC, stubbed if model missing)
- Update dashboard to 6-card responsive grid
- Apply role-based card visibility using effective_role
- Add tests for new dashboard service methods
- Spoke 3: Infrastructure (Cross-Cutting UI)
```

---

# Item 5: Sortable + Sticky Table Headers

**Branch:** `feature/sortable-headers`
**Estimated Effort:** 4–6 hours (1–1.5 hrs for macro + first table, 3–5 hrs for rollout)
**Prerequisites:** None (independent of other items, can run in parallel)

## Context

Every list view in UnionCore uses data tables. Users need to sort columns and keep the header visible when scrolling. This is a cross-cutting pattern: build the reusable macro once, then apply it to every existing table.

**Server-side sorting via HTMX, NOT client-side JavaScript.** This is a non-negotiable decision from the Hub handoff.

## 5.1: Discover Current Table Patterns

**Mandatory. Read everything before writing anything.**

```bash
# Find ALL templates with tables
grep -rn "<table\|<thead\|<tbody" src/templates/ --include="*.html" -l

# Read the first table you find completely — understand the pattern
# (adjust path based on what you find)
cat src/templates/operations/salting/index.html

# Check if any tables already have sorting
grep -rn "sort\|order\|hx-get.*sort" src/templates/ --include="*.html"

# Check backend for existing sort support
grep -rn "sort\|order_by\|order" src/routers/ --include="*.py" | head -20
grep -rn "order_by" src/services/ --include="*.py" | head -20

# Check for HTMX partial rendering patterns
grep -rn "hx-target\|hx-swap\|HX-Request\|is_htmx" src/ --include="*.py" | head -20

# Measure navbar height (for sticky offset)
grep -rn "navbar\|h-16\|h-14\|h-20\|64px\|56px" src/templates/ --include="*.html" | head -10

# Check for DaisyUI's built-in table-pin-rows
grep -rn "table-pin-rows\|table-pin-cols" src/templates/ --include="*.html"
```

Document:
1. **All templates with tables** — full file list (this is your rollout checklist)
2. **Table HTML pattern** — DaisyUI classes, row structure, how data is rendered
3. **Route handler pattern** — how list endpoints work, what params they accept
4. **Service layer pattern** — how queries are built, if `order_by` already exists
5. **HTMX patterns** — does the codebase already do partial rendering for tables?
6. **Navbar height** — exact pixel value for sticky positioning
7. **Impersonation banner height** — if View As banner (Item 3) is sticky, its height affects the offset
8. **Search/filter patterns** — do tables have search fields, filter dropdowns?
9. **Pagination** — is there pagination? Sort must be preserved when paginating.
10. **DaisyUI `table-pin-rows`** — does it exist? If so, it may handle sticky natively.

## 5.2: Create the Sortable Header Macro

**File:** `src/templates/components/_sortable_th.html`

```html
{#
  Sortable Table Header Macro

  Usage:
    {% from 'components/_sortable_th.html' import sortable_header %}

    <thead>
      <tr>
        {{ sortable_header('date', 'Date', current_sort, current_order) }}
        {{ sortable_header('name', 'Name', current_sort, current_order) }}
        {{ sortable_header('status', 'Status', current_sort, current_order) }}
        <th>Actions</th>  {# Non-sortable column — use plain <th> #}
      </tr>
    </thead>

  Parameters:
    column      - The backend sort field name (e.g., 'date', 'last_name', 'status')
    label       - Display text for the column header
    current_sort  - The currently active sort column (from query params)
    current_order - The current sort direction: 'asc' or 'desc'
    target_id   - (optional) HTMX target element ID, defaults to 'table-body'
    extra_params - (optional) Additional hx-include selectors to preserve filters
#}

{% macro sortable_header(column, label, current_sort, current_order, target_id='table-body', extra_params='') %}
<th class="sticky top-[NAVBAR_HEIGHT_PX] z-10 bg-base-200 cursor-pointer select-none hover:bg-base-300 transition-colors"
    hx-get="?sort={{ column }}&order={% if current_sort == column and current_order == 'asc' %}desc{% else %}asc{% endif %}"
    hx-target="#{{ target_id }}"
    hx-swap="innerHTML"
    hx-push-url="true"
    {% if extra_params %}hx-include="{{ extra_params }}"{% else %}hx-include="[name='search'], [name='filter_type'], [name='filter_status'], [name='page_size']"{% endif %}>
    <div class="flex items-center gap-1">
        {{ label }}
        {% if current_sort == column %}
            <span class="text-xs opacity-70">{% if current_order == 'asc' %}▲{% else %}▼{% endif %}</span>
        {% else %}
            <span class="text-xs opacity-20">⇅</span>
        {% endif %}
    </div>
</th>
{% endmacro %}
```

**CRITICAL ADAPTATIONS:**
- Replace `NAVBAR_HEIGHT_PX` with the actual value (e.g., `64px`). If the impersonation banner is also sticky, the offset needs to account for both.
- The `hx-include` attribute preserves search/filter/pagination state when sorting. Adjust the selector list to match whatever form inputs actually exist.
- If DaisyUI's `table-pin-rows` class already handles sticky headers, you may be able to simplify the CSS. Check if it works with the correct offset.

## 5.3: Implement on the First Table

Pick the first table (SALTing activities recommended, or whichever has the most data for testing). This is your proof-of-concept.

### 5.3a: Update the Route Handler

Add `sort` and `order` query parameters with validation:

```python
@router.get("/operations/salting")
async def list_activities(
    request: Request,
    sort: str = "date",       # Default sort column
    order: str = "desc",      # Default sort direction
    search: str = "",         # Existing search param (if any)
    # ... other existing params ...
):
    # Validate sort column against whitelist
    ALLOWED_SORT_COLUMNS = ['date', 'name', 'status', 'location']  # Adjust to actual columns
    if sort not in ALLOWED_SORT_COLUMNS:
        sort = "date"
    if order not in ("asc", "desc"):
        order = "desc"

    # Pass to service
    activities = service.get_activities(db, sort=sort, order=order, search=search)

    # HTMX partial rendering
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "operations/salting/_table_body.html",
            {"request": request, "activities": activities}
        )

    return templates.TemplateResponse(
        "operations/salting/index.html",
        {
            "request": request,
            "activities": activities,
            "current_sort": sort,
            "current_order": order,
            # ... other existing context ...
        }
    )
```

**Adapt to actual route patterns.** If the codebase doesn't already have HTMX partial rendering, this creates the pattern.

### 5.3b: Update the Service Layer

Add `order_by` support:

```python
def get_activities(self, db: Session, sort: str = "date", order: str = "desc", **kwargs):
    query = db.query(SaltingActivity)

    # ... existing filter logic ...

    sort_column = getattr(SaltingActivity, sort, None)
    if sort_column is not None:
        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

    return query.all()
```

**Adapt to actual model attributes.** Only allow known column names (validated in the route handler).

### 5.3c: Extract Table Body to Partial Template

Create a partial template for just the table rows:

**File:** `src/templates/operations/salting/_table_body.html` (adjust path)

```html
{% for activity in activities %}
<tr>
    <td>{{ activity.date }}</td>
    <td>{{ activity.name }}</td>
    <td>{{ activity.status }}</td>
    <td>{{ activity.location }}</td>
    <td>
        <a href="/operations/salting/{{ activity.id }}" class="btn btn-xs btn-ghost">View</a>
    </td>
</tr>
{% else %}
<tr>
    <td colspan="5" class="text-center text-base-content/50 py-8">No activities found.</td>
</tr>
{% endfor %}
```

### 5.3d: Update the Full Template

```html
{% from 'components/_sortable_th.html' import sortable_header %}

<table class="table table-zebra w-full">
    <thead>
        <tr>
            {{ sortable_header('date', 'Date', current_sort, current_order) }}
            {{ sortable_header('name', 'Activity Name', current_sort, current_order) }}
            {{ sortable_header('status', 'Status', current_sort, current_order) }}
            {{ sortable_header('location', 'Location', current_sort, current_order) }}
            <th class="sticky top-[NAVBAR_HEIGHT_PX] z-10 bg-base-200">Actions</th>
        </tr>
    </thead>
    <tbody id="table-body">
        {% include 'operations/salting/_table_body.html' %}
    </tbody>
</table>
```

**The `id="table-body"` on `<tbody>` is critical** — the macro's `hx-target` points to it.

## 5.4: Write Tests (First Table)

```python
def test_sort_by_date_ascending(admin_client):
    """Sorting by date ascending returns results in chronological order."""
    response = admin_client.get("/operations/salting?sort=date&order=asc")
    assert response.status_code == 200

def test_sort_by_date_descending(admin_client):
    """Sorting by date descending returns results in reverse chronological order."""

def test_sort_by_name(admin_client):
    """Sorting by name works correctly."""

def test_invalid_sort_column_falls_back_to_default(admin_client):
    """Invalid sort column silently falls back to default."""
    response = admin_client.get("/operations/salting?sort=nonexistent&order=asc")
    assert response.status_code == 200

def test_htmx_request_returns_partial(admin_client):
    """HTMX requests return partial table body, not full page."""
    response = admin_client.get(
        "/operations/salting?sort=date&order=asc",
        headers={"HX-Request": "true"}
    )
    assert response.status_code == 200
    assert "<table" not in response.text  # Partial should not contain full table
    assert "<tr" in response.text or "No activities" in response.text

def test_sort_with_search_preserves_filter(admin_client):
    """Sorting while searching preserves the search filter."""
    response = admin_client.get("/operations/salting?sort=name&order=asc&search=test")
    assert response.status_code == 200
```

## 5.5: Verify First Table

1. Navigate to the list page
2. Click "Date" header → table sorts by date ascending, ▲ appears
3. Click "Date" again → sorts descending, ▼ appears
4. Click "Name" → sorts by name ascending, ▲ on Name, ⇅ on Date
5. Scroll down → header row sticks below navbar
6. If search box exists: type a search term, then sort → search is preserved
7. Check URL → sort params appear (`?sort=name&order=asc`)
8. Click browser back → returns to previous sort state

## 5.6: Rollout to All Remaining Tables

After the first table works, apply the same pattern to **every remaining table**. The rule: if it has a `<thead>`, it gets sticky + sortable. No exceptions.

**Per table, the work is:**
1. Add `sort` and `order` query params to the route handler (with whitelist validation)
2. Add `order_by` support to the service method
3. Extract `<tbody>` into a partial template
4. Replace static `<th>` with `sortable_header` macro calls
5. Add HTMX partial rendering to the route handler
6. Write tests
7. Manual verify
8. Commit

**Tables that MUST be updated (verify against actual codebase — may not be exhaustive):**

| Priority | Table |
|----------|-------|
| ✅ Done | First table (SALTing or equivalent) |
| 2 | Members list |
| 3 | Referral Books / Registrations |
| 4 | Dispatch / Labor Requests |
| 5 | Dues Payments |
| 6 | Students list |
| 7 | Grievances list |
| 8 | Staff list |
| 9 | Benevolence applications |
| 10 | Audit log table (if implemented) |
| 11+ | Any other table found in discovery |

**If a table exists in the codebase but is not on this list, it still gets the treatment.**

**You do NOT need to finish all tables in one session.** The macro is built and proven after the first table. Commit after each table. Remaining tables can be done incrementally.

## Item 5 Anti-Patterns

- **DO NOT** implement client-side JavaScript sorting — server-side HTMX only
- **DO NOT** allow arbitrary column names in `sort` — validate against a whitelist per table
- **DO NOT** put the table inside a `<div>` with `overflow-y: auto` or `max-height` — this breaks `position: sticky`
- **DO NOT** forget to preserve search/filter state when sorting — `hx-include` must capture all active filter inputs
- **DO NOT** forget `hx-push-url="true"` — without it, browser back/forward won't work
- **DO NOT** use `hx-swap="outerHTML"` on the tbody — use `innerHTML` so `<tbody id="table-body">` stays in the DOM
- **DO NOT** duplicate row rendering logic — the partial template is the single source of truth
- **DO NOT** sort by computed/virtual columns unless handled explicitly in the service layer
- **DO NOT** forget the empty-state row (`{% else %}`) in the partial template

## Item 5 Acceptance Criteria (First Table)

- [ ] Sortable header macro created in `src/templates/components/_sortable_th.html`
- [ ] First table uses the sortable macro
- [ ] Clicking a column header sorts via HTMX
- [ ] Clicking same header reverses sort order
- [ ] Sort indicator (▲/▼) on active column, (⇅) on inactive
- [ ] Header row sticks below navbar when scrolling
- [ ] Sort params in URL via `hx-push-url`
- [ ] Browser back/forward works with sort state
- [ ] Search/filter state preserved when sorting
- [ ] HTMX returns partial content (not full page)
- [ ] Invalid sort columns fall back safely
- [ ] All existing tests still pass
- [ ] New tests written and passing

## Item 5 Acceptance Criteria (Per Additional Table)

- [ ] Route handler accepts sort/order params with validation
- [ ] Service method supports order_by
- [ ] Template uses `sortable_header` macro
- [ ] Table body extracted to partial template
- [ ] HTMX partial rendering works
- [ ] Tests written and passing

## Item 5 File Manifest (First Table)

**Created:**
- `src/templates/components/_sortable_th.html` — reusable macro
- `src/templates/[domain]/[entity]/_table_body.html` — table body partial
- `tests/test_sortable_tables.py` — tests
- `src/static/css/custom.css` — sticky styles (only if DaisyUI `table-pin-rows` doesn't suffice)

**Modified:**
- First table's list template — replace `<th>` with macro calls
- First table's route handler — add sort/order params + HTMX partial rendering
- First table's service method — add order_by support

## Item 5 Git Commits

**First commit (macro + first table):**
```
feat(ui): add sortable sticky table headers with HTMX

- Create reusable sortable_header Jinja2 macro
- Implement server-side sorting via HTMX for [first table name]
- Sticky table headers stay visible when scrolling
- Sort state preserved in URL via hx-push-url
- Search/filter state preserved when sorting
- HTMX returns partial table body for efficient re-rendering
- Spoke 3: Infrastructure (Cross-Cutting UI)
```

**Subsequent commits (per table):**
```
feat(ui): apply sortable headers to [Table Name]

- Add sort/order query params to [route name]
- Add order_by support to [service method]
- Extract table body to partial template
- Add tests for sort functionality
- Spoke 3: Infrastructure (Cross-Cutting UI)
```

---

# Session Close-Out (After Each Item)

After committing any item:

1. **Update `CLAUDE.md`** — increment version, note what changed, update test count
2. **Update `CHANGELOG.md`** — add entry under current version
3. **Update any relevant docs under `/docs/`** — especially auth/role docs, UI conventions, template patterns

---

# Cross-Spoke Handoff Notes

After completing the bundle, generate handoff notes for:

| Recipient | Topic | Why |
|-----------|-------|-----|
| **Hub** | ADR-019 creation (if it doesn't exist) | Developer role needs ADR documentation |
| **Spoke 1** | Developer role + `effective_role` pattern | New permission checks must include developer |
| **Spoke 2** | Developer role + `effective_role` pattern | Same as Spoke 1 |
| **All Spokes** | Sortable header pattern + macro usage | New tables should use the macro |
| **All Spokes** | Dashboard card data dependencies | Service changes to LaborRequest/BookRegistration/Certification status fields will break dashboard |

---

# Known Risks & Blockers

| Risk | Mitigation |
|------|-----------|
| Certification model might not exist yet | Stub the Upcoming Expirations card with 0 and TODO comment |
| Session middleware might not be configured | Item 2 instructions include adding SessionMiddleware |
| Navbar height may differ from assumed 64px | Discovery steps require measuring actual height |
| HTMX partial rendering may not be an existing pattern | Item 5 covers creating the pattern from scratch |
| Test accounts for specific roles may not exist | Note gaps, verify with available accounts |
| Impersonation banner height affects sticky offset | Item 5 macro accounts for dynamic top offset |

---

*UI Enhancement Bundle — Consolidated Claude Code Instructions*
*Spoke 3: Infrastructure*
*UnionCore v0.9.16-alpha*
*Created: February 10, 2026 | Consolidated: February 17, 2026*
