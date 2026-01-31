# Week 11 Session C: Inline History & Member Notes UI

**Project:** UnionCore (IP2A Database v2)
**Phase:** 6 - Frontend Implementation
**Week:** 11 - Audit Trail & Member History UI
**Session:** C (of 3)
**Estimated Duration:** 2.5-3 hours
**Branch:** `develop` (ALWAYS work on develop, main is frozen for Railway demo)
**Prerequisite:** Week 11 Session B complete (Audit UI & Role Permissions)

---

## Session Overview

This session adds inline audit history to entity detail pages and implements the member notes UI. Users will see recent activity directly on member/student/grievance pages, and staff can add/view notes with visibility controls.

---

## Pre-Session Checklist

```bash
# 1. Switch to develop branch
git checkout develop
git pull origin develop

# 2. Start environment
docker-compose up -d

# 3. Verify tests pass
pytest -v --tb=short

# 4. Verify Session B complete
# - /admin/audit-logs page works
# - Role-based filtering working
# - Sensitive field redaction working
pytest src/tests/test_audit_frontend.py -v
```

---

## Tasks

### Task 1: Create Reusable Audit History Partial (30 min)

**Goal:** Create a reusable component for displaying entity audit history inline.

**File:** `src/templates/components/_audit_history.html`

```html
{# 
  Reusable audit history partial for inline display on entity pages.
  
  Required variables:
    - logs: List of audit log entries
    - table_name: Name of the table (e.g., "members")
    - record_id: ID of the record
    
  Optional variables:
    - show_header: Whether to show "Recent Activity" header (default: true)
    - show_view_all: Whether to show "View Full History" link (default: true)
    - max_display: Max items to display before "show more" (default: 5)
#}

{% set show_header = show_header | default(true) %}
{% set show_view_all = show_view_all | default(true) %}
{% set max_display = max_display | default(5) %}

<div class="audit-history-widget">
    {% if show_header %}
    <div class="flex justify-between items-center mb-3">
        <h3 class="text-lg font-semibold">Recent Activity</h3>
        {% if show_view_all %}
        <a href="/admin/audit-logs?table_name={{ table_name }}&record_id={{ record_id }}" 
           class="link link-primary text-sm">
            View Full History →
        </a>
        {% endif %}
    </div>
    {% endif %}

    {% if logs and logs|length > 0 %}
    <ul class="timeline timeline-vertical timeline-compact">
        {% for log in logs[:max_display] %}
        <li>
            {% if not loop.first %}<hr>{% endif %}
            <div class="timeline-start text-xs text-gray-500">
                {{ log.changed_at[:16].replace('T', ' ') if log.changed_at else '' }}
            </div>
            <div class="timeline-middle">
                {% if log.action == 'CREATE' %}
                <span class="text-success">●</span>
                {% elif log.action == 'UPDATE' %}
                <span class="text-warning">●</span>
                {% elif log.action == 'DELETE' %}
                <span class="text-error">●</span>
                {% elif log.action == 'READ' %}
                <span class="text-info">●</span>
                {% else %}
                <span class="text-gray-400">●</span>
                {% endif %}
            </div>
            <div class="timeline-end timeline-box py-2 px-3">
                <div class="text-sm">
                    <span class="font-medium">{{ log.changed_by or 'System' }}</span>
                    {% if log.action == 'CREATE' %}
                    <span class="text-success">created</span> record
                    {% elif log.action == 'UPDATE' %}
                    <span class="text-warning">updated</span>
                    {% if log.changed_fields %}
                    <span class="text-gray-600">{{ log.changed_fields | join(', ') }}</span>
                    {% else %}
                    record
                    {% endif %}
                    {% elif log.action == 'DELETE' %}
                    <span class="text-error">deleted</span> record
                    {% elif log.action == 'READ' %}
                    <span class="text-info">viewed</span> record
                    {% else %}
                    performed {{ log.action }}
                    {% endif %}
                </div>
                {% if log.notes %}
                <div class="text-xs text-gray-500 mt-1">{{ log.notes }}</div>
                {% endif %}
            </div>
            {% if not loop.last %}<hr>{% endif %}
        </li>
        {% endfor %}
    </ul>

    {% if logs|length > max_display %}
    <div class="text-center mt-3">
        <a href="/admin/audit-logs?table_name={{ table_name }}&record_id={{ record_id }}"
           class="btn btn-sm btn-ghost">
            Show {{ logs|length - max_display }} more...
        </a>
    </div>
    {% endif %}

    {% else %}
    <div class="text-center text-gray-500 py-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-sm">No activity recorded yet</p>
    </div>
    {% endif %}
</div>
```

---

### Task 2: Add Inline History to Member Detail Page (45 min)

**Goal:** Show recent audit activity directly on member detail page.

#### 2.1 Update Member Detail Route

**File:** `src/routers/member_frontend.py`

Add to the member detail route:

```python
from src.services.audit_frontend_service import audit_frontend_service

@router.get("/{member_id}", response_class=HTMLResponse)
async def member_detail(
    request: Request,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    """Member detail page with inline audit history."""
    member = member_service.get_by_id(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Get recent audit history for this member
    audit_history = audit_frontend_service.get_entity_history(
        db=db,
        current_user=current_user,
        table_name="members",
        record_id=str(member_id),
        limit=10,
    )
    
    # Get member notes (with visibility filtering)
    from src.services.member_note_service import member_note_service
    notes = member_note_service.get_by_member(db, member_id, current_user)
    
    return templates.TemplateResponse(
        "members/detail.html",
        {
            "request": request,
            "current_user": current_user,
            "page_title": f"Member: {member.first_name} {member.last_name}",
            "member": member,
            "audit_history": audit_history,
            "notes": notes,
            # ... other existing context variables ...
        }
    )
```

#### 2.2 Update Member Detail Template

**File:** `src/templates/members/detail.html`

Add after the main member info section:

```html
{% extends "base_auth.html" %}

{% block content %}
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Main Content (2 columns) -->
    <div class="lg:col-span-2 space-y-6">
        <!-- Existing member info card -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <!-- ... existing member details ... -->
            </div>
        </div>

        <!-- Existing tabs (Employment, Dues, etc.) -->
        <!-- ... -->
    </div>

    <!-- Sidebar (1 column) -->
    <div class="space-y-6">
        <!-- Notes Section -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="card-title text-lg">Notes</h2>
                    <button class="btn btn-sm btn-primary" 
                            onclick="document.getElementById('add-note-modal').showModal()">
                        + Add Note
                    </button>
                </div>
                
                {% include "members/partials/_notes_list.html" %}
            </div>
        </div>

        <!-- Audit History Section -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div hx-get="/admin/audit-logs/entity/members/{{ member.id }}"
                     hx-trigger="load"
                     hx-swap="innerHTML">
                    <div class="flex justify-center py-4">
                        <span class="loading loading-spinner"></span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Add Note Modal -->
{% include "members/partials/_add_note_modal.html" %}
{% endblock %}
```

---

### Task 3: Create Member Notes UI Components (60 min)

#### 3.1 Notes List Partial

**File:** `src/templates/members/partials/_notes_list.html`

```html
{# Member notes list partial #}

{% if notes and notes|length > 0 %}
<div class="space-y-3" id="notes-list">
    {% for note in notes %}
    <div class="border-l-4 pl-3 py-2 {% if note.visibility == 'staff_only' %}border-warning{% elif note.visibility == 'officers' %}border-info{% else %}border-success{% endif %}">
        <div class="flex justify-between items-start">
            <div class="flex-1">
                <p class="text-sm">{{ note.note_text }}</p>
                <div class="flex items-center gap-2 mt-2 text-xs text-gray-500">
                    <span>{{ note.created_by_name or 'Unknown' }}</span>
                    <span>•</span>
                    <span>{{ note.created_at.strftime('%b %d, %Y %I:%M %p') if note.created_at else '' }}</span>
                    <span>•</span>
                    <span class="badge badge-xs {% if note.visibility == 'staff_only' %}badge-warning{% elif note.visibility == 'officers' %}badge-info{% else %}badge-success{% endif %}">
                        {{ note.visibility | replace('_', ' ') | title }}
                    </span>
                    {% if note.category %}
                    <span class="badge badge-xs badge-ghost">{{ note.category }}</span>
                    {% endif %}
                </div>
            </div>
            
            {% if current_user.id == note.created_by_id or current_user.role == 'admin' %}
            <div class="dropdown dropdown-end">
                <label tabindex="0" class="btn btn-ghost btn-xs">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                    </svg>
                </label>
                <ul tabindex="0" class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-32">
                    <li>
                        <button hx-delete="/api/v1/member-notes/{{ note.id }}"
                                hx-target="#notes-list"
                                hx-swap="outerHTML"
                                hx-confirm="Are you sure you want to delete this note?"
                                class="text-error">
                            Delete
                        </button>
                    </li>
                </ul>
            </div>
            {% endif %}
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="text-center text-gray-500 py-4">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
    </svg>
    <p class="text-sm">No notes yet</p>
    <p class="text-xs mt-1">Add a note to track interactions with this member</p>
</div>
{% endif %}
```

#### 3.2 Add Note Modal

**File:** `src/templates/members/partials/_add_note_modal.html`

```html
{# Add Note Modal #}
<dialog id="add-note-modal" class="modal">
    <div class="modal-box">
        <form method="dialog">
            <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
        </form>
        
        <h3 class="font-bold text-lg mb-4">Add Note</h3>
        
        <form hx-post="/members/{{ member.id }}/notes"
              hx-target="#notes-list"
              hx-swap="outerHTML"
              hx-on::after-request="document.getElementById('add-note-modal').close(); this.reset();">
            
            <!-- Note Text -->
            <div class="form-control mb-4">
                <label class="label">
                    <span class="label-text">Note</span>
                </label>
                <textarea 
                    name="note_text" 
                    class="textarea textarea-bordered h-24" 
                    placeholder="Enter your note..."
                    required
                    minlength="1"
                    maxlength="10000"></textarea>
            </div>
            
            <!-- Visibility -->
            <div class="form-control mb-4">
                <label class="label">
                    <span class="label-text">Visibility</span>
                </label>
                <select name="visibility" class="select select-bordered">
                    <option value="staff_only">Staff Only - Only you and admins can see</option>
                    <option value="officers">Officers - Officers and above can see</option>
                    <option value="all_authorized">All Authorized - Anyone with member access</option>
                </select>
                <label class="label">
                    <span class="label-text-alt text-gray-500">Controls who can view this note</span>
                </label>
            </div>
            
            <!-- Category (optional) -->
            <div class="form-control mb-4">
                <label class="label">
                    <span class="label-text">Category (optional)</span>
                </label>
                <select name="category" class="select select-bordered">
                    <option value="">No Category</option>
                    <option value="contact">Contact/Communication</option>
                    <option value="dues">Dues Related</option>
                    <option value="grievance">Grievance Related</option>
                    <option value="referral">Referral/Dispatch</option>
                    <option value="training">Training Related</option>
                    <option value="general">General</option>
                </select>
            </div>
            
            <!-- Submit -->
            <div class="modal-action">
                <button type="button" class="btn btn-ghost" onclick="document.getElementById('add-note-modal').close()">
                    Cancel
                </button>
                <button type="submit" class="btn btn-primary">
                    Save Note
                </button>
            </div>
        </form>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
```

#### 3.3 Add Notes Frontend Route

**File:** `src/routers/member_frontend.py`

```python
from src.schemas.member_note import MemberNoteCreate
from src.services.member_note_service import member_note_service


@router.post("/{member_id}/notes", response_class=HTMLResponse)
async def add_member_note(
    request: Request,
    member_id: int,
    note_text: str = Form(...),
    visibility: str = Form("staff_only"),
    category: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    """Add a note to a member (HTMX endpoint)."""
    # Create the note
    note_data = MemberNoteCreate(
        member_id=member_id,
        note_text=note_text,
        visibility=visibility,
        category=category if category else None,
    )
    
    member_note_service.create(db, note_data, current_user)
    
    # Return updated notes list
    notes = member_note_service.get_by_member(db, member_id, current_user)
    
    return templates.TemplateResponse(
        "members/partials/_notes_list.html",
        {
            "request": request,
            "current_user": current_user,
            "notes": [_format_note(n) for n in notes],
        }
    )


def _format_note(note):
    """Format note for template."""
    return {
        "id": note.id,
        "note_text": note.note_text,
        "visibility": note.visibility,
        "category": note.category,
        "created_by_id": note.created_by_id,
        "created_by_name": note.created_by.email if note.created_by else None,
        "created_at": note.created_at,
    }
```

---

### Task 4: Add Inline History to Other Entity Pages (30 min)

Apply the same pattern to other entity detail pages.

#### 4.1 Student Detail Page

**File:** `src/templates/training/students/detail.html`

Add in the sidebar or bottom section:

```html
<!-- Audit History Section -->
<div class="card bg-base-100 shadow mt-6">
    <div class="card-body">
        <h2 class="card-title text-lg">Recent Activity</h2>
        <div hx-get="/admin/audit-logs/entity/students/{{ student.id }}"
             hx-trigger="load"
             hx-swap="innerHTML">
            <div class="flex justify-center py-4">
                <span class="loading loading-spinner"></span>
            </div>
        </div>
    </div>
</div>
```

#### 4.2 Grievance Detail Page

**File:** `src/templates/operations/grievances/detail.html`

```html
<!-- Audit History Section -->
<div class="card bg-base-100 shadow mt-6">
    <div class="card-body">
        <h2 class="card-title text-lg">Case Activity Log</h2>
        <div hx-get="/admin/audit-logs/entity/grievances/{{ grievance.id }}"
             hx-trigger="load"
             hx-swap="innerHTML">
            <div class="flex justify-center py-4">
                <span class="loading loading-spinner"></span>
            </div>
        </div>
    </div>
</div>
```

#### 4.3 Benevolence Application Detail Page

**File:** `src/templates/operations/benevolence/detail.html`

```html
<!-- Audit History Section -->
<div class="card bg-base-100 shadow mt-6">
    <div class="card-body">
        <h2 class="card-title text-lg">Application Activity</h2>
        <div hx-get="/admin/audit-logs/entity/benevolence_applications/{{ application.id }}"
             hx-trigger="load"
             hx-swap="innerHTML">
            <div class="flex justify-center py-4">
                <span class="loading loading-spinner"></span>
            </div>
        </div>
    </div>
</div>
```

---

### Task 5: Update Member Notes API for HTMX (20 min)

**File:** `src/routers/member_notes.py`

Add HTMX-friendly delete endpoint:

```python
@router.delete("/{note_id}", response_class=HTMLResponse)
async def delete_note_htmx(
    request: Request,
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    """Delete a member note (HTMX endpoint)."""
    note = member_note_service.get_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Check permission (creator or admin)
    if note.created_by_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this note")
    
    member_id = note.member_id
    member_note_service.soft_delete(db, note_id, current_user)
    
    # Return updated notes list
    notes = member_note_service.get_by_member(db, member_id, current_user)
    
    return templates.TemplateResponse(
        "members/partials/_notes_list.html",
        {
            "request": request,
            "current_user": current_user,
            "notes": [_format_note(n) for n in notes],
        }
    )
```

---

### Task 6: Write Tests (30 min)

**File:** `src/tests/test_inline_history.py`

```python
"""Tests for inline audit history and member notes UI."""
import pytest


class TestInlineAuditHistory:
    """Tests for inline audit history on entity pages."""

    def test_member_detail_shows_history_section(self, client, auth_cookies, test_member):
        """Member detail page should have audit history section."""
        response = client.get(f"/members/{test_member.id}", cookies=auth_cookies)
        assert response.status_code == 200
        assert b"Recent Activity" in response.content or b"audit-logs/entity/members" in response.content

    def test_entity_history_endpoint(self, client, auth_cookies, test_member):
        """Entity history HTMX endpoint should return history partial."""
        response = client.get(
            f"/admin/audit-logs/entity/members/{test_member.id}",
            cookies=auth_cookies
        )
        assert response.status_code == 200

    def test_student_detail_shows_history(self, client, auth_cookies, test_student):
        """Student detail page should have audit history section."""
        response = client.get(f"/training/students/{test_student.id}", cookies=auth_cookies)
        assert response.status_code == 200


class TestMemberNotesUI:
    """Tests for member notes UI components."""

    def test_member_detail_shows_notes_section(self, client, auth_cookies, test_member):
        """Member detail page should have notes section."""
        response = client.get(f"/members/{test_member.id}", cookies=auth_cookies)
        assert response.status_code == 200
        assert b"Notes" in response.content
        assert b"Add Note" in response.content

    def test_add_note_via_htmx(self, client, auth_cookies, test_member):
        """Should be able to add note via HTMX endpoint."""
        response = client.post(
            f"/members/{test_member.id}/notes",
            data={
                "note_text": "Test note from UI",
                "visibility": "staff_only",
                "category": "general",
            },
            cookies=auth_cookies,
        )
        assert response.status_code == 200
        assert b"Test note from UI" in response.content

    def test_add_note_requires_text(self, client, auth_cookies, test_member):
        """Adding note without text should fail."""
        response = client.post(
            f"/members/{test_member.id}/notes",
            data={
                "note_text": "",
                "visibility": "staff_only",
            },
            cookies=auth_cookies,
        )
        assert response.status_code in [400, 422]

    def test_note_visibility_badges(self, client, auth_cookies, test_member, db_session):
        """Notes should display correct visibility badges."""
        # Create notes with different visibility
        from src.services.member_note_service import member_note_service
        from src.schemas.member_note import MemberNoteCreate
        
        for vis in ["staff_only", "officers", "all_authorized"]:
            member_note_service.create(
                db_session,
                MemberNoteCreate(
                    member_id=test_member.id,
                    note_text=f"Note with {vis} visibility",
                    visibility=vis,
                ),
                current_user
            )
        
        response = client.get(f"/members/{test_member.id}", cookies=auth_cookies)
        assert response.status_code == 200
        # Check visibility badges are rendered
        assert b"Staff Only" in response.content or b"staff_only" in response.content

    def test_delete_note_htmx(self, client, auth_cookies, test_member, test_note):
        """Should be able to delete note via HTMX."""
        response = client.delete(
            f"/api/v1/member-notes/{test_note.id}",
            cookies=auth_cookies,
        )
        # Returns updated list (200) or 204
        assert response.status_code in [200, 204]

    def test_delete_note_requires_permission(self, client, other_user_cookies, test_note):
        """Should not be able to delete another user's note."""
        response = client.delete(
            f"/api/v1/member-notes/{test_note.id}",
            cookies=other_user_cookies,
        )
        assert response.status_code == 403


class TestNoteCategoryDisplay:
    """Tests for note category display."""

    def test_category_badge_displayed(self, client, auth_cookies, test_member):
        """Notes with categories should show category badge."""
        # Add note with category
        response = client.post(
            f"/members/{test_member.id}/notes",
            data={
                "note_text": "Dues inquiry",
                "visibility": "staff_only",
                "category": "dues",
            },
            cookies=auth_cookies,
        )
        assert response.status_code == 200
        assert b"dues" in response.content.lower()
```

---

## Acceptance Criteria

- [ ] Reusable `_audit_history.html` partial created
- [ ] Member detail page shows "Recent Activity" section
- [ ] Member detail page shows "Notes" section with add button
- [ ] Add note modal works with visibility selector
- [ ] Note category selector functional
- [ ] Notes display with visibility badges
- [ ] Note delete works (creator or admin only)
- [ ] Student detail page shows audit history
- [ ] Grievance detail page shows audit history
- [ ] Benevolence detail page shows audit history
- [ ] HTMX endpoints return proper partials
- [ ] All tests pass (~15 new tests)

---

## Files Created

```
src/templates/components/_audit_history.html
src/templates/members/partials/_notes_list.html
src/templates/members/partials/_add_note_modal.html
src/tests/test_inline_history.py
```

## Files Modified

```
src/routers/member_frontend.py                  # Added notes routes, audit history
src/routers/member_notes.py                     # Added HTMX delete endpoint
src/templates/members/detail.html               # Added notes + history sections
src/templates/training/students/detail.html     # Added history section
src/templates/operations/grievances/detail.html # Added history section
src/templates/operations/benevolence/detail.html # Added history section
```

---

## Week 11 Completion Summary

After this session, Week 11 is complete with:

| Component | Status |
|-----------|--------|
| Audit immutability trigger | ✅ Session A |
| member_notes table | ✅ Session A |
| MemberNoteService | ✅ Session A |
| Audit permissions system | ✅ Session B |
| Sensitive field redaction | ✅ Session B |
| Audit log list page | ✅ Session B |
| Audit export (CSV) | ✅ Session B |
| Inline audit history partial | ✅ Session C |
| Member notes UI | ✅ Session C |
| History on entity pages | ✅ Session C |

**New Tests Added:** ~45 (across all 3 sessions)
**Target Version:** v0.8.2

---

## Next Phase Preview

**Week 12: Settings & Profile** will add:
- User profile page (view own info)
- Password change form
- System settings page (admin only)
- Email notification preferences

---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** 

### Before Ending This Session:

Scan all documentation in `/app/*`. Update *ANY* & *ALL* relevant documentation as necessary with current progress for the historical record. Do not forget to update ADRs, Roadmap, Checklist, again only if necessary.

**Documentation Checklist:**

| Document | Updated? | Notes |
|----------|----------|-------|
| CLAUDE.md | [ ] | Update to v0.8.2, mark Week 11 COMPLETE |
| CHANGELOG.md | [ ] | Add Week 11 Session C entry |
| CONTINUITY.md | [ ] | Update current status |
| IP2A_MILESTONE_CHECKLIST.md | [ ] | Mark Week 11 complete, add Week 12 |
| IP2A_BACKEND_ROADMAP.md | [ ] | Update Week 11 status |
| ADR-012 (Audit Logging) | [ ] | Mark full implementation complete |
| Session log created | [ ] | `docs/reports/session-logs/` |

This ensures historical record-keeping and project continuity ("bus factor" protection).

---

*End of instruction document*
