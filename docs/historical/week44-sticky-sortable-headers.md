# UnionCore — Week 44: Sticky + Sortable Table Headers
**Spoke:** Spoke 3: Infrastructure (Cross-Cutting UI)
**Phase:** UI Enhancement Bundle — Item 5
**Estimated Effort:** Phase A: 15–30 min | Phase B: 30–45 min per table
**Prerequisites:** Git status clean, on a feature branch, app runs locally
**Source:** Hub Handoff Document (February 10, 2026)

> **⚠️ POST-IMPLEMENTATION CORRECTION (2026-02-18 — Bug #039):**
> The original implementation had two overflow blockers that defeated `position: sticky`:
> 1. `overflow-hidden` on card wrapper divs
> 2. `overflow-x-auto` on table wrapper divs (per CSS spec, forces `overflow-y: auto`, trapping sticky)
>
> Both were removed in commit `4608606` (2026-02-18). The live pattern is documented in
> `docs/table-sortable-rollout.md`. Do NOT add `overflow-x-auto` or `overflow-hidden`
> to any ancestor of a `table-pin-rows` table. See `docs/BUGS_LOG.md` Bug #039 for full details.

---

## Context

Every data table in UnionCore needs two things:
1. **Sticky headers** — the header row stays visible when scrolling long tables
2. **Sortable columns** — clicking a column header sorts the table via server-side HTMX

These are split into two phases because sticky headers can be applied globally with a single CSS rule, while sortable columns require per-table backend work.

**Server-side sorting via HTMX, NOT client-side JavaScript.** This is non-negotiable.

---

## Pre-Flight Checklist

- [ ] `git status` is clean
- [ ] Create and checkout branch: `git checkout -b feature/sortable-sticky-headers`
- [ ] App starts without errors
- [ ] Record current test count: `pytest --tb=short -q 2>&1 | tail -5` — note the number
- [ ] Confirm you can access the app at `http://localhost:8000`
- [ ] Read current `CLAUDE.md` for project state and version

---

# PHASE A: Global Sticky Headers (All Tables, One Change)

This phase makes every table header in the app sticky. No per-table template changes required.

## A.1: Discover the Navbar Height and Existing Styles

**Do this before writing any CSS.**

```bash
# Find the base template and layout
cat src/templates/base.html

# Find existing custom CSS
find src/static -name "*.css" -not -path "*/node_modules/*" | head -10
cat src/static/css/custom.css 2>/dev/null || echo "No custom.css found"

# Check for Tailwind config or global styles
find . -name "tailwind.config*" -o -name "globals.css" -o -name "app.css" | head -10

# Measure navbar height — look for height classes
grep -rn "navbar\|h-16\|h-14\|h-20\|h-12" src/templates/base.html src/templates/components/_navbar.html 2>/dev/null

# Check if DaisyUI's table-pin-rows is already used anywhere
grep -rn "table-pin-rows\|table-pin-cols" src/templates/ --include="*.html"

# Check if there's already a sticky header rule somewhere
grep -rn "sticky\|position.*sticky" src/static/ --include="*.css" 2>/dev/null
grep -rn "sticky" src/templates/ --include="*.html" | grep -i "thead\|th\|header"

# Find ALL templates with tables — this is your full inventory
grep -rn "<thead" src/templates/ --include="*.html" -l
```

Document:
1. **Navbar height** — what's the actual pixel value? DaisyUI `navbar` is typically 64px (`h-16`), but verify.
2. **Where to put global CSS** — is there a `custom.css`, `app.css`, or `<style>` block in `base.html`?
3. **DaisyUI `table-pin-rows`** — if this class exists and is supported by the installed DaisyUI version, it may handle sticky natively. Test it before writing custom CSS.
4. **Complete table inventory** — list every template file with a `<thead>`. This is your Phase B rollout checklist.
5. **Any existing sticky behavior** — the screenshot shows the Students table already has a sticky bar at the top. Understand what's causing it so you don't conflict.

## A.2: Check if DaisyUI `table-pin-rows` Works

DaisyUI 4.x has a `table-pin-rows` utility class that makes `<thead>` sticky. Before writing custom CSS, test this:

1. Open any table template (e.g., the Students table from the screenshot)
2. Add `table-pin-rows` to the `<table>` class list:
   ```html
   <table class="table table-zebra table-pin-rows">
   ```
3. Load the page and scroll — does the header stick?
4. If yes: does it stick at the correct position (below the navbar, not at `top: 0`)?

**If `table-pin-rows` works AND positions correctly below the navbar**, use it. Add the class to every `<table>` in the app (or add it to a shared base class if one exists).

**If `table-pin-rows` sticks at `top: 0` (behind the navbar)**, you still need a CSS override to set the correct `top` value. Proceed to A.3.

**If `table-pin-rows` is not recognized** (older DaisyUI version), proceed to A.3.

## A.3: Add Global Sticky Header CSS

Add a single CSS rule that targets all table headers. Put this in the global stylesheet (the location found in A.1).

**If a `custom.css` or `app.css` exists:**

```css
/* ============================================
   Sticky Table Headers — Global Rule
   All <thead> <th> elements stick below the navbar
   when the user scrolls.
   ============================================ */

thead th {
    position: sticky;
    top: 64px;               /* ← REPLACE with actual navbar height from A.1 */
    z-index: 10;
    background-color: oklch(var(--b2)); /* DaisyUI base-200 background — prevents content showing through */
}

/* When impersonation banner is active, headers need extra offset.
   The banner adds ~48px. Adjust if your banner height differs. */
.impersonation-active thead th {
    top: 112px;              /* navbar (64px) + banner (~48px) — VERIFY BOTH VALUES */
}
```

**If no custom CSS file exists, create one:**

```bash
# Create the file
touch src/static/css/custom.css
```

Then add the CSS above, and link it in `base.html`:

```html
<!-- Add AFTER the DaisyUI/Tailwind stylesheet -->
<link rel="stylesheet" href="{{ url_for('static', path='css/custom.css') }}">
```

**If the project uses only Tailwind utility classes (no custom CSS files):**

Add a `<style>` block in `base.html` inside `<head>`:

```html
<style>
    thead th {
        position: sticky;
        top: 64px;
        z-index: 10;
        background-color: oklch(var(--b2));
    }
</style>
```

### Background Color Note

The `background-color` is critical — without it, table body content will show through the sticky header when scrolling. The value must match the actual header background:

- If using DaisyUI theme: `oklch(var(--b2))` for `base-200`, or `oklch(var(--b1))` for `base-100`
- If headers have a specific class like `bg-base-200`, match that color
- Check an existing table header to see what background is applied

### Impersonation Banner Offset

If the View As impersonation banner (from Item 3) is implemented and is `sticky`, the table header offset needs to account for both navbar + banner height. Two approaches:

**Approach 1: CSS class toggle (recommended)**

In `base.html`, add a class to `<body>` when impersonating:

```html
<body class="{% if is_impersonating %}impersonation-active{% endif %}">
```

Then use the `.impersonation-active thead th` rule above.

**Approach 2: CSS custom property**

```html
<style>
    :root {
        --header-offset: 64px;  /* navbar only */
    }
    body.impersonation-active {
        --header-offset: 112px; /* navbar + banner */
    }
    thead th {
        position: sticky;
        top: var(--header-offset);
        z-index: 10;
        background-color: oklch(var(--b2));
    }
</style>
```

**If the impersonation banner is NOT yet implemented (Item 3 not done yet)**, skip the banner offset for now. Use the simple navbar-only rule. Add a code comment:

```css
/* TODO: When impersonation banner (Item 3) is implemented,
   add offset for banner height. See Phase A.3 in instruction doc. */
```

## A.4: Verify Sticky Headers Globally

Test across multiple table pages:

1. **Navigate to Students list** (shown in screenshot) → header sticks below navbar when scrolling
2. **Navigate to Members list** → same behavior
3. **Navigate to every other table page** from your inventory (A.1) → all sticky
4. **Header background** → no content bleeding through the header when scrolling
5. **z-index** → header renders above table body rows, below navbar and any modals/dropdowns
6. **No horizontal scroll issues** → if tables are wider than viewport, sticky still works
7. **Mobile responsive** → on small screens, sticky still behaves correctly

**If any table's header doesn't stick**, check:
- Does that table use a different `<table>` structure (e.g., `<div>` tables)?
- Is the table inside a container with `overflow: auto` or `overflow: hidden`? This breaks `position: sticky`. The fix is to remove the overflow from the parent or move the sticky to the scrolling container.
- Is the `<thead>` missing entirely? Some tables might use `<tr>` directly. Flag these for cleanup.

## A.5: Commit Phase A

```bash
git add -A
git commit -m "feat(ui): add global sticky table headers

- Add CSS rule for sticky thead across all tables
- Headers stick below navbar when scrolling
- Background color prevents content bleed-through
- Works with all existing tables without per-table changes
- Spoke 3: Infrastructure (Cross-Cutting UI)"
```

---

# PHASE B: Sortable Column Headers (Per-Table)

This phase adds click-to-sort functionality to every table. Unlike Phase A, this requires backend changes for each table — there's no global shortcut.

## B.1: Create the Sortable Header Macro

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
        <th>Actions</th>  {# Non-sortable — use plain <th> #}
      </tr>
    </thead>

  Parameters:
    column       - Backend sort field name (e.g., 'date', 'last_name', 'status')
    label        - Display text for the column header
    current_sort - Currently active sort column (from query params)
    current_order - Current sort direction: 'asc' or 'desc'
    target_id    - (optional) HTMX target element ID, defaults to 'table-body'
#}

{% macro sortable_header(column, label, current_sort, current_order, target_id='table-body') %}
<th class="cursor-pointer select-none hover:bg-base-300 transition-colors"
    hx-get="?sort={{ column }}&order={% if current_sort == column and current_order == 'asc' %}desc{% else %}asc{% endif %}"
    hx-target="#{{ target_id }}"
    hx-swap="innerHTML"
    hx-push-url="true"
    hx-include="[name='search'], [name='filter_type'], [name='filter_status'], [name='page_size']">
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

**Key notes:**
- The `<th>` does NOT include sticky positioning — that's already handled globally by Phase A's CSS rule.
- The `hx-include` preserves search/filter state when sorting. Adjust the selector list to match whatever form input `name` attributes actually exist in the codebase. Inspect an existing table with a search box to find the correct names.
- The `hx-push-url="true"` updates the browser URL so back/forward navigation works with sort state.

## B.2: Implement on the First Table

Pick the table with the most data for meaningful testing. Based on the screenshot, **Students** is a good candidate since it clearly has many rows.

### B.2a: Discover the First Table's Implementation

```bash
# Find the Students list template
grep -rn "students\|student" src/templates/ --include="*.html" -l
cat src/templates/[path-to-students-list].html  # Read the full template

# Find the route handler
grep -rn "students\|student.*list\|student.*index" src/routers/ --include="*.py" -l
grep -rn "def.*student" src/routers/ --include="*.py" -A 20

# Find the service method
grep -rn "StudentService\|student_service\|get_students\|list_students" src/services/ --include="*.py" -l

# Check if the route already accepts sort/order params
grep -rn "sort\|order" src/routers/ --include="*.py" | grep -i student

# Check if HTMX partial rendering exists anywhere in the codebase
grep -rn "HX-Request\|is_htmx\|hx-request" src/routers/ --include="*.py" | head -10
```

Document:
1. **Template location and structure** — what columns exist? What's the `<thead>` structure?
2. **Route handler** — function name, URL path, what params it accepts, how it passes data to template
3. **Service method** — how queries are built, what filters exist
4. **Column-to-model mapping** — which display columns map to which SQLAlchemy model attributes?
5. **HTMX patterns** — does the codebase already do partial rendering for any table?

### B.2b: Update the Route Handler

Add `sort` and `order` query parameters with validation:

```python
@router.get("/path/to/students")  # Use actual URL path
async def list_students(
    request: Request,
    sort: str = "last_name",     # Sensible default sort column
    order: str = "asc",          # Default sort direction
    search: str = "",            # Keep existing params
    # ... other existing params ...
    db: Session = Depends(get_db),
):
    # Validate sort column against a whitelist of actual model attributes
    ALLOWED_SORT_COLUMNS = ['last_name', 'first_name', 'student_id', 'cohort', 'status', 'completion_date']
    # ^^^ REPLACE with actual column names from the Student model
    if sort not in ALLOWED_SORT_COLUMNS:
        sort = "last_name"  # Fall back to default
    if order not in ("asc", "desc"):
        order = "asc"

    # Call service with sort params
    students = student_service.get_students(db, sort=sort, order=order, search=search)

    # HTMX partial rendering — return just the table body for sort requests
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "students/_table_body.html",   # Partial template — adjust path
            {"request": request, "students": students}
        )

    # Full page render
    return templates.TemplateResponse(
        "students/index.html",   # Full template — adjust path
        {
            "request": request,
            "students": students,
            "current_sort": sort,
            "current_order": order,
            # ... keep all existing context variables ...
        }
    )
```

**Adapt completely to actual codebase patterns.** Match the existing route handler structure — if it uses `@app.get` instead of `@router.get`, if it uses a different template response helper, if it passes context differently. **Follow what's already there.**

### B.2c: Update the Service Layer

Add `order_by` support to the query method:

```python
def get_students(self, db: Session, sort: str = "last_name", order: str = "asc", **kwargs):
    query = db.query(Student)  # Use actual model name

    # ... existing filter/search logic stays exactly as-is ...

    # Add sorting
    sort_column = getattr(Student, sort, None)
    if sort_column is not None:
        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(Student.last_name.asc())  # Fallback

    return query.all()  # or .paginate() if pagination exists
```

**Adapt to actual model and method patterns.** If the service uses a different query style, follow it.

### B.2d: Extract Table Body to Partial Template

Create a partial that renders just the `<tbody>` content:

**File:** `src/templates/students/_table_body.html` (adjust path to match template organization)

Move the `{% for student in students %}` loop and all `<tr>` rows from the main template into this partial. Include the empty-state row:

```html
{% for student in students %}
<tr>
    <td>
        <div class="flex items-center gap-3">
            <div class="avatar placeholder">
                <div class="bg-neutral text-neutral-content rounded-full w-10">
                    <span>{{ student.first_name[0] }}{{ student.last_name[0] }}</span>
                </div>
            </div>
            <div>
                <div class="font-bold">{{ student.first_name }} {{ student.last_name }}</div>
                <div class="text-sm opacity-50">S{{ student.student_id }}</div>
            </div>
        </div>
    </td>
    <td>{{ student.cohort }}</td>
    <td><span class="badge badge-{{ 'info' if student.status == 'Enrolled' else 'success' }}">{{ student.status }}</span></td>
    <td>{{ student.completion_date.strftime('%b %d, %Y') if student.completion_date else '—' }}</td>
    <td><a href="/students/{{ student.id }}" class="link link-primary">View</a></td>
</tr>
{% else %}
<tr>
    <td colspan="5" class="text-center text-base-content/50 py-8">No students found.</td>
</tr>
{% endfor %}
```

**IMPORTANT:** This is a rough template based on the screenshot. The actual columns, classes, badge styles, URL patterns, and data formatting MUST match what's currently in the existing template. Copy the existing `<tr>` content exactly — just move it into the partial file.

### B.2e: Update the Full Template to Use Macro + Partial

In the main list template, replace the static `<th>` elements and include the partial:

```html
{% from 'components/_sortable_th.html' import sortable_header %}

{# ... existing page content above the table ... #}

<table class="table table-zebra w-full">
    <thead>
        <tr>
            {{ sortable_header('last_name', 'Student', current_sort, current_order) }}
            {{ sortable_header('cohort', 'Cohort', current_sort, current_order) }}
            {{ sortable_header('status', 'Status', current_sort, current_order) }}
            {{ sortable_header('completion_date', 'Completion Date', current_sort, current_order) }}
            <th>Actions</th>  {# Not sortable #}
        </tr>
    </thead>
    <tbody id="table-body">
        {% include 'students/_table_body.html' %}
    </tbody>
</table>
```

**Adapt column names and labels to match actual columns.** The `column` parameter (first arg) must exactly match a model attribute name. The `label` (second arg) is what the user sees.

**The `id="table-body"` on `<tbody>` is critical** — the macro's `hx-target` points to it.

### B.2f: Write Tests for the First Table

```python
def test_students_list_loads(admin_client):
    """Students list page loads successfully."""
    response = admin_client.get("/students")  # Use actual URL
    assert response.status_code == 200

def test_students_sort_by_name_asc(admin_client):
    """Sorting students by name ascending works."""
    response = admin_client.get("/students?sort=last_name&order=asc")
    assert response.status_code == 200

def test_students_sort_by_name_desc(admin_client):
    """Sorting students by name descending works."""
    response = admin_client.get("/students?sort=last_name&order=desc")
    assert response.status_code == 200

def test_students_sort_by_status(admin_client):
    """Sorting students by status works."""
    response = admin_client.get("/students?sort=status&order=asc")
    assert response.status_code == 200

def test_students_invalid_sort_falls_back(admin_client):
    """Invalid sort column silently falls back to default."""
    response = admin_client.get("/students?sort=nonexistent&order=asc")
    assert response.status_code == 200

def test_students_invalid_order_falls_back(admin_client):
    """Invalid order value silently falls back to default."""
    response = admin_client.get("/students?sort=last_name&order=sideways")
    assert response.status_code == 200

def test_students_htmx_returns_partial(admin_client):
    """HTMX request returns partial table body, not full page."""
    response = admin_client.get(
        "/students?sort=last_name&order=asc",
        headers={"HX-Request": "true"}
    )
    assert response.status_code == 200
    # Partial should NOT contain the full page chrome
    assert "<html" not in response.text.lower()
    assert "<nav" not in response.text.lower()

def test_students_sort_preserves_search(admin_client):
    """Sorting while searching preserves the search filter."""
    response = admin_client.get("/students?sort=last_name&order=asc&search=Alvarez")
    assert response.status_code == 200
```

### B.2g: Verify First Table Manually

1. Navigate to the Students list
2. Click "Student" column header → table sorts by name ascending, ▲ appears
3. Click "Student" again → sorts descending, ▼ appears
4. Click "Status" → sorts by status, ▲ on Status, ⇅ on Student
5. Click "Completion Date" → sorts by date
6. Scroll down → header sticks (Phase A already handles this)
7. If search exists: type a search term, then sort → search preserved
8. Check URL → `?sort=last_name&order=asc` in the browser URL bar
9. Click browser back → returns to previous sort state
10. Click browser forward → goes to sort state again

### B.2h: Commit First Table

```bash
git add -A
git commit -m "feat(ui): add sortable table header macro + apply to Students list

- Create reusable sortable_header Jinja2 macro
- Implement server-side sorting via HTMX for Students table
- Extract table body to partial template for HTMX rendering
- Sort state preserved in URL via hx-push-url
- Search/filter state preserved when sorting
- Validate sort columns against whitelist
- Add tests for sort functionality
- Spoke 3: Infrastructure (Cross-Cutting UI)"
```

---

## B.3: Rollout to All Remaining Tables

After the first table works, apply the same pattern to **every remaining table**. The rule: if it has a `<thead>`, it gets sortable. No exceptions.

### Per-Table Checklist

For each table, repeat this checklist:

- [ ] Read the template — identify all columns and their model attribute names
- [ ] Read the route handler — understand current params and response pattern
- [ ] Read the service method — understand the query
- [ ] Add `sort` and `order` query params to the route handler with whitelist validation
- [ ] Add `order_by` to the service method
- [ ] Extract `<tbody>` into a partial template (e.g., `_table_body.html`)
- [ ] Replace static `<th>` with `sortable_header` macro calls in the main template
- [ ] Add HTMX partial rendering to the route handler (`HX-Request` header check)
- [ ] Pass `current_sort` and `current_order` to the template context
- [ ] Write tests (at minimum: default load, sort asc, sort desc, invalid sort, HTMX partial)
- [ ] Manual verify: click headers, check URL, check back/forward, check sticky
- [ ] Commit

### Table Inventory

**Find every table in the codebase:**

```bash
grep -rn "<thead" src/templates/ --include="*.html" -l
```

**Expected tables (verify against actual codebase — this list may not be exhaustive):**

| # | Table | Likely Default Sort |
|---|-------|-------------------|
| ✅ | Students list | `last_name` asc |
| 2 | Members list | `last_name` asc |
| 3 | SALTing Activities | `date` desc |
| 4 | Referral Books / Registrations | `book_number` or `date` |
| 5 | Dispatch / Labor Requests | `date` desc |
| 6 | Dues Payments | `date` desc |
| 7 | Grievances list | `date` desc |
| 8 | Staff list | `last_name` asc |
| 9 | Benevolence applications | `date` desc |
| 10 | Audit log table (if exists) | `timestamp` desc |
| 11+ | Any other table found by the grep | Context-dependent |

**If a table exists that is not on this list, it still gets the treatment.**

### Commit Per Table

Each table gets its own commit:

```
feat(ui): apply sortable headers to [Table Name]

- Add sort/order query params to [route name]
- Add order_by support to [service method]
- Extract table body to partial template
- Add HTMX partial rendering
- Add tests for sort functionality
- Spoke 3: Infrastructure (Cross-Cutting UI)
```

### Incremental is OK

**You do NOT need to finish all tables in one session.** The macro is built and proven after the first table. Each subsequent table is ~30–45 minutes of mechanical work. Commit after each one. If the session runs out of time, note which tables are done and which remain in `CLAUDE.md`.

---

## Anti-Patterns to Avoid

### Phase A (Sticky)
- **DO NOT** add sticky classes to individual templates — use the global CSS rule
- **DO NOT** set `top: 0` — it must offset below the navbar
- **DO NOT** forget the background color — content will bleed through without it
- **DO NOT** put tables inside containers with `overflow: auto` or `overflow: hidden` or `max-height` — this breaks `position: sticky`. If you find a table wrapped in such a container, remove the overflow/max-height from the parent.

### Phase B (Sortable)
- **DO NOT** implement client-side JavaScript sorting — server-side HTMX only
- **DO NOT** allow arbitrary column names in `sort` — validate against a whitelist per table
- **DO NOT** use `hx-swap="outerHTML"` on the tbody — use `innerHTML` so `<tbody id="table-body">` stays in the DOM
- **DO NOT** forget `hx-push-url="true"` — without it, browser back/forward won't work with sort state
- **DO NOT** duplicate row rendering logic — the partial template is the single source of truth, included by both the full template and the HTMX response
- **DO NOT** sort by computed/virtual columns that aren't database fields unless handled explicitly in the service layer
- **DO NOT** forget the empty-state row (`{% else %}` in the for loop) in the partial
- **DO NOT** forget to preserve search/filter state — `hx-include` in the macro captures active filter inputs

---

## Acceptance Criteria

### Phase A
- [ ] Global CSS rule added (one location — stylesheet or `<style>` in base.html)
- [ ] Every table in the app has sticky headers below the navbar
- [ ] Header background prevents content bleed-through
- [ ] No individual template changes were needed for sticky behavior
- [ ] All existing tests still pass

### Phase B — First Table
- [ ] Sortable header macro created at `src/templates/components/_sortable_th.html`
- [ ] First table uses the macro for all sortable columns
- [ ] Clicking a column header sorts via HTMX server-side request
- [ ] Clicking the same header reverses sort order
- [ ] Sort indicator: ▲ (asc) / ▼ (desc) on active column, ⇅ on inactive
- [ ] Sort params appear in URL (`?sort=name&order=asc`)
- [ ] Browser back/forward navigation works with sort state
- [ ] Search/filter state preserved when sorting
- [ ] HTMX returns partial content (not full page)
- [ ] Invalid sort columns fall back to default safely
- [ ] All existing tests still pass
- [ ] New tests written and passing

### Phase B — Each Additional Table
- [ ] Route handler accepts `sort`/`order` with whitelist validation
- [ ] Service method supports `order_by`
- [ ] Template uses `sortable_header` macro
- [ ] Table body extracted to partial template
- [ ] HTMX partial rendering works
- [ ] Tests written and passing
- [ ] Committed separately

---

## File Manifest

### Phase A

**Created (if no custom CSS exists):**
- `src/static/css/custom.css`

**Modified:**
- `src/static/css/custom.css` (or `app.css`, or `<style>` in `base.html`) — add sticky rule
- `src/templates/base.html` — link custom CSS (if newly created); add `impersonation-active` body class (if impersonation banner exists)

### Phase B — First Table

**Created:**
- `src/templates/components/_sortable_th.html` — reusable macro
- `src/templates/[domain]/[entity]/_table_body.html` — table body partial
- `tests/test_sortable_tables.py` — tests

**Modified:**
- First table's list template — replace `<th>` with macro, include partial
- First table's route handler — add sort/order params, HTMX partial rendering
- First table's service method — add order_by support

### Phase B — Each Additional Table

**Created:**
- `src/templates/[domain]/[entity]/_table_body.html` — table body partial

**Modified:**
- Table's list template, route handler, service method
- `tests/test_sortable_tables.py` — additional tests

---

## Session Close-Out

After committing:

1. Update `CLAUDE.md`:
   - Note sticky headers are globally applied
   - Note sortable headers macro location
   - List which tables have been converted to sortable (and which remain)
   - Update test count
2. Update `CHANGELOG.md` — add entries for sticky + sortable features
3. Update any docs under `/docs/` that reference table patterns or UI conventions
4. **Cross-Spoke Handoff Note:** Generate a brief note for all Spokes documenting:
   - Sticky headers are automatic for any new table (no action needed)
   - How to use the `sortable_header` macro for new tables
   - Backend requirements: `sort`/`order` params, `order_by`, HTMX partial rendering
   - Link to the first implementation as a reference example
5. If any tables remain unconverted, note them as remaining work in `CLAUDE.md`

---

*Spoke 3: Infrastructure — Sticky + Sortable Table Headers*
*UnionCore v0.9.16-alpha*
