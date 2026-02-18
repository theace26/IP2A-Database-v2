# UnionCore — Week 44: View As Toggle (Frontend)
**Spoke:** Spoke 3: Infrastructure (Cross-Cutting UI)
**Phase:** UI Enhancement Bundle — Item 3B of 5
**Estimated Effort:** 2–3 hours
**Prerequisites:** Item 3A (Developer Role Backend) committed and merged, git status clean
**Source:** Hub Handoff Document (February 10, 2026) + ADR-019

---

## Context

The backend for the Developer role and View As API is already in place (Item 3A). This item adds:
1. A "View As" dropdown in the top navbar, visible only to developer role users
2. A persistent warning banner when impersonation is active
3. Updated template permission checks to use `effective_role`

---

## Pre-Flight Checklist

- [ ] `git status` is clean
- [ ] Create and checkout branch: `git checkout -b feature/view-as-frontend`
- [ ] Item 3A changes are merged and available on this branch
- [ ] App starts without errors
- [ ] Record current test count: `pytest --tb=short -q 2>&1 | tail -5`
- [ ] Confirm you can login as the developer user (`dev@ibew46.dev`)
- [ ] Confirm the View As API works: `curl -X POST http://localhost:8000/api/v1/dev/view-as -H "Content-Type: application/json" -d '{"role": "organizer"}'` (with appropriate auth cookie/header)

---

## Step 1: Discover Current Navbar & Template Context

**Mandatory discovery before writing code.**

```bash
# Read the navbar template
cat src/templates/components/_navbar.html

# Read the base template to understand layout structure
cat src/templates/base.html

# Find how template context is populated
grep -rn "TemplateResponse\|template_context\|get_context" src/ --include="*.py" | head -20

# Check what variables are available in templates
grep -rn "current_user\|effective_role\|viewing_as" src/templates/ --include="*.html"

# Check if Alpine.js is loaded and how it's used
grep -rn "x-data\|x-show\|x-bind\|alpine" src/templates/ --include="*.html" | head -10

# Check HTMX usage pattern
grep -rn "hx-post\|hx-delete\|hx-swap" src/templates/ --include="*.html" | head -10

# Check DaisyUI version and dropdown pattern
grep -rn "dropdown\|daisyui" src/templates/ --include="*.html" | head -10
```

Document:
1. **Navbar structure** — what HTML pattern does the existing navbar use?
2. **Template context** — what variables are already available? Is `current_user.role` used directly or through a function?
3. **Effective role in context** — did Item 3A add `effective_role`, `is_impersonating`, `viewing_as` to the template context? If not, you need to add them.
4. **Alpine.js pattern** — is Alpine already loaded? What version? How are interactive components structured?
5. **HTMX pattern** — how does the codebase handle HTMX requests that shouldn't swap content (like setting a session value)?
6. **DaisyUI dropdown** — what's the existing dropdown pattern? (DaisyUI has multiple dropdown implementations across versions)

---

## Step 2: Ensure Template Context Has Required Variables

The View As frontend needs these variables available in every template:

- `current_user` — the real, authenticated user object
- `effective_role` — the role being used for permission checks (equals `current_user.role` when not impersonating)
- `is_impersonating` — boolean
- `viewing_as` — the impersonated role name (or `None`)

If Item 3A set these on `request.state` but they're not in the template context, add them now.

Find where template context is assembled:

```bash
grep -rn "TemplateResponse\|Jinja2Templates\|template" src/ --include="*.py" | grep -v "test\|__pycache__"
```

**Option A: Global template context processor (preferred)**

If the codebase has a global context processor or middleware that adds variables to all templates, add the View As variables there:

```python
# Add to existing template context
context["effective_role"] = getattr(request.state, "effective_role", None)
context["is_impersonating"] = getattr(request.state, "is_impersonating", False)
context["viewing_as"] = getattr(request.state, "viewing_as", None)
```

**Option B: Per-response injection**

If each route manually builds its template context, you'll need to add these variables to a shared helper function. Do NOT add them to every route handler individually — that's unmaintainable.

---

## Step 3: Add the View As Dropdown to Navbar

In `_navbar.html` (or wherever the top navbar is defined), add a dropdown menu visible **only to developer role users**.

**CRITICAL: Use `current_user.role`, NOT `effective_role`, for the visibility check.** The View As dropdown should always be visible to developers, even when they're impersonating another role.

```html
{% if current_user.role == 'developer' %}
<div class="dropdown dropdown-end" x-data="{ open: false }">
    <label tabindex="0" class="btn btn-sm btn-ghost gap-1" @click="open = !open">
        <!-- Eye icon — use whatever icon library the project uses -->
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
    <ul tabindex="0"
        class="dropdown-content z-[50] menu p-2 shadow-lg bg-base-100 rounded-box w-52 border border-base-300"
        @click.outside="open = false"
        x-show="open"
        x-transition>
        <li>
            <a hx-post="/api/v1/dev/view-as"
               hx-vals='{"role": null}'
               hx-swap="none"
               hx-on::after-request="window.location.reload()"
               class="{% if not viewing_as %}active{% endif %}">
                Developer (Default)
            </a>
        </li>
        <li class="menu-title"><span>Business Roles</span></li>
        {% set roles = ['admin', 'officer', 'staff', 'organizer', 'instructor', 'steward', 'member', 'applicant'] %}
        {% for role in roles %}
        <li>
            <a hx-post="/api/v1/dev/view-as"
               hx-vals='{"role": "{{ role }}"}'
               hx-swap="none"
               hx-on::after-request="window.location.reload()"
               class="{% if viewing_as == role %}active{% endif %}">
                {{ role | title }}
            </a>
        </li>
        {% endfor %}
    </ul>
</div>
{% endif %}
```

**Adaptation notes:**
- Match the existing navbar's HTML structure and class patterns
- The `hx-on::after-request="window.location.reload()"` pattern sends the HTMX POST, waits for the response, then reloads the page to show the new role's view. If the codebase has a different pattern for "fire-and-reload", use that instead.
- If the project doesn't use Alpine.js for dropdowns and instead relies on DaisyUI's pure CSS dropdown (using `tabindex` and `:focus`), drop the Alpine `x-data`/`x-show` attributes and use DaisyUI's native pattern.
- The `z-[50]` ensures the dropdown renders above the impersonation banner. Adjust if needed.

**Placement:** Put the dropdown in the navbar's right-side section, near the user menu / logout button. It should be easily accessible but not confused with the regular user menu.

---

## Step 4: Add the Impersonation Warning Banner

When View As is active, show a persistent banner below the navbar warning the developer that they're viewing as a different role.

**Location:** In `base.html`, immediately after the navbar and before the main content area.

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
- The `top-[64px]` value must match the actual navbar height. Measure it: inspect the navbar in browser devtools and get the computed height in pixels. If it's 56px, 64px, 72px — use the actual value.
- The `z-40` should be below the navbar's z-index but above page content. Adjust if needed.
- If the banner causes the sticky header position to shift for tables (Item 2), that's fine — Item 2 will account for it.
- The `sticky` positioning means it stays visible when scrolling. If you prefer fixed, use `fixed` — but `sticky` is usually better because it doesn't overlap content.

---

## Step 5: Update Template Permission Checks

This is the most important and most tedious step.

Every template permission check must use `effective_role` instead of `current_user.role` (except for the View As dropdown visibility check in Step 3, which must always use `current_user.role`).

```bash
# Find all permission checks in templates
grep -rn "current_user.role\|has_permission\|user.role" src/templates/ --include="*.html"
```

**For each occurrence:**

If the check currently reads `current_user.role`:
```html
<!-- Before -->
{% if current_user.role in ['admin', 'officer'] %}

<!-- After -->
{% if effective_role in ['admin', 'officer'] %}
```

If the check uses `has_permission()` and you updated `has_permission()` in Item 3A to use `effective_role` from `request.state`, then template calls to `has_permission()` should already work correctly. **Verify this by testing.**

**The ONE exception:** The View As dropdown visibility check (Step 3) must stay as `current_user.role == 'developer'` so the developer can always access it.

**Keep count of how many checks you update.** This is your regression surface — you'll need to verify each one.

---

## Step 6: Verify

Manual testing is critical for this item. Test each scenario:

### Developer — No Impersonation
1. Login as `dev@ibew46.dev`
2. View As dropdown visible in navbar
3. No warning banner
4. All sidebar items visible
5. All pages accessible

### Developer → Admin
1. Select "Admin" from View As dropdown
2. Warning banner appears: "Viewing as Admin"
3. Sidebar shows admin-level items (all business items, no developer-only items if any exist)
4. Dashboard shows admin-appropriate cards
5. Can navigate to all admin pages

### Developer → Organizer
1. Select "Organizer" from View As
2. Banner shows "Viewing as Organizer"
3. Sidebar shows ONLY: Dashboard, SALTing, and whatever organizers can see
4. Cannot access pages organizers shouldn't see (e.g., direct URL to admin settings should show 403 or redirect)

### Developer → Staff
1. Select "Staff" from View As
2. Sidebar shows staff-level items (Members, Dues, Grievances, Referral, Benevolence)
3. SALTing NOT visible

### Developer → Applicant
1. Select "Applicant" from View As
2. Sidebar shows minimal items
3. Most pages restricted

### Exit Impersonation
1. Click "Exit View As" on the warning banner
2. Banner disappears
3. Full developer access restored

### Non-Developer Cannot See Dropdown
1. Login as admin (not developer)
2. View As dropdown NOT in the DOM (inspect element to confirm — it should be completely absent, not just hidden)

### Audit Trail
1. While impersonating as "organizer", perform an action that generates an audit log (e.g., view a record, if viewing is logged)
2. Check the audit log — it should show the developer user, NOT "organizer"

---

## Anti-Patterns to Avoid

- **DO NOT** use `effective_role` for the View As dropdown visibility check — always use `current_user.role == 'developer'` for that
- **DO NOT** hide the View As dropdown with CSS (`display: none`) for non-developers — use Jinja2 `{% if %}` so it's not in the DOM at all
- **DO NOT** forget to include the warning banner in the `base.html` template — it must appear on every page
- **DO NOT** use JavaScript to toggle sidebar items — the page reload approach ensures server-side permission checks are respected
- **DO NOT** cache the effective role in JavaScript — always rely on the server-side session and page reload
- **DO NOT** add page transition animations that interfere with the reload pattern

---

## Acceptance Criteria

- [ ] View As dropdown visible in navbar when logged in as developer
- [ ] View As dropdown NOT in DOM for non-developer roles
- [ ] Selecting a role from the dropdown → page reloads with impersonated role's view
- [ ] Warning banner appears during impersonation with correct role name
- [ ] Warning banner has working "Exit View As" button
- [ ] Sidebar items change to match impersonated role's permissions
- [ ] Page access restrictions match impersonated role
- [ ] Audit logs record real developer identity during impersonation
- [ ] All template permission checks use `effective_role` (except View As dropdown)
- [ ] All existing tests still pass
- [ ] New tests passing (if any frontend-testable components exist)

---

## File Manifest

**Modified files:**
- `src/templates/components/_navbar.html` — View As dropdown
- `src/templates/base.html` — impersonation warning banner
- `src/templates/components/_sidebar.html` — update permission checks to use `effective_role`
- All other templates with permission checks — update to `effective_role`
- Possibly template context helper/middleware — add `effective_role`, `is_impersonating`, `viewing_as` to context

**Created files:**
- None (unless a new template partial is warranted for the banner)

**Deleted files:**
- None

---

## Git Commit Message

```
feat(ui): add View As toggle for developer role impersonation

- Add View As dropdown to navbar (developer-only)
- Add impersonation warning banner to base template
- Update all template permission checks to use effective_role
- Page reloads on role switch to ensure server-side consistency
- View As dropdown uses current_user.role (always visible to devs)
- Spoke 3: Infrastructure (Cross-Cutting UI)
```

---

## Session Close-Out

After committing:

1. Update `CLAUDE.md` — note View As frontend completion, update version
2. Update `CHANGELOG.md` — add entry
3. Update any docs referencing the navbar or permission system
4. **Cross-Spoke Impact Note:** Template permission checks now use `effective_role` instead of `current_user.role`. Any new templates created by other Spokes should follow this pattern. Generate a brief handoff note for Spoke 1 and Spoke 2.

---

*Spoke 3: Infrastructure — Item 3B of UI Enhancement Bundle*
*UnionCore v0.9.16-alpha*
