# Sortable Table Header Rollout Tracker

## Status Key
- ✅ Complete — sortable headers implemented, tested, verified
- 🔧 In Progress — currently being implemented
- ⬜ Not Started — needs implementation
- ➖ N/A — page doesn't have a sortable data table

## Tables

| Page | Route | Sortable | Sticky | Notes |
|------|-------|----------|--------|-------|
| SALTing Activities | /operations/salting | ✅ | ✅ | Fixed in hotfix (sort response + sticky + text color) |
| Benevolence | /operations/benevolence | ✅ | ✅ | Rolled out in Phase B |
| Grievances | /operations/grievances | ✅ | ✅ | Rolled out in Phase B |
| Students | /training/students | ✅ | ✅ | Rolled out in Phase B |
| Members List | /members | ✅ | ✅ | Rolled out in Phase B |
| Staff | /admin/staff | ✅ | ✅ | Rolled out in Phase B |
| Referral Books | /referral/books | ⬜ | ⬜ | |
| Dues Payments | /dues/payments | ⬜ | ⬜ | |
| Dispatch Requests | /dispatch/requests | ⬜ | ⬜ | |
| Audit Log | /admin/audit | ⬜ | ⬜ | |

## Pattern for Adding Sorting to a New Table

Each table rollout requires:

1. **Route handler:** Add `sort` and `order` query params with whitelist validation
2. **Route handler:** Add HTMX detection — if `HX-Request: true` AND `HX-Target: table-body`, call service and return `_table_body.html` partial
3. **Service layer:** Add `sort` and `order` params to the query method, apply `order_by` dynamically
4. **Template:** Ensure `<tbody id="table-body">` exists with that exact ID
5. **Template:** Use `{% include 'path/_table_body.html' %}` inside the tbody
6. **Template:** Use `{{ sortable_header(...) }}` macro for each sortable column
7. **Template (full page):** Pass `current_sort` and `current_order` to the initial HTMX load URL so refresh preserves sort state

### Critical Rules

- The `_table_body.html` partial must contain ONLY `<tr>` elements — no `<table>`, `<thead>`, `{% extends %}`, or layout markup
- Do NOT use `overflow-hidden` on any ancestor of the table — breaks `position: sticky`
- `overflow-x-auto` on the table wrapper div is fine for horizontal scroll
- Use `table-pin-rows` on `<table>` (NOT per-cell `sticky` on `<th>`) to avoid column collapse in `overflow-x-auto` containers
- Non-sortable columns (like "Actions") need `text-white` in their `<th>` class to match sortable headers
- Always include an empty-state `<tr>` in the `{% else %}` branch of the for loop in `_table_body.html`

### Sticky Offset (custom.css)

The sticky top offset is managed globally in `src/static/css/custom.css`:

```css
.table.table-pin-rows thead tr {
    top: 64px;               /* navbar height */
    z-index: 10;
}

body.impersonation-active .table.table-pin-rows thead tr {
    top: 128px;              /* navbar + impersonation banner */
}
```

If navbar or banner height changes, update these values.

### Route Handler Pattern

```python
@router.get("/your-route")
async def your_list_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    sort: str = Query("default_column"),
    order: str = Query("desc"),
    # ... other filters ...
):
    allowed_sort_columns = ["col1", "col2", "col3"]
    if sort not in allowed_sort_columns:
        sort = "default_column"
    if order not in ("asc", "desc"):
        order = "desc"

    service = YourService(db)

    # HTMX sort request → return only tbody partial
    if request.headers.get("HX-Request") == "true" and request.headers.get("HX-Target") == "table-body":
        items = await service.list_items(sort=sort, order=order, ...)
        return templates.TemplateResponse(
            "your_module/partials/_table_body.html",
            {"request": request, "items": items, "current_sort": sort, "current_order": order, ...},
        )

    # Full page load
    return templates.TemplateResponse(
        "your_module/index.html",
        {"request": request, "current_sort": sort, "current_order": order, ...},
    )
```

### Template Pattern (index.html table container)

```html
<!-- Pass sort params into the initial HTMX load so page refresh preserves sort state -->
<div
    id="table-container"
    hx-get="/your-route/search?sort={{ current_sort }}&order={{ current_order }}"
    hx-trigger="load"
>
    <span class="loading loading-spinner loading-lg"></span>
</div>
```

### Template Pattern (_table.html)

```html
{% from 'components/_sortable_th.html' import sortable_header %}

<div class="overflow-x-auto">
    <table class="table table-zebra table-pin-rows">
        <thead>
            <tr>
                {{ sortable_header('col1', 'Column 1', current_sort, current_order) }}
                {{ sortable_header('col2', 'Column 2', current_sort, current_order) }}
                <th class="bg-base-200 text-white">Actions</th>
            </tr>
        </thead>
        <tbody id="table-body">
            {% include 'your_module/partials/_table_body.html' %}
        </tbody>
    </table>
</div>
```

## Estimated Effort Per Table
~30–45 minutes per table (route + service + template work)

## Ownership
- **Spoke 3 (Infrastructure):** Owns `_sortable_th.html` macro, `custom.css` sticky rules, this tracking doc, and the rollout pattern
- **Domain Spokes:** Own the backend sort logic (route + service) for tables in their domain
