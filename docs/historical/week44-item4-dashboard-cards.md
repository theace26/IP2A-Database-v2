# UnionCore — Week 44: Replace Dashboard Cards
**Spoke:** Spoke 3: Infrastructure (Cross-Cutting UI + ⚠️ Dashboard service methods touch domain queries — see scope notes)
**Phase:** UI Enhancement Bundle — Item 4 of 5
**Estimated Effort:** 2–3 hours
**Prerequisites:** Items 1 + 3A + 3B committed (developer role needed for testing RBAC card visibility)
**Source:** Hub Handoff Document (February 10, 2026)

---

## Context

The dashboard currently shows 4 stat cards. We're removing "Active Members" and adding 3 new operational cards, bringing the total to 6.

**Current cards (4):**
1. ~~Active Members~~ → REMOVE
2. Active Students → KEEP
3. Pending Grievances → KEEP
4. Dues MTD → KEEP

**New cards (6 total):**
1. Open Dispatch Requests (NEW)
2. Members on Book (NEW)
3. Upcoming Expirations (NEW)
4. Active Students (existing)
5. Pending Grievances (existing)
6. Dues MTD (existing)

### Scope Note

The **dashboard template layout and card rendering** belong to Spoke 3. The **service methods that query domain-specific data** (dispatch counts, book registrations, certifications) arguably belong to the domain Spokes. However, the Hub handoff assigns all of this here. We'll implement the queries, but keep them in the DashboardService (or equivalent aggregation service) rather than in domain-specific services. If the queries need to change due to domain logic evolution, the owning Spoke will update them.

---

## Pre-Flight Checklist

- [ ] `git status` is clean
- [ ] Create and checkout branch: `git checkout -b feature/dashboard-cards`
- [ ] Items 1, 3A, 3B are merged and available
- [ ] App starts without errors
- [ ] Record current test count: `pytest --tb=short -q 2>&1 | tail -5`
- [ ] Login as developer and confirm dashboard loads

---

## Step 1: Discover Current Dashboard Implementation

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

**Open Dispatch Requests:**
```bash
grep -rn "class.*LaborRequest\|class.*DispatchRequest" src/models/ --include="*.py"
grep -rn "status.*open\|status.*pending" src/models/ --include="*.py"
```
→ Need to find: model name, status field name, and what values represent "open" and "pending"

**Members on Book:**
```bash
grep -rn "class.*BookRegistration\|class.*Registration" src/models/ --include="*.py"
grep -rn "status.*active" src/models/ --include="*.py" | grep -i "book\|registration\|referral"
```
→ Need to find: model name, status field name, what value represents "active"

**Upcoming Expirations:**
```bash
grep -rn "class.*Certification\|expir" src/models/ --include="*.py"
```
→ Need to find: model name, expiration date field name

**If any model/table doesn't exist**, document this as a blocker. Stub the card with placeholder data (`N/A` or `—`) and add a code comment: `# TODO: Implement when [model] is created (see Spoke [N])`. Do NOT create new models — that's out of scope per the handoff.

---

## Step 2: Add Dashboard Service Methods

In the dashboard service (or create one if it doesn't exist), add three new methods. **Match the existing code style exactly.**

### Method 1: Open Dispatch Requests

```python
def get_open_dispatch_count(self, db: Session) -> int:
    """Count labor requests with open/pending status."""
    # Adapt to actual model name and field names
    return db.query(LaborRequest).filter(
        LaborRequest.status.in_(["open", "pending"])
    ).count()
```

### Method 2: Members on Book

```python
def get_members_on_book_count(self, db: Session) -> int:
    """Count active registrations across all referral books."""
    # Adapt to actual model name and field names
    return db.query(BookRegistration).filter(
        BookRegistration.status == "active"
    ).count()
```

### Method 3: Upcoming Expirations

```python
def get_upcoming_expirations_count(self, db: Session, days: int = 30) -> int:
    """Count certifications expiring within N days."""
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() + timedelta(days=days)
    # Adapt to actual model name and field names
    return db.query(Certification).filter(
        Certification.expiration_date.between(datetime.utcnow(), cutoff)
    ).count()
```

**Adapt all three to:**
- The actual model names (found in Step 1)
- The actual field names
- The actual status values
- The existing code style (import patterns, type hints, docstring format, session handling)

If a model doesn't exist, create a stubbed method:

```python
def get_upcoming_expirations_count(self, db: Session, days: int = 30) -> int:
    """Count certifications expiring within N days.

    TODO: Implement when Certification model is created (Spoke 1/2).
    Currently returns 0 as placeholder.
    """
    return 0
```

---

## Step 3: Update the Dashboard Route Handler

The route handler needs to call the new service methods and pass the results to the template.

Find the route handler (located in Step 1) and add:

```python
# Add to existing dashboard route handler
open_dispatch_count = dashboard_service.get_open_dispatch_count(db)
members_on_book_count = dashboard_service.get_members_on_book_count(db)
upcoming_expirations_count = dashboard_service.get_upcoming_expirations_count(db)

# Pass to template (add to existing context dict)
context.update({
    "open_dispatch_count": open_dispatch_count,
    "members_on_book_count": members_on_book_count,
    "upcoming_expirations_count": upcoming_expirations_count,
})
```

**Match the existing pattern** for how the route calls service methods and passes data to the template.

---

## Step 4: Update the Dashboard Template

### 4a: Remove Active Members Card

Find and delete the "Active Members" card entirely. Remove both the HTML and any template logic associated with it.

### 4b: Create the New Card Layout

Replace the card grid with a 6-card responsive layout:

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

    {# Row 1: New operational cards #}

    {% if effective_role in ['admin', 'officer', 'staff', 'developer'] %}
    <div class="stat bg-base-100 shadow rounded-box p-4">
        {# Use whatever icon pattern existing cards use #}
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

    {# Row 2: Existing cards (kept) #}

    {% if effective_role in ['admin', 'officer', 'staff', 'instructor', 'developer'] %}
    {# Active Students card — KEEP EXISTING MARKUP but fix subtitle if needed #}
    ...
    {% endif %}

    {% if effective_role in ['admin', 'officer', 'staff', 'developer'] %}
    {# Pending Grievances card — KEEP EXISTING MARKUP #}
    ...
    {% endif %}

    {% if effective_role in ['admin', 'officer', 'developer'] %}
    {# Dues MTD card — KEEP EXISTING MARKUP #}
    ...
    {% endif %}

</div>
```

**CRITICAL: Match the existing card HTML pattern.** The above is a template — your actual implementation must use the same classes, structure, and icon patterns as the existing cards. If existing cards use `<div class="card">` instead of `<div class="stat">`, follow their pattern.

### Card RBAC Matrix

| Card | Visible to |
|------|-----------|
| Open Dispatch Requests | `admin`, `officer`, `staff`, `developer` |
| Members on Book | `admin`, `officer`, `staff`, `developer` |
| Upcoming Expirations | `admin`, `officer`, `staff`, `instructor`, `developer` |
| Active Students | `admin`, `officer`, `staff`, `instructor`, `developer` |
| Pending Grievances | `admin`, `officer`, `staff`, `developer` |
| Dues MTD | `admin`, `officer`, `developer` |

Use `effective_role` (not `current_user.role`) so View As impersonation works correctly.

When a card is not visible to the current role, it must not render in the DOM (use `{% if %}`, not CSS hiding). The grid will naturally adjust — a 3-column grid with 2 cards just shows one row of 2.

### 4c: Fix the Active Students Subtitle

The handoff notes that the "Active Students" card subtitle ("+2690 this month") may be showing seed data counts rather than actual new-this-month records.

Check the dashboard service method that provides the students subtitle:

```bash
grep -rn "student.*count\|student.*month\|active_students" src/services/ --include="*.py"
```

If the subtitle is calculated by counting records `created_at` in the current month, verify the query is correct:

```python
# Should be something like:
from datetime import datetime
current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
new_this_month = db.query(Student).filter(Student.created_at >= current_month_start).count()
```

If the subtitle is just a hardcoded string or counts all records, fix it. If the fix is complex or unclear, change the subtitle to something static and accurate like "In current cohorts" and add a TODO comment.

---

## Step 5: Write Tests

### Service Method Tests

```python
def test_get_open_dispatch_count(db_session, dashboard_service):
    """Open dispatch count returns correct number."""
    # Create test labor requests with various statuses
    # Assert count matches expected

def test_get_open_dispatch_count_zero(db_session, dashboard_service):
    """Returns 0 when no open/pending requests exist."""

def test_get_members_on_book_count(db_session, dashboard_service):
    """Members on book count returns active registrations."""

def test_get_members_on_book_count_excludes_inactive(db_session, dashboard_service):
    """Inactive registrations are not counted."""

def test_get_upcoming_expirations_count(db_session, dashboard_service):
    """Upcoming expirations count returns certs expiring within 30 days."""

def test_get_upcoming_expirations_excludes_past(db_session, dashboard_service):
    """Already-expired certifications are not counted."""

def test_get_upcoming_expirations_excludes_far_future(db_session, dashboard_service):
    """Certifications expiring beyond 30 days are not counted."""
```

### Dashboard Route Tests

```python
def test_dashboard_loads_for_admin(admin_client):
    """Dashboard loads successfully for admin role."""
    response = admin_client.get("/")  # or /dashboard — check actual URL
    assert response.status_code == 200

def test_dashboard_contains_new_cards(admin_client):
    """Dashboard HTML contains the new card titles."""
    response = admin_client.get("/")
    assert "Open Dispatch Requests" in response.text
    assert "Members on Book" in response.text
    assert "Upcoming Expirations" in response.text

def test_dashboard_no_active_members_card(admin_client):
    """Active Members card has been removed."""
    response = admin_client.get("/")
    assert "Active Members" not in response.text

def test_dashboard_card_rbac_organizer(organizer_client):
    """Organizer should not see dispatch or grievance cards."""
    response = organizer_client.get("/")
    assert "Open Dispatch Requests" not in response.text
    assert "Pending Grievances" not in response.text
```

**Adapt test fixtures to match existing patterns.** If `admin_client` and `organizer_client` fixtures don't exist, create them following the same pattern as the `developer_client` from Item 3A.

For stubbed methods (where the model doesn't exist), test that they return 0:

```python
def test_stubbed_expirations_returns_zero(db_session, dashboard_service):
    """Stubbed method returns 0 until Certification model exists."""
    assert dashboard_service.get_upcoming_expirations_count(db_session) == 0
```

---

## Step 6: Verify

```bash
# Run full test suite
pytest --tb=short -q

# Verify test count increased
```

### Manual Verification

1. **Login as developer (no impersonation)** → All 6 cards visible, correct counts
2. **View As Admin** → All 6 cards visible
3. **View As Officer** → All 6 cards visible (officers see everything except maybe developer-only items)
4. **View As Staff** → 5 cards visible (Dues MTD hidden — only admin/officer)
5. **View As Instructor** → 2 cards visible (Active Students + Upcoming Expirations)
6. **View As Organizer** → 0 or minimal cards (check what organizers should see on the dashboard)
7. **View As Member** → 0 cards (or whatever the minimum is)
8. **Responsive layout** → Resize browser: 3 cols on desktop, 2 on tablet, 1 on mobile
9. **No "Active Members"** → The phrase should not appear anywhere on the dashboard
10. **Card values** → Each card shows a real number (or 0 if no data). No errors, no "undefined", no NaN.

---

## Anti-Patterns to Avoid

- **DO NOT** create new database models for missing tables. Stub and document.
- **DO NOT** hide cards with CSS (`display: none`). Use Jinja2 `{% if %}` so they're not in the DOM.
- **DO NOT** hardcode card counts. Always query the database.
- **DO NOT** change the grid layout to something other than `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`. The handoff specifies this layout.
- **DO NOT** remove the "Active Students" card. Only remove "Active Members".
- **DO NOT** leave any reference to "Active Members" in the template, route handler, or service.
- **DO NOT** add complex card interactions (click-to-expand, hover tooltips, etc.). These are simple stat cards.

---

## Acceptance Criteria

- [ ] "Active Members" card completely removed from dashboard
- [ ] "Open Dispatch Requests" card added with correct count (or stubbed)
- [ ] "Members on Book" card added with correct count (or stubbed)
- [ ] "Upcoming Expirations" card added with correct count and warning styling (or stubbed)
- [ ] 6-card responsive grid: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
- [ ] RBAC: Cards only render for authorized roles (using `effective_role`)
- [ ] Active Students subtitle shows meaningful data (not seed data artifacts)
- [ ] Dashboard service has 3 new methods with tests
- [ ] All existing tests still pass
- [ ] New tests written and passing (target: 8-12 new tests)
- [ ] Stubbed methods clearly documented with TODO comments

---

## File Manifest

**Modified files:**
- `src/services/dashboard_service.py` (or equivalent) — 3 new methods
- `src/templates/dashboard/index.html` (or equivalent) — card grid overhaul
- Dashboard route handler — pass new data to template
- Active Students subtitle logic (if fix needed)

**Created files:**
- `tests/test_dashboard_cards.py` (or add to existing dashboard test file)

**Deleted files:**
- None

---

## Git Commit Message

```
feat(dashboard): replace Active Members card with operational cards

- Remove Active Members stat card
- Add Open Dispatch Requests card (admin/officer/staff)
- Add Members on Book card (admin/officer/staff)
- Add Upcoming Expirations card (admin/officer/staff/instructor)
- 6-card responsive grid (3-col desktop, 2-col tablet, 1-col mobile)
- RBAC: cards render only for authorized roles via effective_role
- Fix Active Students subtitle to show meaningful data
- Add dashboard service methods with tests
- Spoke 3: Infrastructure (Cross-Cutting UI)
```

---

## Session Close-Out

After committing:

1. Update `CLAUDE.md` — note dashboard changes, new test count, version bump
2. Update `CHANGELOG.md` — add entry
3. Update any docs referencing dashboard layout
4. **Blocker documentation:** If any models were stubbed (especially Certification for expirations), create a note in `/docs/` listing what needs to be implemented and by which Spoke
5. **Cross-Spoke Impact Note:** Dashboard now depends on `LaborRequest.status`, `BookRegistration.status`, and `Certification.expiration_date` fields. If domain Spokes rename these fields or change status values, the dashboard will break. Generate a handoff note.

---

*Spoke 3: Infrastructure — Item 4 of UI Enhancement Bundle*
*UnionCore v0.9.16-alpha*
