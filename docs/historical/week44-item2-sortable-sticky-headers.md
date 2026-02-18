# UnionCore — Week 44+: Sortable + Sticky Table Headers
**Spoke:** Spoke 3: Infrastructure (Cross-Cutting UI)
**Phase:** UI Enhancement Bundle — Item 2 of 5 (final item, incrementally applied)
**Estimated Effort:** 3–4 hours (1–1.5 hours for macro + first table, then ~30 min per additional table)
**Prerequisites:** Items 1, 3A, 3B, 4 committed. At least one data table with records to test against.
**Source:** Hub Handoff Document (February 10, 2026)

---

## Context

Every list view in UnionCore uses data tables. Users need:
1. **Clickable column headers** to sort ascending/descending
2. **Sticky header row** that stays visible when scrolling long lists

This is implemented as **server-side sorting via HTMX** (not client-side JavaScript). The approach: build a reusable Jinja2 macro once, then roll it out table-by-table.

---

## Pre-Flight Checklist

- [ ] `git status` is clean
- [ ] Create and checkout branch: `git checkout -b feature/sortable-sticky-headers`
- [ ] App starts without errors
- [ ] Record current test count: `pytest --tb=short -q 2>&1 | tail -5`
- [ ] Identify at least one table with enough records to test scrolling (seed data should provide this)

---

## Step 1: Discover Current Table Patterns

**Mandatory discovery. Read all list templates before writing the macro.**

```bash
# Find all templates with tables
grep -rln "<table\|<thead\|<th" src/templates/ --include="*.html"

# Read the SALTing activities table (recommended first target)
find src/templates -path "*salt*" -name "*.html" | xargs cat

# Read the Members list table
find src/templates -path "*member*" -name "*list*" -o -path "*member*" -name "*index*" | xargs cat

# Check existing table class patterns
grep -rn "class=.*table\|<table" src/templates/ --include="*.html" | head -20

# Find list route handlers to understand query patterns
grep -rn "def.*list\|def.*index\|async def.*list\|async def.*index" src/routers/ --include="*.py" | head -20

# Find service methods with query/list functions
grep -rn "def.*get_all\|def.*list\|def.*search\|def.*filter" src/services/ --include="*.py" | head -20

# Check if any tables already have sort params
grep -rn "sort\|order_by\|order" src/routers/ --include="*.py" | head -20

# Measure the navbar height (we need this for sticky positioning)
grep -rn "navbar\|nav " src/templates/ --include="*.html" | head -10
```

Document:
1. **All table template locations** — which templates have `<table>` elements?
2. **Current `<th>` pattern** — plain `<th>Text</th>` or something more complex?
3. **Table CSS classes** — what DaisyUI/Tailwind classes are used? (`table`, `table-zebra`, `table-pin-rows`?)
4. **Route handlers** — do any already accept `sort`/`order` query params?
5. **Service layer** — do query methods support `order_by`?
6. **Navbar height** — inspect in browser, get exact pixel value
7. **Impersonation banner height** — if the View As banner (Item 3B) is sticky, its height affects the sticky offset. Measure this too.
8. **Existing search/filter patterns** — do tables have search fields, filter dropdowns? These must be preserved when sorting.
9. **Pagination** — is there pagination? Sort must be preserved when paginating.
10. **HTMX partial rendering** — do list pages already use HTMX to swap table bodies? Or do they full-page render?

---

## Step 2: Create the Sortable Header Macro

Create a reusable Jinja2 macro file.

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
- Replace `NAVBAR_HEIGHT_PX` with the actual navbar height in pixels (e.g., `64px`). If the impersonation banner is also sticky, the offset needs to account for both: `top-[calc(NAVBAR_PX+BANNER_PX)]` or just the navbar height if the banner is above the sticky threshold.
- The `hx-include` attribute preserves search/filter/pagination state when sorting. Adjust the selector list to match whatever form inputs exist in the actual tables.
- If tables already use DaisyUI's `table-pin-rows` class, the sticky behavior might already be partially implemented. Check and don't duplicate.
- If the codebase uses `table-pin-rows` from DaisyUI, you might not need the custom sticky CSS at all — DaisyUI handles it. **Test this.**

---

## Step 3: Add Sticky Header CSS (If Needed)

Check if DaisyUI's `table-pin-rows` class handles sticky headers:

```bash
# Check if table-pin-rows is already used
grep -rn "table-pin-rows" src/templates/ --include="*.html"
```

**If DaisyUI handles it:** Add `table-pin-rows` class to `<table>` elements and skip custom CSS. You may still need to set the `top` offset if the default doesn't account for the navbar.

**If custom CSS is needed:** Add to the project's custom CSS file (or create one):

**File:** `src/static/css/custom.css` (or wherever custom styles live)

```css
/* Sortable sticky table headers
   Adjust top value to match navbar height.
   If impersonation banner is active, JavaScript adjusts this dynamically. */
.table thead th.sticky {
    /* top value set via Tailwind class on the element */
    background-color: inherit;
    box-shadow: 0 1px 0 0 var(--fallback-bc, oklch(var(--bc) / 0.1));
}

/* Ensure table container allows sticky to work */
.table-container {
    overflow-x: auto;
    /* Do NOT set overflow-y or max-height — sticky requires the scroll container
       to be the viewport, not a nested div */
}
```

**IMPORTANT:** Sticky positioning only works if the nearest scrolling ancestor is the viewport (or an explicitly set overflow container). If the table is inside a `<div>` with `overflow: auto` or `overflow: hidden`, the sticky header will NOT work. Check the existing layout and remove any conflicting overflow settings on parent elements.

---

## Step 4: Backend — Add Sort Support to the First Table

Start with the **SALTing Activities table** (or whichever table the discovery step reveals as the best first target — ideally one with the most records and simplest query).

### 4a: Update the Route Handler

Find the list route handler for the chosen table. Add `sort` and `order` query parameters:

```python
@router.get("/operations/salting")  # or whatever the actual path is
async def list_salting_activities(
    request: Request,
    db: Session = Depends(get_db),
    sort: str = "date",           # Default sort column — pick something sensible
    order: str = "desc",          # Default order
    search: str = None,           # Existing search param (if any)
    # ... other existing params
):
    # Validate sort column against allowed columns
    allowed_sort_columns = ["date", "name", "status", "location", "type"]  # Adjust to actual columns
    if sort not in allowed_sort_columns:
        sort = "date"  # Fall back to default
    if order not in ("asc", "desc"):
        order = "desc"

    activities = salting_service.get_activities(
        db,
        sort=sort,
        order=order,
        search=search,
        # ... other existing params
    )

    # If this is an HTMX request, return only the table body partial
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "operations/salting/_table_body.html",  # Partial template
            {
                "request": request,
                "activities": activities,
                "current_sort": sort,
                "current_order": order,
            }
        )

    # Full page render
    return templates.TemplateResponse(
        "operations/salting/index.html",
        {
            "request": request,
            "activities": activities,
            "current_sort": sort,
            "current_order": order,
            "effective_role": request.state.effective_role,
            # ... other existing context
        }
    )
```

**CRITICAL: HTMX partial rendering.** When the user clicks a sort header, HTMX sends a request with `HX-Request: true`. The response should return ONLY the `<tbody>` content (a partial template), not the entire page. This requires:

1. A partial template that renders just the table rows
2. The route handler detecting HTMX requests and returning the partial

**If the codebase doesn't already have HTMX partial rendering for tables**, you need to:
1. Extract the `<tbody>` content from the full template into a separate partial (e.g., `_table_body.html`)
2. Include the partial from the full template: `{% include 'operations/salting/_table_body.html' %}`
3. Return the partial for HTMX requests, the full template for regular requests

**If HTMX partial rendering already exists**, just add the sort/order params to the existing pattern.

### 4b: Update the Service Layer

Add `order_by` support to the service method:

```python
def get_activities(self, db: Session, sort: str = "date", order: str = "desc", **kwargs):
    query = db.query(SaltingActivity)

    # Apply existing filters (search, status, etc.)
    # ... existing filter logic ...

    # Apply sorting
    sort_column = getattr(SaltingActivity, sort, None)
    if sort_column is not None:
        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

    return query.all()  # or .paginate() if pagination exists
```

**Adapt to actual model attributes.** The `sort` parameter from the URL maps to a model attribute name. Make sure the mapping is safe — only allow known column names (validated in the route handler).

### 4c: Update the Template

In the list template, replace static `<th>` elements with the sortable macro:

```html
{% from 'components/_sortable_th.html' import sortable_header %}

<table class="table table-zebra w-full">
    <thead>
        <tr>
            {{ sortable_header('date', 'Date', current_sort, current_order) }}
            {{ sortable_header('name', 'Activity Name', current_sort, current_order) }}
            {{ sortable_header('status', 'Status', current_sort, current_order) }}
            {{ sortable_header('location', 'Location', current_sort, current_order) }}
            <th>Actions</th>  {# Not sortable #}
        </tr>
    </thead>
    <tbody id="table-body">
        {% include 'operations/salting/_table_body.html' %}
    </tbody>
</table>
```

**The `id="table-body"` on `<tbody>` is critical** — this is what the `hx-target` in the macro points to.

### 4d: Create the Table Body Partial (If It Doesn't Exist)

**File:** `src/templates/operations/salting/_table_body.html` (adjust path to match conventions)

Extract the row-rendering loop from the full template into this partial:

```html
{% for activity in activities %}
<tr>
    <td>{{ activity.date.strftime('%Y-%m-%d') }}</td>
    <td>{{ activity.name }}</td>
    <td>{{ activity.status }}</td>
    <td>{{ activity.location }}</td>
    <td>
        <a href="/operations/salting/{{ activity.id }}" class="btn btn-sm btn-ghost">View</a>
    </td>
</tr>
{% else %}
<tr>
    <td colspan="5" class="text-center text-base-content/50 py-8">No activities found.</td>
</tr>
{% endfor %}
```

---

## Step 5: Test the First Table

### Automated Tests

```python
def test_salting_list_default_sort(admin_client):
    """List endpoint returns results sorted by date descending by default."""
    response = admin_client.get("/operations/salting")
    assert response.status_code == 200

def test_salting_list_sort_by_name_asc(admin_client):
    """Sort by name ascending."""
    response = admin_client.get("/operations/salting?sort=name&order=asc")
    assert response.status_code == 200

def test_salting_list_sort_by_name_desc(admin_client):
    """Sort by name descending."""
    response = admin_client.get("/operations/salting?sort=name&order=desc")
    assert response.status_code == 200

def test_salting_list_invalid_sort_column(admin_client):
    """Invalid sort column falls back to default."""
    response = admin_client.get("/operations/salting?sort=invalid_column&order=asc")
    assert response.status_code == 200

def test_salting_list_invalid_order(admin_client):
    """Invalid order value falls back to desc."""
    response = admin_client.get("/operations/salting?sort=date&order=invalid")
    assert response.status_code == 200

def test_salting_list_htmx_returns_partial(admin_client):
    """HTMX request returns partial table body, not full page."""
    response = admin_client.get(
        "/operations/salting?sort=date&order=asc",
        headers={"HX-Request": "true"}
    )
    assert response.status_code == 200
    # Partial should NOT contain <html>, <head>, <body>, or nav elements
    assert "<html" not in response.text
    assert "<nav" not in response.text

def test_salting_list_sort_preserves_search(admin_client):
    """Sorting preserves active search filter."""
    response = admin_client.get("/operations/salting?sort=name&order=asc&search=test")
    assert response.status_code == 200
```

### Manual Verification

1. Navigate to the SALTing activities list
2. Click "Date" header → table sorts by date ascending, ▲ appears
3. Click "Date" again → sorts descending, ▼ appears
4. Click "Name" → sorts by name ascending, ▲ on Name, ⇅ on Date
5. Scroll down a long list → header row sticks below navbar
6. If search box exists: type a search term, then sort → search is preserved
7. Check URL → sort params appear in the URL (`?sort=name&order=asc`)
8. Click browser back → returns to previous sort state (because of `hx-push-url`)

---

## Step 6: Rollout Plan for Remaining Tables

After the first table is working, apply the same pattern to each remaining table. For each table:

1. Add `sort` and `order` query params to the route handler
2. Add `order_by` support to the service method
3. Replace static `<th>` with `sortable_header` macro calls
4. Extract `<tbody>` into a partial template (if not already done)
5. Add HTMX partial rendering to the route handler (if not already done)
6. Write tests
7. Manual verify

**Rollout order (recommended — adjust based on what actually exists):**

| Priority | Table | Reason |
|----------|-------|--------|
| ✅ Done | SALTing Activities | First implementation (Step 4) |
| 2 | Members list | Largest dataset, most-used table |
| 3 | Referral Books / Registrations | High-frequency use |
| 4 | Dispatch requests | Operational priority |
| 5 | Dues payments | Less frequently sorted |
| 6 | Students | Moderate use |
| 7 | Grievances | Lower volume |

**You do NOT need to finish all tables in one session.** The macro is built and proven after the first table. Remaining tables can be done incrementally across future sessions. Commit after each table is complete.

---

## Anti-Patterns to Avoid

- **DO NOT** implement client-side JavaScript sorting. The handoff explicitly requires server-side HTMX sorting.
- **DO NOT** allow arbitrary column names in the `sort` parameter. Validate against a whitelist of allowed columns per table.
- **DO NOT** put the table inside a `<div>` with `overflow-y: auto` or `max-height` — this breaks `position: sticky`.
- **DO NOT** forget to preserve search/filter state when sorting. The `hx-include` attribute must capture all active filter inputs.
- **DO NOT** forget `hx-push-url="true"` — without it, the browser URL won't update and back/forward navigation won't work.
- **DO NOT** use `hx-swap="outerHTML"` on the tbody — use `innerHTML` so the `<tbody id="table-body">` element itself stays in the DOM.
- **DO NOT** duplicate the row rendering logic — the partial template should be the single source of truth, included by both the full template and the HTMX response.
- **DO NOT** sort by computed/virtual columns that aren't database fields unless you handle it explicitly in the service layer.
- **DO NOT** forget the empty-state row (`{% else %}` in the for loop) in the partial template.

---

## Acceptance Criteria (First Table)

- [ ] Sortable header macro created in `src/templates/components/_sortable_th.html`
- [ ] First table (SALTing or equivalent) uses the sortable macro
- [ ] Clicking a column header sorts the table by that column via HTMX
- [ ] Clicking the same header again reverses sort order
- [ ] Sort indicator (▲/▼) appears on active column
- [ ] Inactive columns show neutral indicator (⇅)
- [ ] Header row sticks below navbar when scrolling
- [ ] Sort parameters appear in the URL
- [ ] Browser back/forward navigation works with sort state
- [ ] Search/filter state preserved when sorting
- [ ] HTMX requests return partial content (not full page)
- [ ] Invalid sort columns fall back to default safely
- [ ] All existing tests still pass
- [ ] New tests written and passing for the first table

## Acceptance Criteria (Remaining Tables — Per Table)

- [ ] Route handler accepts sort/order params with validation
- [ ] Service method supports order_by
- [ ] Template uses sortable_header macro
- [ ] Table body extracted to partial template
- [ ] HTMX partial rendering works
- [ ] Tests written and passing

---

## File Manifest (First Table)

**Created files:**
- `src/templates/components/_sortable_th.html` — reusable macro
- `src/templates/operations/salting/_table_body.html` — table body partial (adjust path)
- `src/static/css/custom.css` — sticky header styles (only if DaisyUI `table-pin-rows` doesn't suffice)
- `tests/test_sortable_tables.py` — tests

**Modified files:**
- First table's list template — replace `<th>` with macro calls, add `<tbody id="table-body">`
- First table's route handler — add sort/order params, HTMX partial rendering
- First table's service method — add order_by support

**Deleted files:**
- None

---

## Git Commit Messages

**First commit (macro + first table):**
```
feat(ui): add sortable sticky table headers with HTMX

- Create reusable sortable_header Jinja2 macro
- Implement server-side sorting via HTMX for SALTing activities table
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

## Session Close-Out

After committing:

1. Update `CLAUDE.md` — note sortable headers, list which tables have been converted
2. Update `CHANGELOG.md` — add entry
3. Update any docs under `/docs/` that reference table patterns or UI conventions
4. **Cross-Spoke Impact Note:** New tables created by other Spokes should follow the sortable header pattern. Generate a brief handoff note documenting:
   - How to use the `sortable_header` macro
   - Backend requirements (sort/order params, order_by, HTMX partial rendering)
   - Link to the first implementation as a reference

---

*Spoke 3: Infrastructure — Item 2 of UI Enhancement Bundle*
*UnionCore v0.9.16-alpha*
