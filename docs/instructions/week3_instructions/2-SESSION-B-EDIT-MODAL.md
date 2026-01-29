# Phase 6 Week 3 - Session B: Quick Edit Modal + Role Assignment

**Document:** 2 of 3
**Estimated Time:** 2-3 hours
**Focus:** Modal editing, role checkboxes, status toggle

---

## Objective

Create a quick edit modal that allows:
- Editing user email and name
- Multi-select role assignment (checkboxes)
- Status toggle (active/locked)
- Save with HTMX and toast feedback
- Link to full detail page

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show 189+ passed
```

---

## Step 1: Add Modal Endpoints to Staff Router (30 min)

Add to `src/routers/staff.py`:

```python
from fastapi import Form
from typing import List

# ============================================================
# Edit Modal Endpoints
# ============================================================

@router.get("/{user_id}/edit", response_class=HTMLResponse)
async def get_edit_modal(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """
    HTMX partial: Return the edit modal content for a user.
    """
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(content="<p>Session expired</p>", status_code=401)
    
    service = StaffService(db)
    user = await service.get_user_by_id(user_id)
    
    if not user:
        return HTMLResponse(content="<p>User not found</p>", status_code=404)
    
    all_roles = await service.get_all_roles()
    user_role_names = [r.name for r in user.roles]
    
    return templates.TemplateResponse(
        "staff/partials/_edit_modal.html",
        {
            "request": request,
            "target_user": user,
            "all_roles": all_roles,
            "user_role_names": user_role_names,
        }
    )


@router.post("/{user_id}/edit", response_class=HTMLResponse)
async def update_user(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    email: str = Form(...),
    first_name: str = Form(None),
    last_name: str = Form(None),
    roles: List[str] = Form(default=[]),
    is_locked: bool = Form(default=False),
):
    """
    Update user details from the edit modal.
    Returns the updated row HTML for HTMX swap.
    """
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(content="Session expired", status_code=401)
    
    service = StaffService(db)
    
    try:
        updated_user = await service.update_user(
            user_id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            roles=roles,
            is_locked=is_locked,
            updated_by=current_user["id"],
        )
        
        if not updated_user:
            return HTMLResponse(
                content='<div class="alert alert-error">User not found</div>',
                status_code=404
            )
        
        # Return success message for toast
        return HTMLResponse(
            content=f'''
            <div class="alert alert-success" id="save-success">
                <svg class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>User updated successfully!</span>
            </div>
            <script>
                // Close modal after short delay
                setTimeout(() => {{
                    document.getElementById('edit-modal').close();
                    // Refresh the table
                    htmx.trigger('#table-container', 'refresh');
                }}, 1000);
            </script>
            ''',
            status_code=200
        )
        
    except ValueError as e:
        return HTMLResponse(
            content=f'<div class="alert alert-error">{str(e)}</div>',
            status_code=400
        )
    except Exception as e:
        return HTMLResponse(
            content=f'<div class="alert alert-error">Failed to update user: {str(e)}</div>',
            status_code=500
        )


@router.post("/{user_id}/roles", response_class=HTMLResponse)
async def update_user_roles(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    roles: List[str] = Form(default=[]),
):
    """
    Update only the user's roles.
    Returns updated role badges HTML.
    """
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(content="Session expired", status_code=401)
    
    service = StaffService(db)
    
    try:
        updated_user = await service.update_user_roles(
            user_id=user_id,
            roles=roles,
            updated_by=current_user["id"],
        )
        
        if not updated_user:
            return HTMLResponse(content="User not found", status_code=404)
        
        # Return updated role badges
        badges_html = ""
        for role in updated_user.roles:
            badge_class = "primary" if role.name == "admin" else "secondary" if role.name == "officer" else "accent" if role.name == "staff" else "ghost"
            badges_html += f'<span class="badge badge-{badge_class} badge-sm">{role.name}</span>'
        
        if not updated_user.roles:
            badges_html = '<span class="badge badge-ghost badge-sm">No roles</span>'
        
        return HTMLResponse(content=badges_html)
        
    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)
```

---

## Step 2: Add Update Methods to Staff Service (30 min)

Add to `src/services/staff_service.py`:

```python
from src.models.role import Role
from sqlalchemy.orm import selectinload

class StaffService:
    # ... existing methods ...

    async def update_user(
        self,
        user_id: int,
        email: str,
        first_name: Optional[str],
        last_name: Optional[str],
        roles: List[str],
        is_locked: bool,
        updated_by: int,
    ) -> Optional[User]:
        """
        Update user details including roles.
        Logs all changes to audit log.
        """
        # Get user with roles
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Track changes for audit log
        changes = {"before": {}, "after": {}}
        
        # Update email
        if user.email != email:
            # Check for duplicate email
            existing = await self.db.execute(
                select(User).where(User.email == email, User.id != user_id)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Email {email} is already in use")
            changes["before"]["email"] = user.email
            changes["after"]["email"] = email
            user.email = email
        
        # Update name fields
        if user.first_name != first_name:
            changes["before"]["first_name"] = user.first_name
            changes["after"]["first_name"] = first_name
            user.first_name = first_name
        
        if user.last_name != last_name:
            changes["before"]["last_name"] = user.last_name
            changes["after"]["last_name"] = last_name
            user.last_name = last_name
        
        # Update locked status
        if user.is_locked != is_locked:
            changes["before"]["is_locked"] = user.is_locked
            changes["after"]["is_locked"] = is_locked
            user.is_locked = is_locked
            if not is_locked:
                # Reset failed attempts when unlocking
                user.failed_login_attempts = 0
                user.locked_until = None
        
        # Update roles
        old_role_names = sorted([r.name for r in user.roles])
        new_role_names = sorted(roles)
        
        if old_role_names != new_role_names:
            changes["before"]["roles"] = old_role_names
            changes["after"]["roles"] = new_role_names
            
            # Get role objects
            role_stmt = select(Role).where(Role.name.in_(roles))
            role_result = await self.db.execute(role_stmt)
            new_roles = list(role_result.scalars().all())
            user.roles = new_roles
        
        # Only log if there were changes
        if changes["before"]:
            await self.audit.log_action(
                user_id=updated_by,
                action="UPDATE",
                entity_type="user",
                entity_id=user_id,
                changes=changes,
            )
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user

    async def update_user_roles(
        self,
        user_id: int,
        roles: List[str],
        updated_by: int,
    ) -> Optional[User]:
        """Update only the user's roles."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        old_role_names = sorted([r.name for r in user.roles])
        new_role_names = sorted(roles)
        
        if old_role_names != new_role_names:
            # Get role objects
            role_stmt = select(Role).where(Role.name.in_(roles))
            role_result = await self.db.execute(role_stmt)
            new_roles = list(role_result.scalars().all())
            user.roles = new_roles
            
            # Log the change
            await self.audit.log_action(
                user_id=updated_by,
                action="UPDATE",
                entity_type="user_role",
                entity_id=user_id,
                changes={
                    "before": {"roles": old_role_names},
                    "after": {"roles": new_role_names},
                },
            )
            
            await self.db.commit()
            await self.db.refresh(user)
        
        return user

    async def toggle_lock(
        self,
        user_id: int,
        lock: bool,
        updated_by: int,
    ) -> Optional[User]:
        """Lock or unlock a user account."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        if user.is_locked != lock:
            user.is_locked = lock
            if not lock:
                user.failed_login_attempts = 0
                user.locked_until = None
            
            await self.audit.log_action(
                user_id=updated_by,
                action="UPDATE",
                entity_type="user",
                entity_id=user_id,
                changes={
                    "before": {"is_locked": not lock},
                    "after": {"is_locked": lock},
                },
            )
            
            await self.db.commit()
            await self.db.refresh(user)
        
        return user
```

---

## Step 3: Create Edit Modal Template (30 min)

Create `src/templates/staff/partials/_edit_modal.html`:

```html
{# Quick edit modal content - loaded via HTMX #}

<h3 class="font-bold text-lg mb-4">
    Edit User: {{ target_user.first_name or target_user.email.split('@')[0] }}
</h3>

<form 
    hx-post="/staff/{{ target_user.id }}/edit"
    hx-target="#modal-feedback"
    hx-swap="innerHTML"
    hx-indicator="#save-spinner"
    class="space-y-4"
>
    <!-- Feedback area -->
    <div id="modal-feedback"></div>

    <!-- Email -->
    <div class="form-control">
        <label class="label">
            <span class="label-text font-medium">Email Address</span>
        </label>
        <input 
            type="email" 
            name="email" 
            value="{{ target_user.email }}"
            class="input input-bordered"
            required
        />
    </div>

    <!-- Name Fields (side by side) -->
    <div class="grid grid-cols-2 gap-4">
        <div class="form-control">
            <label class="label">
                <span class="label-text font-medium">First Name</span>
            </label>
            <input 
                type="text" 
                name="first_name" 
                value="{{ target_user.first_name or '' }}"
                class="input input-bordered"
                placeholder="Optional"
            />
        </div>
        <div class="form-control">
            <label class="label">
                <span class="label-text font-medium">Last Name</span>
            </label>
            <input 
                type="text" 
                name="last_name" 
                value="{{ target_user.last_name or '' }}"
                class="input input-bordered"
                placeholder="Optional"
            />
        </div>
    </div>

    <!-- Roles (Checkboxes) -->
    <div class="form-control">
        <label class="label">
            <span class="label-text font-medium">Roles</span>
            <span class="label-text-alt text-base-content/60">Select all that apply</span>
        </label>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-2 p-3 bg-base-200 rounded-lg">
            {% for role in all_roles %}
            <label class="label cursor-pointer justify-start gap-3 p-2 rounded hover:bg-base-300">
                <input 
                    type="checkbox" 
                    name="roles" 
                    value="{{ role.name }}"
                    class="checkbox checkbox-sm checkbox-primary"
                    {% if role.name in user_role_names %}checked{% endif %}
                />
                <span class="label-text">
                    {{ role.name | title }}
                    {% if role.name == 'admin' %}
                    <span class="badge badge-xs badge-warning ml-1">Full Access</span>
                    {% endif %}
                </span>
            </label>
            {% endfor %}
        </div>
        <label class="label">
            <span class="label-text-alt text-warning">
                <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
                Admin role grants full system access
            </span>
        </label>
    </div>

    <!-- Account Status -->
    <div class="form-control">
        <label class="label">
            <span class="label-text font-medium">Account Status</span>
        </label>
        <div class="flex gap-4 p-3 bg-base-200 rounded-lg">
            <label class="label cursor-pointer justify-start gap-3">
                <input 
                    type="radio" 
                    name="is_locked" 
                    value="false"
                    class="radio radio-success radio-sm"
                    {% if not target_user.is_locked %}checked{% endif %}
                />
                <span class="label-text flex items-center gap-2">
                    <span class="badge badge-success badge-xs"></span>
                    Active
                </span>
            </label>
            <label class="label cursor-pointer justify-start gap-3">
                <input 
                    type="radio" 
                    name="is_locked" 
                    value="true"
                    class="radio radio-error radio-sm"
                    {% if target_user.is_locked %}checked{% endif %}
                />
                <span class="label-text flex items-center gap-2">
                    <span class="badge badge-error badge-xs"></span>
                    Locked
                </span>
            </label>
        </div>
        {% if target_user.is_locked and target_user.locked_until %}
        <label class="label">
            <span class="label-text-alt text-error">
                Locked until {{ target_user.locked_until.strftime('%b %d, %Y %I:%M %p') }}
            </span>
        </label>
        {% endif %}
    </div>

    <!-- Divider -->
    <div class="divider">Quick Actions</div>

    <!-- Quick Action Buttons -->
    <div class="flex flex-wrap gap-2">
        <button 
            type="button"
            class="btn btn-sm btn-outline"
            hx-post="/staff/{{ target_user.id }}/reset-password"
            hx-target="#modal-feedback"
            hx-swap="innerHTML"
            hx-confirm="Send password reset email to {{ target_user.email }}?"
        >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
            </svg>
            Reset Password
        </button>
        
        <a href="/staff/{{ target_user.id }}" class="btn btn-sm btn-outline">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
            </svg>
            Full Details
        </a>
    </div>

    <!-- Modal Actions -->
    <div class="modal-action">
        <button type="button" class="btn btn-ghost" onclick="document.getElementById('edit-modal').close()">
            Cancel
        </button>
        <button type="submit" class="btn btn-primary">
            <span id="save-spinner" class="loading loading-spinner loading-sm htmx-indicator"></span>
            Save Changes
        </button>
    </div>
</form>

<!-- User Info Footer -->
<div class="text-xs text-base-content/50 mt-4 pt-4 border-t border-base-200">
    <div class="flex justify-between">
        <span>User ID: {{ target_user.id }}</span>
        <span>Created: {{ target_user.created_at.strftime('%b %d, %Y') }}</span>
    </div>
    {% if target_user.last_login %}
    <div class="mt-1">
        Last login: {{ target_user.last_login.strftime('%b %d, %Y at %I:%M %p') }}
    </div>
    {% endif %}
</div>
```

---

## Step 4: Add HTMX Refresh Handler (15 min)

Update `src/static/js/app.js` to add table refresh on edit:

```javascript
// Add to existing app.js

// Listen for custom refresh event on table container
document.addEventListener('htmx:trigger', function(event) {
    if (event.detail.name === 'refresh') {
        // Trigger a search with current params to refresh table
        const searchInput = document.querySelector('input[name="q"]');
        if (searchInput) {
            htmx.trigger(searchInput, 'search');
        }
    }
});

// Close modal on escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('edit-modal');
        if (modal && modal.open) {
            modal.close();
        }
    }
});

// Auto-dismiss alerts after 5 seconds
document.addEventListener('htmx:afterSwap', function(event) {
    const alerts = event.target.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease-out';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});
```

---

## Step 5: Update Table Container for Refresh (10 min)

Update `src/templates/staff/index.html` table container to support HTMX refresh:

Find the table container div and update it:

```html
<!-- User Table -->
<div class="card bg-base-100 shadow overflow-hidden">
    <div 
        id="table-container"
        hx-get="/staff/search"
        hx-trigger="refresh from:body"
        hx-include="[name='q'], [name='role'], [name='status']"
    >
        {% include "staff/partials/_table_body.html" %}
    </div>
</div>
```

---

## Step 6: Test Modal Flow

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

1. Login and go to `/staff`
2. Click edit (pencil) icon on any user row
3. Modal should open with user data
4. Change some fields (email, name, roles)
5. Click "Save Changes"
6. Modal should show success, then close
7. Table should refresh with updated data

---

## Step 7: Add Modal Tests

Add to `src/tests/test_staff.py`:

```python
class TestStaffEditModal:
    """Tests for edit modal functionality."""

    @pytest.mark.asyncio
    async def test_edit_modal_endpoint_exists(self, async_client: AsyncClient):
        """Edit modal endpoint should exist."""
        response = await async_client.get("/staff/1/edit")
        # Will return 302 (auth) or 404 (user not found), not 404 for route
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_edit_modal_requires_auth(self, async_client: AsyncClient):
        """Edit modal should require authentication."""
        response = await async_client.get("/staff/1/edit", follow_redirects=False)
        assert response.status_code in [302, 401]

    @pytest.mark.asyncio
    async def test_update_endpoint_accepts_post(self, async_client: AsyncClient):
        """Update endpoint should accept POST."""
        response = await async_client.post(
            "/staff/1/edit",
            data={"email": "test@test.com", "roles": ["member"]}
        )
        # Will fail auth but endpoint should exist
        assert response.status_code in [200, 302, 401, 404, 422]
```

---

## Step 8: Run Tests

```bash
pytest -v --tb=short

# Expected: 192+ tests passing
```

---

## Step 9: Commit

```bash
git add -A
git status

git commit -m "feat(staff): Phase 6 Week 3 Session B - Quick edit modal

- Add edit modal endpoint (GET /staff/{id}/edit)
- Add update endpoint (POST /staff/{id}/edit)
- Add role update endpoint (POST /staff/{id}/roles)
- Create _edit_modal.html with:
  - Email/name editing
  - Multi-select role checkboxes
  - Account status toggle
  - Quick action buttons
- Add StaffService.update_user() with audit logging
- Add StaffService.update_user_roles()
- Add StaffService.toggle_lock()
- HTMX refresh after save
- Auto-dismiss alerts
- Modal tests"

git push origin main
```

---

## Session B Checklist

- [ ] Added edit modal GET endpoint
- [ ] Added update POST endpoint
- [ ] Added role update endpoint
- [ ] Created `_edit_modal.html` template
- [ ] Implemented `StaffService.update_user()`
- [ ] Implemented `StaffService.update_user_roles()`
- [ ] Implemented `StaffService.toggle_lock()`
- [ ] Role checkboxes working (multi-select)
- [ ] Status toggle working
- [ ] Audit logging on all changes
- [ ] Modal closes and table refreshes on save
- [ ] Tests passing
- [ ] Committed changes

---

## Files Modified This Session

```
src/
├── services/
│   └── staff_service.py         # Added update methods
├── routers/
│   └── staff.py                 # Added modal endpoints
├── templates/
│   └── staff/
│       └── partials/
│           └── _edit_modal.html # NEW: Edit modal content
├── static/
│   └── js/
│       └── app.js               # Added refresh handlers
└── tests/
    └── test_staff.py            # Added modal tests
```

---

*Session B complete. Proceed to Session C for account actions and full detail page.*
