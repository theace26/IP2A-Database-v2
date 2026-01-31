# Phase 6 Week 5 - Session B: Member List with Search/Filters

**Document:** 2 of 3
**Estimated Time:** 2-3 hours
**Focus:** Member table with search, filters, badges, and pagination

---

## Objective

Create the member list with:
- Table displaying all members
- Live search (name, card ID, email)
- Filter by status and classification
- Status and classification badges
- Current employer column
- Pagination
- Row actions (view, edit)

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show ~229 passed
```

---

## Step 1: Create Table Partial (30 min)

Create `src/templates/members/partials/_table.html`:

```html
{# Member table partial - updated via HTMX search #}

<div class="overflow-x-auto">
    <table class="table table-zebra">
        <thead>
            <tr class="bg-base-200">
                <th class="w-12">
                    <label>
                        <input type="checkbox" class="checkbox checkbox-sm" id="select-all" />
                    </label>
                </th>
                <th>Card ID</th>
                <th>Name</th>
                <th>Classification</th>
                <th>Status</th>
                <th>Current Employer</th>
                <th>Dues</th>
                <th class="w-24">Actions</th>
            </tr>
        </thead>
        <tbody id="member-table-body">
            {% if members_data %}
                {% for item in members_data %}
                {% set member = item.member %}
                {% set employer = item.current_employer %}
                {% include "members/partials/_row.html" %}
                {% endfor %}
            {% else %}
            <tr>
                <td colspan="8" class="text-center py-12">
                    <div class="text-base-content/50">
                        <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                        </svg>
                        <p class="text-lg">No members found</p>
                        {% if query %}
                        <p class="text-sm mt-1">Try adjusting your search or filters</p>
                        {% endif %}
                    </div>
                </td>
            </tr>
            {% endif %}
        </tbody>
    </table>
</div>

{% if members_data %}
<!-- Pagination -->
<div class="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t border-base-200">
    <div class="text-sm text-base-content/60">
        Showing {{ ((current_page - 1) * 20) + 1 }} - {{ ((current_page - 1) * 20) + members_data|length }} of {{ total }} members
    </div>

    <div class="join">
        {% if current_page > 1 %}
        <button
            class="join-item btn btn-sm"
            hx-get="/members/search?page={{ current_page - 1 }}&q={{ query }}&status={{ status_filter }}&classification={{ classification_filter }}"
            hx-target="#table-container"
        >
            «
        </button>
        {% else %}
        <button class="join-item btn btn-sm btn-disabled">«</button>
        {% endif %}

        {% for p in range(1, total_pages + 1) %}
            {% if p == current_page %}
            <button class="join-item btn btn-sm btn-active">{{ p }}</button>
            {% elif p == 1 or p == total_pages or (p >= current_page - 2 and p <= current_page + 2) %}
            <button
                class="join-item btn btn-sm"
                hx-get="/members/search?page={{ p }}&q={{ query }}&status={{ status_filter }}&classification={{ classification_filter }}"
                hx-target="#table-container"
            >
                {{ p }}
            </button>
            {% elif p == current_page - 3 or p == current_page + 3 %}
            <button class="join-item btn btn-sm btn-disabled">...</button>
            {% endif %}
        {% endfor %}

        {% if current_page < total_pages %}
        <button
            class="join-item btn btn-sm"
            hx-get="/members/search?page={{ current_page + 1 }}&q={{ query }}&status={{ status_filter }}&classification={{ classification_filter }}"
            hx-target="#table-container"
        >
            »
        </button>
        {% else %}
        <button class="join-item btn btn-sm btn-disabled">»</button>
        {% endif %}
    </div>
</div>
{% endif %}
```

---

## Step 2: Create Row Partial (25 min)

Create `src/templates/members/partials/_row.html`:

```html
{# Single member row - can be swapped via HTMX after actions #}

<tr class="hover" id="member-row-{{ member.id }}">
    <!-- Checkbox -->
    <td>
        <label>
            <input type="checkbox" class="checkbox checkbox-sm" name="selected_members" value="{{ member.id }}" />
        </label>
    </td>

    <!-- Card ID -->
    <td>
        <span class="font-mono text-sm">{{ member.card_id or '—' }}</span>
    </td>

    <!-- Name -->
    <td>
        <div class="flex items-center gap-3">
            <div class="avatar placeholder">
                <div class="bg-neutral text-neutral-content rounded-full w-10">
                    <span class="text-sm">
                        {{ member.first_name[0] | upper if member.first_name else '?' }}{{ member.last_name[0] | upper if member.last_name else '' }}
                    </span>
                </div>
            </div>
            <div>
                <div class="font-bold">
                    {{ member.first_name or '' }} {{ member.last_name or '' }}
                </div>
                <div class="text-sm text-base-content/60">
                    {{ member.email or 'No email' }}
                </div>
            </div>
        </div>
    </td>

    <!-- Classification -->
    <td>
        {% if member.classification %}
        <span class="badge {{ get_classification_badge_class(member.classification) }} badge-sm">
            {{ format_classification(member.classification) }}
        </span>
        {% else %}
        <span class="badge badge-ghost badge-sm">Unclassified</span>
        {% endif %}
    </td>

    <!-- Status -->
    <td>
        <span class="badge {{ get_status_badge_class(member.status) }} gap-1">
            {% if member.status.value == 'active' %}
            <span class="w-2 h-2 rounded-full bg-current opacity-75"></span>
            {% endif %}
            {{ member.status.value | title }}
        </span>
    </td>

    <!-- Current Employer -->
    <td>
        {% if employer %}
        <div>
            <div class="font-medium text-sm">{{ employer.name }}</div>
            <div class="text-xs text-base-content/60">
                Since {{ employer.start_date.strftime('%b %Y') }}
            </div>
        </div>
        {% else %}
        <span class="text-base-content/40 text-sm">Not employed</span>
        {% endif %}
    </td>

    <!-- Dues Status -->
    <td>
        {# Simplified dues indicator - will be enhanced in detail page #}
        <div class="flex items-center gap-1">
            <span class="w-2 h-2 rounded-full bg-success"></span>
            <span class="text-xs text-success">Current</span>
        </div>
    </td>

    <!-- Actions -->
    <td>
        <div class="flex gap-1">
            <!-- View Detail -->
            <a href="/members/{{ member.id }}" class="btn btn-ghost btn-sm" title="View Details">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
            </a>

            <!-- Quick Edit -->
            <button
                class="btn btn-ghost btn-sm"
                hx-get="/members/{{ member.id }}/edit"
                hx-target="#modal-content"
                hx-swap="innerHTML"
                onclick="document.getElementById('edit-modal').showModal()"
                title="Quick Edit"
            >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                </svg>
            </button>

            <!-- More Actions Dropdown -->
            <div class="dropdown dropdown-end">
                <label tabindex="0" class="btn btn-ghost btn-sm">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/>
                    </svg>
                </label>
                <ul tabindex="0" class="dropdown-content z-[1] menu menu-sm p-2 shadow-lg bg-base-100 rounded-box w-48">
                    <li>
                        <a href="/members/{{ member.id }}">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                            </svg>
                            View Full Profile
                        </a>
                    </li>
                    <li>
                        <a href="/members/{{ member.id }}#employment">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                            </svg>
                            Employment History
                        </a>
                    </li>
                    <li>
                        <a href="/members/{{ member.id }}#dues">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                            Dues History
                        </a>
                    </li>
                    {% if member.status.value == 'active' %}
                    <div class="divider my-1"></div>
                    <li>
                        <button class="text-warning">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"/>
                            </svg>
                            Mark Inactive
                        </button>
                    </li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </td>
</tr>
```

---

## Step 3: Update Index Page with Edit Modal (10 min)

Add to `src/templates/members/index.html` before the closing `{% endblock %}`:

```html
<!-- Edit Modal -->
<dialog id="edit-modal" class="modal">
    <div class="modal-box max-w-2xl">
        <form method="dialog">
            <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
        </form>
        <div id="modal-content">
            <!-- HTMX loads content here -->
            <div class="flex items-center justify-center py-8">
                <span class="loading loading-spinner loading-lg"></span>
            </div>
        </div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
```

---

## Step 4: Add Edit Modal Endpoint (20 min)

Add to `src/routers/member_frontend.py`:

```python
@router.get("/{member_id}/edit", response_class=HTMLResponse)
async def member_edit_modal(
    request: Request,
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: Return the edit modal content for a member."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = MemberFrontendService(db)
    member = await service.get_member_by_id(member_id)

    if not member:
        return HTMLResponse("Member not found", status_code=404)

    all_statuses = [s.value for s in MemberStatus]
    all_classifications = [c.value for c in MemberClassification]

    return templates.TemplateResponse(
        "members/partials/_edit_modal.html",
        {
            "request": request,
            "member": member,
            "all_statuses": all_statuses,
            "all_classifications": all_classifications,
            "format_classification": service.format_classification,
        }
    )
```

---

## Step 5: Create Edit Modal Partial (25 min)

Create `src/templates/members/partials/_edit_modal.html`:

```html
{# Quick edit modal content - loaded via HTMX #}

<h3 class="font-bold text-lg mb-4">
    Edit Member: {{ member.first_name }} {{ member.last_name }}
</h3>

<form
    hx-post="/members/{{ member.id }}/edit"
    hx-target="#modal-feedback"
    hx-swap="innerHTML"
    class="space-y-4"
>
    <!-- Feedback area -->
    <div id="modal-feedback"></div>

    <!-- Card ID (read-only) -->
    <div class="form-control">
        <label class="label">
            <span class="label-text font-medium">Card ID</span>
        </label>
        <input
            type="text"
            value="{{ member.card_id or 'Not assigned' }}"
            class="input input-bordered bg-base-200"
            disabled
        />
    </div>

    <!-- Name Fields -->
    <div class="grid grid-cols-2 gap-4">
        <div class="form-control">
            <label class="label">
                <span class="label-text font-medium">First Name</span>
            </label>
            <input
                type="text"
                name="first_name"
                value="{{ member.first_name or '' }}"
                class="input input-bordered"
                required
            />
        </div>
        <div class="form-control">
            <label class="label">
                <span class="label-text font-medium">Last Name</span>
            </label>
            <input
                type="text"
                name="last_name"
                value="{{ member.last_name or '' }}"
                class="input input-bordered"
                required
            />
        </div>
    </div>

    <!-- Contact Info -->
    <div class="grid grid-cols-2 gap-4">
        <div class="form-control">
            <label class="label">
                <span class="label-text font-medium">Email</span>
            </label>
            <input
                type="email"
                name="email"
                value="{{ member.email or '' }}"
                class="input input-bordered"
            />
        </div>
        <div class="form-control">
            <label class="label">
                <span class="label-text font-medium">Phone</span>
            </label>
            <input
                type="tel"
                name="phone"
                value="{{ member.phone or '' }}"
                class="input input-bordered"
            />
        </div>
    </div>

    <!-- Status and Classification -->
    <div class="grid grid-cols-2 gap-4">
        <div class="form-control">
            <label class="label">
                <span class="label-text font-medium">Status</span>
            </label>
            <select name="status" class="select select-bordered">
                {% for status in all_statuses %}
                <option value="{{ status }}" {% if member.status.value == status %}selected{% endif %}>
                    {{ status | title }}
                </option>
                {% endfor %}
            </select>
        </div>
        <div class="form-control">
            <label class="label">
                <span class="label-text font-medium">Classification</span>
            </label>
            <select name="classification" class="select select-bordered">
                {% for classification in all_classifications %}
                <option value="{{ classification }}" {% if member.classification and member.classification.value == classification %}selected{% endif %}>
                    {{ format_classification(classification) }}
                </option>
                {% endfor %}
            </select>
        </div>
    </div>

    <!-- Quick Links -->
    <div class="divider">Quick Links</div>

    <div class="flex flex-wrap gap-2">
        <a href="/members/{{ member.id }}" class="btn btn-sm btn-outline">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
            </svg>
            Full Profile
        </a>
        <a href="/members/{{ member.id }}#employment" class="btn btn-sm btn-outline">
            Employment History
        </a>
        <a href="/members/{{ member.id }}#dues" class="btn btn-sm btn-outline">
            Dues History
        </a>
    </div>

    <!-- Modal Actions -->
    <div class="modal-action">
        <button type="button" class="btn btn-ghost" onclick="document.getElementById('edit-modal').close()">
            Cancel
        </button>
        <button type="submit" class="btn btn-primary">
            Save Changes
        </button>
    </div>
</form>

<!-- Member Info Footer -->
<div class="text-xs text-base-content/50 mt-4 pt-4 border-t border-base-200">
    <div class="flex justify-between">
        <span>Member ID: {{ member.id }}</span>
        <span>Created: {{ member.created_at.strftime('%b %d, %Y') }}</span>
    </div>
</div>
```

---

## Step 6: Add More Tests (15 min)

Update `src/tests/test_member_frontend.py`:

```python
"""
Member frontend tests.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestMembersLanding:
    """Tests for members landing page."""

    @pytest.mark.asyncio
    async def test_members_page_requires_auth(self, async_client: AsyncClient):
        """Members page redirects to login when not authenticated."""
        response = await async_client.get("/members", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_members_page_exists(self, async_client: AsyncClient):
        """Members page route exists."""
        response = await async_client.get("/members")
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_members_stats_endpoint(self, async_client: AsyncClient):
        """Stats endpoint exists."""
        response = await async_client.get("/members/stats")
        assert response.status_code in [200, 302, 401]


class TestMembersSearch:
    """Tests for member search functionality."""

    @pytest.mark.asyncio
    async def test_search_endpoint_exists(self, async_client: AsyncClient):
        """Search endpoint exists."""
        response = await async_client.get("/members/search")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_query(self, async_client: AsyncClient):
        """Search accepts query parameter."""
        response = await async_client.get("/members/search?q=john")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_status_filter(self, async_client: AsyncClient):
        """Search accepts status filter."""
        response = await async_client.get("/members/search?status=active")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_classification_filter(self, async_client: AsyncClient):
        """Search accepts classification filter."""
        response = await async_client.get("/members/search?classification=journeyman_wireman")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_pagination(self, async_client: AsyncClient):
        """Search accepts page parameter."""
        response = await async_client.get("/members/search?page=2")
        assert response.status_code in [200, 302, 401]


class TestMemberEdit:
    """Tests for member edit functionality."""

    @pytest.mark.asyncio
    async def test_edit_modal_endpoint(self, async_client: AsyncClient):
        """Edit modal endpoint exists."""
        response = await async_client.get("/members/1/edit")
        assert response.status_code in [200, 302, 401, 404]
```

---

## Step 7: Run Tests

```bash
pytest src/tests/test_member_frontend.py -v

# Expected: 10 tests passing
```

---

## Step 8: Test Manually

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

1. Navigate to `/members`
2. Test search - type in search box, verify table updates
3. Test filters - change status/classification dropdowns
4. Test pagination - click page numbers
5. Click edit icon - verify modal opens
6. Verify badges display correctly

---

## Step 9: Commit

```bash
git add -A
git status

git commit -m "feat(members): Phase 6 Week 5 Session B - Member list with search

- Create _table.html with member columns and pagination
- Create _row.html with status/classification badges
- Create _edit_modal.html for quick editing
- Add edit modal endpoint
- HTMX live search with 300ms debounce
- Filter by status and classification
- Current employer column
- Dues status indicator (simplified)
- Row actions dropdown
- 10 member frontend tests

Columns: card ID, name, classification, status, employer, dues, actions"

git push origin main
```

---

## Session B Checklist

- [ ] Created `_table.html` partial with all columns
- [ ] Created `_row.html` partial with badges
- [ ] Created `_edit_modal.html` partial
- [ ] Added edit modal endpoint
- [ ] HTMX search working
- [ ] Status filter working
- [ ] Classification filter working
- [ ] Pagination working
- [ ] Badges colored correctly
- [ ] Tests passing (10)
- [ ] Committed changes

---

## Files Created This Session

```
src/
├── routers/
│   └── member_frontend.py       # Added edit modal endpoint
├── templates/
│   └── members/
│       ├── index.html           # Added edit modal dialog
│       └── partials/
│           ├── _table.html      # Table with pagination
│           ├── _row.html        # Member row with badges
│           └── _edit_modal.html # Quick edit modal
└── tests/
    └── test_member_frontend.py  # Updated (10 tests)
```

---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session.

### Before Ending This Session:

1. **Scan `/docs/*`** - Review all documentation files
2. **Update existing docs** - Reflect changes, progress, and decisions
3. **Create new docs** - If needed for new components or concepts
4. **ADR Review** - Update or create Architecture Decision Records as necessary
5. **Session log entry** - Record what was accomplished

This ensures historical record-keeping and project continuity ("bus factor" protection).

---

*Session B complete. Proceed to Session C for member detail page with employment history and dues.*
