# Phase 7 Week 26: Books & Registration UI

**Document Type:** Claude Code Instruction Document
**Created:** February 3, 2026
**Spoke:** Spoke 2 (Operations)
**Estimated Time:** 6-8 hours
**Prerequisites:** Phase 7 backend complete (Weeks 20-25), Phase 6 frontend complete (Weeks 1-12)
**Version Target:** v0.9.7-alpha

---

## Objective

Build the staff-facing UI for referral book management and member registration. This is the "data management" side of the dispatch system — setting up and maintaining the out-of-work books that the dispatch workflow (Week 27) operates on.

**End State:** Staff can view all referral books, see who's registered on each book, register/re-sign/resign members, and view registration statistics — all through the existing HTMX + DaisyUI frontend.

---

## Pre-Flight Checklist

Before starting, verify:

```bash
# 1. Docker is running
docker-compose ps

# 2. All tests pass — capture exact count
pytest -v --tb=short 2>&1 | tail -5

# 3. Backend referral API is accessible
curl -s http://localhost:8000/docs | grep -i "referral\|registration\|book"

# 4. You're on main branch, clean state
git status
git pull origin main

# 5. Record starting test count for comparison at end
pytest --co -q 2>&1 | tail -1
```

**IMPORTANT:** Record the starting test count. We'll compare at the end.

---

## Task 0: Discovery — Read the Backend Before Writing Any Frontend

**Time:** 30 minutes

**This is not optional.** Before writing a single template, you must understand exactly what the backend provides. The routers and services built in Weeks 22A-25 define the API contract. Do not assume endpoint paths — read them.

### 0.1 Read the Referral Books Router

```bash
cat src/api/referral_books_api.py
```

Document every endpoint: HTTP method, path, request body, response schema, required permissions. Pay special attention to:
- How books are listed (pagination? filtering?)
- How book statistics are returned (inline? separate endpoint?)
- What settings are configurable per book
- What role permissions are required

### 0.2 Read the Registration Router

```bash
cat src/api/registration_api.py
```

Same exercise. Pay special attention to:
- How registration/re-sign/resign workflows differ
- What validation rules the API enforces
- What member information is included in registration responses
- Status transitions and what triggers them

### 0.3 Read the Backend Services

```bash
cat src/services/referral_book_service.py
cat src/services/book_registration_service.py
```

Understand the business logic layer. The service layer contains validation rules and business constraints that the UI must respect. Note any error conditions that need user-friendly handling.

### 0.4 Read the Relevant Models

```bash
# Find the referral-related models
grep -rl "referral_book\|registration\|ReferralBook\|BookRegistration" src/db/models/
# Then read each one
```

Note the enum values, nullable fields, and relationships. These determine what form fields are required vs optional, what dropdown options exist, and how entities relate.

### 0.5 Read the Relevant Pydantic Schemas

```bash
grep -rl "referral\|registration\|ReferralBook\|BookRegistration" src/schemas/
# Then read each one
```

These define the exact request/response shapes the API expects and returns. Your frontend service must match these.

### 0.6 Create a Discovery Notes File

Create `docs/phase7/week26_api_discovery.md` with your findings:

```markdown
# Week 26 API Discovery Notes

## Referral Books Endpoints
| Method | Path | Purpose | Auth Required |
|--------|------|---------|---------------|
| GET | /api/v1/... | ... | ... |
...

## Registration Endpoints
| Method | Path | Purpose | Auth Required |
|--------|------|---------|---------------|
...

## Key Business Rules Found
- ...

## Form Fields Required
- ...
```

This file serves as your reference for the rest of the week. Don't skip it.

---

## Task 1: Create Directory Structure

**Time:** 5 minutes

```bash
# Create referral template directories
mkdir -p src/templates/referral
mkdir -p src/templates/partials/referral
```

**Expected new files by end of week:**

```
src/
├── services/
│   └── referral_frontend_service.py    # NEW — frontend service wrapper
├── templates/
│   ├── referral/
│   │   ├── landing.html                # Referral system overview
│   │   ├── books.html                  # All books list
│   │   ├── book_detail.html            # Single book detail
│   │   ├── registrations.html          # Registration list
│   │   └── registration_detail.html    # Single registration detail
│   ├── partials/
│   │   └── referral/
│   │       ├── _book_card.html         # Book stats card
│   │       ├── _book_table.html        # Members-on-book table
│   │       ├── _registration_table.html # Registration list table
│   │       ├── _register_modal.html    # Register member form
│   │       ├── _re_sign_modal.html     # Re-sign confirmation
│   │       └── _resign_modal.html      # Resign confirmation
│   └── components/
│       └── _sidebar.html               # MODIFIED — add Referral section
├── routers/
│   └── frontend.py                     # MODIFIED — add referral routes
└── tests/
    └── test_referral_frontend.py       # NEW — frontend tests
```

---

## Task 2: Update Sidebar Navigation

**Time:** 20 minutes

**File:** `src/templates/components/_sidebar.html`

Add a "Referral & Dispatch" section to the existing sidebar. Follow the exact pattern used by existing sections (Members, Training, Dues, etc.).

**New sidebar section to add:**

```html
<!-- Referral & Dispatch -->
<li>
    <details {% if request.url.path.startswith('/referral') or request.url.path.startswith('/dispatch') %}open{% endif %}>
        <summary>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
            </svg>
            Referral & Dispatch
        </summary>
        <ul>
            <li><a href="/referral" class="{% if request.url.path == '/referral' %}active{% endif %}">Overview</a></li>
            <li><a href="/referral/books" class="{% if request.url.path.startswith('/referral/books') %}active{% endif %}">Books</a></li>
            <li><a href="/referral/registrations" class="{% if request.url.path.startswith('/referral/registrations') %}active{% endif %}">Registrations</a></li>
            <li class="menu-title mt-2"><span>Dispatch</span></li>
            <li><a href="/dispatch" class="{% if request.url.path == '/dispatch' %}active{% endif %} text-base-content/50">Dashboard (Week 27)</a></li>
            <li><a href="/dispatch/requests" class="{% if request.url.path.startswith('/dispatch/requests') %}active{% endif %} text-base-content/50">Requests (Week 27)</a></li>
        </ul>
    </details>
</li>
```

**Notes:**
- The Dispatch items are added now but styled as muted/disabled (Week 27 will activate them)
- The `details/summary` pattern matches existing sidebar sections
- Active state highlighting follows existing convention
- Place this section after the existing Dues section in the sidebar order

**Verification:**
```bash
# Start the dev server and visually confirm the sidebar
# Login and check the new section appears, expands, and links are correct
```

---

## Task 3: Create Referral Frontend Service

**Time:** 45 minutes

**File:** `src/services/referral_frontend_service.py`

This follows the exact pattern established by `DuesFrontendService` and other frontend services. It wraps the backend API calls and formats data for Jinja2 templates.

**Pattern to follow:**

```python
"""
Frontend service for Referral Books & Registration UI.

Wraps backend ReferralBookService and BookRegistrationService
calls and formats data for Jinja2 template rendering.
"""

from sqlalchemy.orm import Session
# Import the actual backend services
from src.services.referral_book_service import ReferralBookService
from src.services.book_registration_service import BookRegistrationService


class ReferralFrontendService:
    """
    Provides template-ready data for referral book and registration pages.
    
    Follows the same pattern as DuesFrontendService:
    - Wraps backend service calls
    - Formats data for template rendering
    - Provides badge/status helper methods
    - Handles pagination formatting
    """

    def __init__(self, db: Session):
        self.db = db
        self.book_service = ReferralBookService(db)
        self.registration_service = BookRegistrationService(db)

    # --- Book Methods ---

    def get_books_overview(self):
        """
        Get all books with summary stats for the landing/list page.
        Returns list of books with registration counts, active counts, etc.
        """
        # TODO: Call book_service methods discovered in Task 0
        # Format for template: list of dicts with book info + stats
        pass

    def get_book_detail(self, book_id: int):
        """
        Get single book with full detail including registered members.
        """
        pass

    def get_book_stats(self, book_id: int):
        """
        Get statistics for a single book (for HTMX partial refresh).
        """
        pass

    # --- Registration Methods ---

    def get_registrations(self, filters: dict = None, page: int = 1, per_page: int = 25):
        """
        Get paginated registration list with optional filters.
        Filters may include: book_id, member_id, status, date range.
        """
        pass

    def get_registration_detail(self, registration_id: int):
        """
        Get single registration with member info and history.
        """
        pass

    def register_member(self, data: dict):
        """
        Register a member on a book. Wraps service call with 
        error handling suitable for HTMX response.
        """
        pass

    def re_sign_member(self, registration_id: int):
        """
        Re-sign a member's registration. Returns success/error for HTMX.
        """
        pass

    def resign_member(self, registration_id: int, data: dict = None):
        """
        Resign a member from a book. Returns success/error for HTMX.
        """
        pass

    # --- Badge & Formatting Helpers ---

    @staticmethod
    def book_status_badge(status: str) -> dict:
        """
        Returns DaisyUI badge class and label for book status.
        Follow the same pattern as DuesFrontendService badge helpers.
        """
        badges = {
            "active": {"class": "badge-success", "label": "Active"},
            "frozen": {"class": "badge-warning", "label": "Frozen"},
            "closed": {"class": "badge-error", "label": "Closed"},
        }
        return badges.get(status, {"class": "badge-ghost", "label": status})

    @staticmethod
    def registration_status_badge(status: str) -> dict:
        """
        Returns DaisyUI badge class and label for registration status.
        """
        badges = {
            "active": {"class": "badge-success", "label": "Active"},
            "resigned": {"class": "badge-warning", "label": "Resigned"},
            "dispatched": {"class": "badge-info", "label": "Dispatched"},
            "suspended": {"class": "badge-error", "label": "Suspended"},
            "expired": {"class": "badge-ghost", "label": "Expired"},
        }
        return badges.get(status, {"class": "badge-ghost", "label": status})
```

**CRITICAL:** The actual method implementations must be based on what you discovered in Task 0. The service methods above are stubs showing the pattern. Fill them in using the actual backend service APIs you found.

**Verification:**
```bash
# Import test — make sure the service loads without errors
python -c "from src.services.referral_frontend_service import ReferralFrontendService; print('OK')"
```

---

## Task 4: Create Referral Landing Page

**Time:** 45 minutes

**File:** `src/templates/referral/landing.html`

This is the overview page for the entire referral system. Think of it like the Dues landing page — stats cards at the top, quick actions in the middle, recent activity at the bottom.

**Layout structure:**

```
┌─────────────────────────────────────────────────┐
│ Referral & Dispatch Overview          [Actions]  │
├─────────────────────────────────────────────────┤
│                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐│
│  │ Active   │ │ Total    │ │ Today's  │ │ Open ││
│  │ Books    │ │ Reg'd    │ │ Dispatch │ │ Req  ││
│  │   11     │ │  387     │ │   12     │ │   3  ││
│  └──────────┘ └──────────┘ └──────────┘ └──────┘│
│                                                   │
│  ┌─────────────────────┐  ┌─────────────────────┐│
│  │ Quick Actions       │  │ Books Summary       ││
│  │ ○ Register Member   │  │ Book 1: 45 members  ││
│  │ ○ Process Re-signs  │  │ Book 2: 38 members  ││
│  │ ○ View Dispatch Log │  │ Book 3: 22 members  ││
│  │ ○ Morning Referral  │  │ ...                 ││
│  └─────────────────────┘  └─────────────────────┘│
│                                                   │
└─────────────────────────────────────────────────┘
```

**Key elements:**

1. **Stats Cards** — Use DaisyUI `stat` component. Four cards showing key metrics loaded from the backend. Make these HTMX-refreshable:
   ```html
   <div hx-get="/referral/partials/stats" hx-trigger="load, every 60s" hx-swap="innerHTML">
       <!-- Stats load here -->
   </div>
   ```

2. **Quick Actions** — DaisyUI card with action links. Some actions (like "Morning Referral") will be inactive until Week 27.

3. **Books Summary** — Compact table or card grid showing all books with registration counts. Link each book to its detail page. This can use the `_book_card.html` partial.

**Template pattern:**

```html
{% extends "base.html" %}

{% block title %}Referral & Dispatch{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-6">
    <div>
        <h1 class="text-2xl font-bold">Referral & Dispatch</h1>
        <p class="text-base-content/60">Out-of-work book management and dispatch operations</p>
    </div>
    <div class="flex gap-2">
        <a href="/referral/books" class="btn btn-outline btn-sm">All Books</a>
        <a href="/referral/registrations" class="btn btn-primary btn-sm">Registrations</a>
    </div>
</div>

<!-- Stats Cards -->
<div id="referral-stats" 
     hx-get="/referral/partials/stats" 
     hx-trigger="load" 
     hx-swap="innerHTML"
     class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
    <!-- Loading skeleton -->
    <div class="skeleton h-24 w-full"></div>
    <div class="skeleton h-24 w-full"></div>
    <div class="skeleton h-24 w-full"></div>
    <div class="skeleton h-24 w-full"></div>
</div>

<!-- Quick Actions + Books Summary -->
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Quick Actions (1 column) -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title text-lg">Quick Actions</h2>
            <ul class="menu">
                <li>
                    <a href="#" hx-get="/referral/partials/register-modal" hx-target="#modal-container" hx-swap="innerHTML">
                        Register Member
                    </a>
                </li>
                <li><a href="/referral/registrations?filter=pending_re_sign">Process Re-signs</a></li>
                <li><a href="/referral/books">View All Books</a></li>
                <li><a href="/dispatch" class="text-base-content/40">Morning Referral (Week 27)</a></li>
            </ul>
        </div>
    </div>

    <!-- Books Summary (2 columns) -->
    <div class="col-span-2">
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title text-lg">Books Overview</h2>
                <div id="books-overview"
                     hx-get="/referral/partials/books-overview"
                     hx-trigger="load"
                     hx-swap="innerHTML">
                    <div class="skeleton h-48 w-full"></div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Task 5: Create Books List Page

**Time:** 45 minutes

**File:** `src/templates/referral/books.html`

Full-page list of all 11 referral books with detailed stats. This is the "management" view — more detail than the landing page summary.

**Key features:**
- Table layout with all books (DaisyUI `table` component)
- Each row shows: Book name/number, book type, registration count, active count, status
- Row click or "View" button navigates to book detail
- Filter/search capability via HTMX (filter by status, type)
- Action buttons: "Create Book" (admin only)

**Pattern:**

```html
{% extends "base.html" %}

{% block title %}Referral Books{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-6">
    <div>
        <h1 class="text-2xl font-bold">Referral Books</h1>
        <p class="text-base-content/60">{{ books|length }} books configured</p>
    </div>
    {% if current_user.role in ['admin', 'officer'] %}
    <button class="btn btn-primary btn-sm"
            hx-get="/referral/partials/create-book-modal"
            hx-target="#modal-container"
            hx-swap="innerHTML">
        + New Book
    </button>
    {% endif %}
</div>

<!-- Filter Bar -->
<div class="flex gap-2 mb-4" x-data="{ status: 'all' }">
    <select class="select select-bordered select-sm"
            hx-get="/referral/partials/books-table"
            hx-target="#books-table-container"
            hx-swap="innerHTML"
            hx-include="[name='search']"
            name="status">
        <option value="all">All Statuses</option>
        <option value="active">Active</option>
        <option value="frozen">Frozen</option>
        <option value="closed">Closed</option>
    </select>
    <input type="search" name="search" placeholder="Search books..."
           class="input input-bordered input-sm flex-1"
           hx-get="/referral/partials/books-table"
           hx-target="#books-table-container"
           hx-swap="innerHTML"
           hx-trigger="keyup changed delay:300ms"
           hx-include="[name='status']">
</div>

<!-- Books Table (HTMX target) -->
<div id="books-table-container">
    {% include 'partials/referral/_book_table.html' %}
</div>
{% endblock %}
```

---

## Task 6: Create Book Detail Page

**Time:** 1 hour

**File:** `src/templates/referral/book_detail.html`

Shows a single book with all its members/registrations, settings, and statistics.

**Layout:**

```
┌─────────────────────────────────────────────────┐
│ ← Back to Books    Book 1: Inside Wireman       │
├─────────────────────────────────────────────────┤
│                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ Reg'd    │ │ Active   │ │ Dispatched│         │
│  │   45     │ │   38     │ │    7      │         │
│  └──────────┘ └──────────┘ └──────────┘         │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │ Registered Members             [+ Register] │ │
│  │ Search: [___________]  Filter: [All ▼]      │ │
│  │ ┌────┬──────────┬──────┬────────┬────────┐  │ │
│  │ │ Pos│ Name     │ Date │ Status │ Action │  │ │
│  │ ├────┼──────────┼──────┼────────┼────────┤  │ │
│  │ │ 1  │ Smith, J │ 1/15 │ Active │ [···]  │  │ │
│  │ │ 2  │ Jones, M │ 1/16 │ Active │ [···]  │  │ │
│  │ │ 3  │ Brown, A │ 1/18 │ Active │ [···]  │  │ │
│  │ └────┴──────────┴──────┴────────┴────────┘  │ │
│  │ Showing 1-25 of 45          [< 1 2 >]       │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  ┌──────────────────┐                            │
│  │ Book Settings    │                            │
│  │ Status: Active   │                            │
│  │ Type: ...        │                            │
│  │ [Edit Settings]  │                            │
│  └──────────────────┘                            │
└─────────────────────────────────────────────────┘
```

**Key features:**
- Stats cards at top (HTMX refreshable)
- Registered members table with search, filter, pagination
- Each member row has an action dropdown: View Registration, Re-sign, Resign
- Action dropdown uses HTMX to load modal partials
- Book settings panel (collapsible, admin-only edit)
- Back navigation breadcrumb

**HTMX interactions:**
- Members table refreshes on search/filter without full page reload
- Re-sign/resign actions open confirmation modals
- After re-sign/resign completes, table refreshes automatically via `hx-swap-oob`

---

## Task 7: Create Registration List Page

**Time:** 45 minutes

**File:** `src/templates/referral/registrations.html`

Cross-book view of all registrations. This lets staff search across all books.

**Key features:**
- Filterable by: book, status, member name, date range
- Table columns: Member name, Book, Position, Registration date, Status, Actions
- HTMX-powered search with debounce
- Bulk actions (admin only): re-sign selected, resign selected

---

## Task 8: Create Registration Detail Page

**Time:** 30 minutes

**File:** `src/templates/referral/registration_detail.html`

Shows a single registration record with full history.

**Key features:**
- Member info (name, card number, contact)
- Current registration: book, position, date registered, status
- Registration history timeline (previous registrations, re-signs, dispatches)
- Action buttons: Re-sign, Resign (with confirmation modals)
- Link to member profile (if member detail page exists from Phase 6)

---

## Task 9: Create HTMX Partials

**Time:** 1.5 hours

Create the following partials in `src/templates/partials/referral/`:

### 9.1 `_book_card.html`
Individual book stats card used in the landing page grid. Receives a single book dict.

```html
<!-- Book Stats Card -->
<div class="stat">
    <div class="stat-figure text-primary">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
    </div>
    <div class="stat-title">{{ book.name }}</div>
    <div class="stat-value text-primary">{{ book.active_count }}</div>
    <div class="stat-desc">{{ book.total_count }} registered</div>
</div>
```

### 9.2 `_book_table.html`
Full table of books for the books list page. Receives a `books` list. This is the HTMX swap target for filtering.

### 9.3 `_registration_table.html`
Table of registrations. Receives `registrations` list, `pagination` dict. HTMX swap target for search/filter.

### 9.4 `_register_modal.html`
Modal form for registering a member on a book.

**Fields:**
- Member selector (search by name or card number — use HTMX typeahead)
- Book selector (dropdown of active books)
- Registration notes (optional textarea)
- Submit button

```html
<div class="modal-box">
    <h3 class="font-bold text-lg">Register Member on Book</h3>
    <form hx-post="/referral/registrations"
          hx-target="#books-table-container"
          hx-swap="innerHTML"
          hx-on::after-request="closeModal()">
        
        <!-- Member Search (typeahead) -->
        <div class="form-control mb-4">
            <label class="label"><span class="label-text">Member</span></label>
            <input type="text" name="member_search" placeholder="Search by name or card #..."
                   class="input input-bordered"
                   hx-get="/api/v1/members/search"
                   hx-trigger="keyup changed delay:300ms"
                   hx-target="#member-results"
                   autocomplete="off">
            <div id="member-results" class="mt-1"></div>
            <input type="hidden" name="member_id" id="selected-member-id">
        </div>

        <!-- Book Selection -->
        <div class="form-control mb-4">
            <label class="label"><span class="label-text">Book</span></label>
            <select name="book_id" class="select select-bordered" required>
                <option value="" disabled selected>Select a book...</option>
                {% for book in active_books %}
                <option value="{{ book.id }}">{{ book.name }}</option>
                {% endfor %}
            </select>
        </div>

        <!-- Notes -->
        <div class="form-control mb-4">
            <label class="label"><span class="label-text">Notes (optional)</span></label>
            <textarea name="notes" class="textarea textarea-bordered" rows="2"></textarea>
        </div>

        <div class="modal-action">
            <button type="button" class="btn" onclick="closeModal()">Cancel</button>
            <button type="submit" class="btn btn-primary">Register</button>
        </div>
    </form>
</div>
```

### 9.5 `_re_sign_modal.html`
Confirmation modal for re-signing. Shows member info, current registration, and confirms the action.

### 9.6 `_resign_modal.html`
Confirmation modal for resignation. Shows member info, warns about consequences (position loss), requires reason selection.

---

## Task 10: Add Frontend Routes

**Time:** 30 minutes

**File:** `src/routers/frontend.py` (MODIFY)

Add routes for the referral pages. Follow the exact pattern used by existing frontend routes.

```python
# --- Referral & Dispatch Routes ---

@router.get("/referral")
async def referral_landing(request: Request, db: Session = Depends(get_db)):
    """Referral & Dispatch overview page."""
    service = ReferralFrontendService(db)
    context = {
        "request": request,
        "current_user": get_current_user_from_cookie(request, db),
    }
    return templates.TemplateResponse("referral/landing.html", context)


@router.get("/referral/books")
async def referral_books(request: Request, db: Session = Depends(get_db)):
    """All referral books list."""
    service = ReferralFrontendService(db)
    books = service.get_books_overview()
    context = {
        "request": request,
        "current_user": get_current_user_from_cookie(request, db),
        "books": books,
    }
    return templates.TemplateResponse("referral/books.html", context)


@router.get("/referral/books/{book_id}")
async def referral_book_detail(book_id: int, request: Request, db: Session = Depends(get_db)):
    """Single book detail with registered members."""
    service = ReferralFrontendService(db)
    book = service.get_book_detail(book_id)
    if not book:
        raise HTTPException(status_code=404)
    context = {
        "request": request,
        "current_user": get_current_user_from_cookie(request, db),
        "book": book,
    }
    return templates.TemplateResponse("referral/book_detail.html", context)


@router.get("/referral/registrations")
async def referral_registrations(
    request: Request,
    db: Session = Depends(get_db),
    book_id: int = None,
    status: str = None,
    search: str = None,
    page: int = 1,
):
    """Registration list with filtering."""
    service = ReferralFrontendService(db)
    filters = {"book_id": book_id, "status": status, "search": search}
    registrations = service.get_registrations(filters=filters, page=page)
    context = {
        "request": request,
        "current_user": get_current_user_from_cookie(request, db),
        "registrations": registrations,
        "filters": filters,
    }
    # Return partial for HTMX requests, full page otherwise
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("partials/referral/_registration_table.html", context)
    return templates.TemplateResponse("referral/registrations.html", context)


@router.get("/referral/registrations/{registration_id}")
async def referral_registration_detail(registration_id: int, request: Request, db: Session = Depends(get_db)):
    """Single registration detail."""
    service = ReferralFrontendService(db)
    registration = service.get_registration_detail(registration_id)
    if not registration:
        raise HTTPException(status_code=404)
    context = {
        "request": request,
        "current_user": get_current_user_from_cookie(request, db),
        "registration": registration,
    }
    return templates.TemplateResponse("referral/registration_detail.html", context)


# --- HTMX Partial Routes ---

@router.get("/referral/partials/stats")
async def referral_stats_partial(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: referral stats cards."""
    service = ReferralFrontendService(db)
    stats = service.get_books_overview()
    context = {"request": request, "stats": stats}
    return templates.TemplateResponse("partials/referral/_stats.html", context)


@router.get("/referral/partials/books-overview")
async def referral_books_overview_partial(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: books overview for landing page."""
    service = ReferralFrontendService(db)
    books = service.get_books_overview()
    context = {"request": request, "books": books}
    return templates.TemplateResponse("partials/referral/_books_overview.html", context)


@router.get("/referral/partials/books-table")
async def referral_books_table_partial(
    request: Request,
    db: Session = Depends(get_db),
    status: str = None,
    search: str = None,
):
    """HTMX partial: filtered books table."""
    service = ReferralFrontendService(db)
    books = service.get_books_overview()  # Apply filters
    context = {"request": request, "books": books}
    return templates.TemplateResponse("partials/referral/_book_table.html", context)


@router.get("/referral/partials/register-modal")
async def register_modal_partial(request: Request, db: Session = Depends(get_db)):
    """HTMX partial: register member modal form."""
    service = ReferralFrontendService(db)
    active_books = service.get_books_overview()  # Just active books
    context = {"request": request, "active_books": active_books}
    return templates.TemplateResponse("partials/referral/_register_modal.html", context)


# POST routes for form submissions

@router.post("/referral/registrations")
async def create_registration(request: Request, db: Session = Depends(get_db)):
    """Process member registration form."""
    form = await request.form()
    service = ReferralFrontendService(db)
    result = service.register_member(dict(form))
    # Return updated table partial on success, error partial on failure
    if result.get("success"):
        books = service.get_books_overview()
        context = {"request": request, "books": books}
        return templates.TemplateResponse("partials/referral/_book_table.html", context)
    else:
        context = {"request": request, "error": result.get("error")}
        return templates.TemplateResponse("partials/_error.html", context)


@router.post("/referral/registrations/{registration_id}/re-sign")
async def re_sign_registration(registration_id: int, request: Request, db: Session = Depends(get_db)):
    """Process re-sign action."""
    service = ReferralFrontendService(db)
    result = service.re_sign_member(registration_id)
    # Return flash message partial
    pass


@router.post("/referral/registrations/{registration_id}/resign")
async def resign_registration(registration_id: int, request: Request, db: Session = Depends(get_db)):
    """Process resign action."""
    form = await request.form()
    service = ReferralFrontendService(db)
    result = service.resign_member(registration_id, dict(form))
    # Return flash message partial
    pass
```

**IMPORTANT:** The route patterns above are templates. Adjust the actual API calls and response handling based on what you discovered in Task 0. The backend may use different parameter names or response structures than assumed here.

---

## Task 11: Write Frontend Tests

**Time:** 1 hour

**File:** `src/tests/test_referral_frontend.py`

Follow the test pattern established in `test_frontend.py`. Test:

1. **Page rendering** — each route returns 200 for authenticated users
2. **Auth protection** — unauthenticated access redirects to login
3. **HTMX partials** — partial routes return HTML fragments (not full pages)
4. **Role-based access** — admin-only features hidden for lower roles
5. **Form submission** — registration creates records, re-sign/resign change status

**Minimum test targets:**

```python
class TestReferralFrontend:
    """Tests for referral frontend routes and HTMX interactions."""

    def test_referral_landing_renders(self):
        """Landing page should render for authenticated staff."""
        pass

    def test_referral_landing_requires_auth(self):
        """Landing page should redirect to login if not authenticated."""
        pass

    def test_books_list_renders(self):
        """Books list page should show all books."""
        pass

    def test_books_list_htmx_filter(self):
        """HTMX filter should return partial table."""
        pass

    def test_book_detail_renders(self):
        """Book detail should show members and stats."""
        pass

    def test_book_detail_404_for_invalid(self):
        """Invalid book ID should return 404."""
        pass

    def test_registrations_list_renders(self):
        """Registrations list should show with filters."""
        pass

    def test_registrations_htmx_search(self):
        """HTMX search should return filtered partial."""
        pass

    def test_registration_detail_renders(self):
        """Registration detail should show member info."""
        pass

    def test_register_modal_partial(self):
        """Register modal should return form HTML."""
        pass

    def test_create_registration_success(self):
        """POST should create registration and return updated table."""
        pass

    def test_re_sign_registration(self):
        """Re-sign should update registration status."""
        pass

    def test_resign_registration(self):
        """Resign should update registration with reason."""
        pass

    def test_sidebar_shows_referral_section(self):
        """Sidebar should include Referral & Dispatch section."""
        pass

    def test_admin_sees_create_book_button(self):
        """Admin should see 'New Book' button on books list."""
        pass

    def test_staff_no_create_book_button(self):
        """Staff should NOT see 'New Book' button."""
        pass
```

**Target: 15-20 new tests**

---

## Task 12: Commit and Document

**Time:** 15 minutes

### 12.1 Run Full Test Suite

```bash
pytest -v --tb=short
```

Record the new total. Compare against starting count from Pre-Flight.

### 12.2 Git Commit

```bash
git add -A
git commit -m "feat(frontend): Phase 7 Week 26 - Books & Registration UI

- Add Referral & Dispatch section to sidebar navigation
- Add ReferralFrontendService with book and registration methods
- Add referral landing page with stats cards and books overview
- Add books list page with HTMX filtering and search
- Add book detail page with registered members table
- Add registration list page with cross-book search
- Add registration detail page with history timeline
- Add HTMX partials (book cards, tables, modals)
- Add register/re-sign/resign modal workflows
- Add referral frontend routes and HTMX partial routes
- Add XX new frontend tests (YYY total)

Consumes: referral_books_api, registration_api (Phase 7 Weeks 22A-22B)
Stack: Jinja2 + HTMX + DaisyUI + Alpine.js"
```

### 12.3 Update CHANGELOG.md

```markdown
### Added
- **Phase 7 Week 26: Books & Registration UI**
  * Referral & Dispatch sidebar navigation section
  * ReferralFrontendService for template data formatting
  * Referral landing page with stats dashboard
  * Books list with HTMX filtering and search
  * Book detail with registered members, stats, settings
  * Registration list with cross-book search
  * Registration detail with history timeline
  * Register/re-sign/resign modal workflows
  * XX new frontend tests
```

---

## Summary: Week 26 Deliverables

| Item | Status |
|------|--------|
| Task 0: API Discovery | ⬜ |
| Task 1: Directory structure | ⬜ |
| Task 2: Sidebar navigation update | ⬜ |
| Task 3: ReferralFrontendService | ⬜ |
| Task 4: Referral landing page | ⬜ |
| Task 5: Books list page | ⬜ |
| Task 6: Book detail page | ⬜ |
| Task 7: Registration list page | ⬜ |
| Task 8: Registration detail page | ⬜ |
| Task 9: HTMX partials (6 files) | ⬜ |
| Task 10: Frontend routes | ⬜ |
| Task 11: Frontend tests (15-20) | ⬜ |
| Task 12: Commit + CHANGELOG | ⬜ |

**Estimated Total Time:** 6-8 hours

---

## Week 27 Preview

Week 27 builds the dispatch workflow UI on top of the book/registration foundation built this week:
- Dispatch dashboard with today's activity
- Labor request management (receive, fill, cancel)
- Job bid processing (morning referral)
- Queue management
- Enforcement dashboard (suspensions, violations)

---

## The 11 Referral Books — Quick Reference

For context when building the UI. These are the books in the IBEW Local 46 system:

| # | Book Name | Typical Use |
|---|-----------|-------------|
| 1 | Inside Wireman (JW) | Journeyman wiremen — primary book |
| 2 | Inside Wireman (Apprentice) | Apprentice electricians |
| 3 | Sound & Communication (JW) | Low-voltage/data specialists |
| 4 | Sound & Communication (Apprentice) | Low-voltage apprentices |
| 5 | Residential Wireman | Residential specialists |
| 6 | Residential Apprentice | Residential apprentices |
| 7 | Installer Technician | Install technicians |
| 8 | VDV Installer | Voice/Data/Video installers |
| 9 | Limited Energy Technician | Limited energy work |
| 10 | Traveler | Out-of-area members |
| 11 | Specialty/Other | Catch-all for specialty classifications |

**Note:** The exact book names and numbers should be verified against the actual `ReferralBook` seed data or enum in the codebase. The list above is approximate.

---

*Week 26 Instruction Document — Spoke 2 (Operations)*
*Created: February 3, 2026*
*UnionCore (IP2A-Database-v2)*
