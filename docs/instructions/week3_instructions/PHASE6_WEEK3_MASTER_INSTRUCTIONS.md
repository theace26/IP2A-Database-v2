# Phase 6 Week 3: Staff Management

**Created:** January 29, 2026
**Estimated Time:** 6-8 hours (3 sessions)
**Prerequisites:** Week 2 complete (cookie auth, dashboard with real data)

---

## Overview

Week 3 builds the first full CRUD interface with search, filtering, pagination, and modal editing:

| Session | Focus | Time |
|---------|-------|------|
| A | User list + search/filter + pagination | 2-3 hrs |
| B | Quick edit modal + role assignment | 2-3 hrs |
| C | Account actions + full detail page + tests | 2-3 hrs |

---

## Week 3 Objectives

### Must Have (MVP)
- [ ] User list page with table layout
- [ ] Search by email, name, card ID
- [ ] Filter by role and account status
- [ ] Pagination (20 per page)
- [ ] Quick edit modal (email, roles, status)
- [ ] Role assignment with multi-select checkboxes
- [ ] Lock/unlock account
- [ ] Reset password (trigger email)
- [ ] Delete account (soft delete)
- [ ] Full audit logging on all actions
- [ ] 15+ new tests

### Nice to Have
- [ ] Bulk actions (select multiple)
- [ ] Export to CSV
- [ ] Sort by column headers

---

## Architecture Overview

### Page Structure

```
/staff                    → User list page (main)
/staff/search             → HTMX partial (table body only)
/staff/{id}               → Full detail page
/staff/{id}/edit          → HTMX partial (modal content)
/staff/{id}/roles         → HTMX partial (role update)
/staff/{id}/lock          → POST action (toggle lock)
/staff/{id}/reset-password → POST action (send reset email)
/staff/{id}/delete        → POST action (soft delete)
```

### Component Hierarchy

```
templates/
└── staff/
    ├── index.html           # Main list page
    ├── detail.html          # Full detail page
    └── partials/
        ├── _table.html      # User table (HTMX target)
        ├── _row.html        # Single row template
        ├── _edit_modal.html # Quick edit modal content
        ├── _pagination.html # Pagination controls
        └── _filters.html    # Filter dropdowns
```

### New Files Summary

| File | Purpose |
|------|---------|
| `src/services/staff_service.py` | User CRUD + search logic |
| `src/routers/staff.py` | Staff management routes |
| `src/templates/staff/index.html` | User list page |
| `src/templates/staff/detail.html` | Full detail page |
| `src/templates/staff/partials/*.html` | HTMX partials |
| `src/templates/components/_pagination.html` | Reusable pagination |
| `src/tests/test_staff.py` | Staff management tests |

---

## Data Model Reference

### User Model (Expected Fields)

```python
class User(Base):
    __tablename__ = "users"
    
    id: int
    email: str
    hashed_password: str
    first_name: str | None
    last_name: str | None
    member_id: int | None          # FK to Member if linked
    is_active: bool = True
    is_locked: bool = False
    failed_login_attempts: int = 0
    locked_until: datetime | None
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    roles: list[Role]              # Many-to-many via user_roles
    member: Member | None          # Optional link to Member
```

### Role Model

```python
class Role(Base):
    __tablename__ = "roles"
    
    id: int
    name: str                      # admin, officer, staff, organizer, instructor, member
    description: str | None
```

### Available Roles (from seed data)

| Role | Description |
|------|-------------|
| admin | Full system access |
| officer | Union officers |
| staff | Office staff |
| organizer | Field organizers (SALTing) |
| instructor | Training instructors |
| member | Basic member access |

---

## HTMX Patterns Used

### Live Search with Debounce
```html
<input 
    type="search"
    name="q"
    hx-get="/staff/search"
    hx-trigger="input changed delay:300ms, search"
    hx-target="#user-table-body"
    hx-include="[name='role'], [name='status']"
/>
```

### Modal Loading
```html
<button 
    hx-get="/staff/123/edit"
    hx-target="#modal-container"
    hx-swap="innerHTML"
    onclick="document.getElementById('edit-modal').showModal()"
>
    Edit
</button>
```

### Form Submission with Feedback
```html
<form 
    hx-post="/staff/123/roles"
    hx-target="#role-feedback"
    hx-swap="innerHTML"
    hx-indicator="#save-spinner"
>
```

### Row Update After Action
```html
<button
    hx-post="/staff/123/lock"
    hx-target="closest tr"
    hx-swap="outerHTML"
>
    Lock Account
</button>
```

---

## Audit Logging Requirements

Every action must be logged:

| Action | Entity Type | Changes Captured |
|--------|-------------|------------------|
| View user list | `user` | READ (optional, can be noisy) |
| View user detail | `user` | READ |
| Update user | `user` | Before/after for each field |
| Assign role | `user_role` | Roles added |
| Remove role | `user_role` | Roles removed |
| Lock account | `user` | `is_locked: false → true` |
| Unlock account | `user` | `is_locked: true → false` |
| Reset password | `user` | `password_reset_requested: true` |
| Delete account | `user` | DELETE (soft delete) |

---

## Session Breakdown

### Session A: User List + Search (Document 1)
1. Create `staff_service.py` with search/filter/paginate
2. Create `staff.py` router
3. Create `staff/index.html` list page
4. Create `_table.html` and `_row.html` partials
5. Create `_pagination.html` component
6. Wire up HTMX search with debounce
7. Test search/filter manually

### Session B: Quick Edit Modal (Document 2)
1. Create `_edit_modal.html` partial
2. Add role checkboxes with multi-select
3. Add status toggle (active/locked)
4. Add save endpoint with validation
5. Add role update endpoint
6. Wire up modal with HTMX
7. Add toast notifications on success

### Session C: Account Actions + Tests (Document 3)
1. Create `detail.html` full detail page
2. Add lock/unlock endpoint
3. Add reset password endpoint
4. Add delete endpoint (soft delete)
5. Add audit logging to all actions
6. Write comprehensive tests (15+)
7. Update documentation

---

## Success Criteria

Week 3 is complete when:
- [ ] User list displays with search/filter/pagination
- [ ] Quick edit modal opens and saves changes
- [ ] Role assignment works with checkboxes
- [ ] Lock/unlock toggles account status
- [ ] Reset password triggers (logs for now, email later)
- [ ] Delete soft-deletes the account
- [ ] All actions are audit logged
- [ ] All tests pass (200+ total)
- [ ] Browser testing confirms full flow

---

## Quick Reference

### DaisyUI Table Classes
```html
<table class="table table-zebra">
  <thead>
    <tr class="bg-base-200">
      <th>Column</th>
    </tr>
  </thead>
  <tbody id="user-table-body">
    <tr class="hover">
      <td>Data</td>
    </tr>
  </tbody>
</table>
```

### DaisyUI Modal
```html
<dialog id="edit-modal" class="modal">
  <div class="modal-box">
    <h3 class="font-bold text-lg">Title</h3>
    <div id="modal-container">
      <!-- HTMX loads content here -->
    </div>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>
```

### DaisyUI Checkbox Group
```html
<div class="form-control">
  <label class="label cursor-pointer justify-start gap-3">
    <input type="checkbox" name="roles" value="admin" class="checkbox checkbox-primary" />
    <span class="label-text">Admin</span>
  </label>
</div>
```

### DaisyUI Badge for Roles
```html
<div class="flex flex-wrap gap-1">
  <span class="badge badge-primary badge-sm">admin</span>
  <span class="badge badge-secondary badge-sm">staff</span>
</div>
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

*Proceed to Document 1 (Session A) to begin implementation.*
