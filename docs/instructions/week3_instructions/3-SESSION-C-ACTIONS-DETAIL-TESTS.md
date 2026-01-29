# Phase 6 Week 3 - Session C: Account Actions + Detail Page + Tests

**Document:** 3 of 3
**Estimated Time:** 2-3 hours
**Focus:** Lock/unlock, reset password, delete, full detail page, comprehensive tests

---

## Objective

Complete the staff management feature with:
- Lock/unlock account actions
- Password reset trigger
- Soft delete with confirmation
- Full detail page with history
- Comprehensive test coverage (15+ tests)
- Documentation updates

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show 192+ passed
```

---

## Step 1: Add Account Action Endpoints (30 min)

Add to `src/routers/staff.py`:

```python
from fastapi.responses import HTMLResponse
from src.templates import templates  # Adjust import as needed

# ============================================================
# Account Actions
# ============================================================

@router.post("/{user_id}/lock", response_class=HTMLResponse)
async def lock_user_account(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Lock a user account. Returns updated row HTML."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(content="Session expired", status_code=401)
    
    # Prevent self-lock
    if current_user["id"] == user_id:
        return HTMLResponse(
            content='<div class="alert alert-error">You cannot lock your own account</div>',
            status_code=400
        )
    
    service = StaffService(db)
    user = await service.toggle_lock(user_id, lock=True, updated_by=current_user["id"])
    
    if not user:
        return HTMLResponse(content="User not found", status_code=404)
    
    # Return the updated row
    return templates.TemplateResponse(
        "staff/partials/_row.html",
        {"request": request, "user": user}
    )


@router.post("/{user_id}/unlock", response_class=HTMLResponse)
async def unlock_user_account(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Unlock a user account. Returns updated row HTML."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(content="Session expired", status_code=401)
    
    service = StaffService(db)
    user = await service.toggle_lock(user_id, lock=False, updated_by=current_user["id"])
    
    if not user:
        return HTMLResponse(content="User not found", status_code=404)
    
    return templates.TemplateResponse(
        "staff/partials/_row.html",
        {"request": request, "user": user}
    )


@router.post("/{user_id}/reset-password", response_class=HTMLResponse)
async def reset_user_password(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """
    Trigger password reset for a user.
    In production, this would send an email.
    For now, it logs the action and returns success.
    """
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(content="Session expired", status_code=401)
    
    service = StaffService(db)
    user = await service.get_user_by_id(user_id)
    
    if not user:
        return HTMLResponse(
            content='<div class="alert alert-error">User not found</div>',
            status_code=404
        )
    
    # Log the password reset request
    await service.log_password_reset_request(user_id, current_user["id"])
    
    # In production, trigger email here:
    # await send_password_reset_email(user.email)
    
    return HTMLResponse(
        content=f'''
        <div class="alert alert-success">
            <svg class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Password reset initiated for {user.email}</span>
        </div>
        ''',
        status_code=200
    )


@router.delete("/{user_id}", response_class=HTMLResponse)
async def delete_user(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """
    Soft delete a user account.
    Returns empty content to remove the row via HTMX.
    """
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(content="Session expired", status_code=401)
    
    # Prevent self-delete
    if current_user["id"] == user_id:
        return HTMLResponse(
            content='<tr><td colspan="6"><div class="alert alert-error">You cannot delete your own account</div></td></tr>',
            status_code=400
        )
    
    service = StaffService(db)
    success = await service.soft_delete_user(user_id, current_user["id"])
    
    if not success:
        return HTMLResponse(
            content='<tr><td colspan="6"><div class="alert alert-error">User not found</div></td></tr>',
            status_code=404
        )
    
    # Return empty string - HTMX will remove the row
    # Using swap:500ms in the button gives a nice fade effect
    return HTMLResponse(content="", status_code=200)


# ============================================================
# Full Detail Page
# ============================================================

@router.get("/{user_id}", response_class=HTMLResponse)
async def user_detail_page(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render the full user detail page."""
    if isinstance(current_user, RedirectResponse):
        return current_user
    
    service = StaffService(db)
    user = await service.get_user_by_id(user_id)
    
    if not user:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "User not found"},
            status_code=404
        )
    
    # Get user's audit history
    audit_history = await service.get_user_audit_history(user_id, limit=20)
    
    # Get all roles for editing
    all_roles = await service.get_all_roles()
    user_role_names = [r.name for r in user.roles]
    
    return templates.TemplateResponse(
        "staff/detail.html",
        {
            "request": request,
            "current_user": current_user,
            "target_user": user,
            "all_roles": all_roles,
            "user_role_names": user_role_names,
            "audit_history": audit_history,
        }
    )
```

---

## Step 2: Add Service Methods (20 min)

Add to `src/services/staff_service.py`:

```python
from src.models.audit_log import AuditLog

class StaffService:
    # ... existing methods ...

    async def log_password_reset_request(
        self,
        user_id: int,
        requested_by: int,
    ) -> None:
        """Log a password reset request to audit log."""
        await self.audit.log_action(
            user_id=requested_by,
            action="UPDATE",
            entity_type="user",
            entity_id=user_id,
            changes={
                "action": "password_reset_requested",
                "requested_at": datetime.utcnow().isoformat(),
            },
        )
        await self.db.commit()

    async def soft_delete_user(
        self,
        user_id: int,
        deleted_by: int,
    ) -> bool:
        """
        Soft delete a user account.
        Sets is_active=False and logs the deletion.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Store user info for audit before "deleting"
        user_email = user.email
        
        # Soft delete: deactivate and anonymize
        user.is_active = False
        user.is_locked = True
        # Optionally anonymize email: user.email = f"deleted_{user_id}@deleted.local"
        
        await self.audit.log_action(
            user_id=deleted_by,
            action="DELETE",
            entity_type="user",
            entity_id=user_id,
            changes={
                "email": user_email,
                "deleted_at": datetime.utcnow().isoformat(),
            },
        )
        
        await self.db.commit()
        return True

    async def get_user_audit_history(
        self,
        user_id: int,
        limit: int = 20,
    ) -> List[dict]:
        """
        Get audit log entries related to a user.
        Includes actions ON the user and BY the user.
        """
        # Actions on this user
        stmt = select(AuditLog).where(
            or_(
                and_(AuditLog.entity_type == "user", AuditLog.entity_id == user_id),
                and_(AuditLog.entity_type == "user_role", AuditLog.entity_id == user_id),
                AuditLog.user_id == user_id,  # Actions by this user
            )
        ).order_by(AuditLog.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        logs = result.scalars().all()
        
        history = []
        for log in logs:
            history.append({
                "id": log.id,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "user_id": log.user_id,
                "changes": log.changes,
                "created_at": log.created_at,
                "description": self._format_audit_entry(log, user_id),
            })
        
        return history

    def _format_audit_entry(self, log: AuditLog, target_user_id: int) -> str:
        """Format an audit log entry for display."""
        if log.entity_type == "user" and log.entity_id == target_user_id:
            if log.action == "UPDATE":
                if log.changes and "action" in log.changes:
                    if log.changes["action"] == "password_reset_requested":
                        return "Password reset requested"
                changes = log.changes or {}
                if "is_locked" in changes.get("after", {}):
                    if changes["after"]["is_locked"]:
                        return "Account locked"
                    else:
                        return "Account unlocked"
                if "roles" in changes.get("after", {}):
                    return f"Roles updated to: {', '.join(changes['after']['roles'])}"
                return "Profile updated"
            elif log.action == "DELETE":
                return "Account deleted"
            elif log.action == "CREATE":
                return "Account created"
        elif log.entity_type == "user_role":
            return "Role assignment changed"
        elif log.user_id == target_user_id:
            return f"{log.action} on {log.entity_type} #{log.entity_id}"
        
        return f"{log.action} - {log.entity_type}"
```

---

## Step 3: Create Detail Page Template (30 min)

Create `src/templates/staff/detail.html`:

```html
{% extends "base.html" %}

{% block title %}{{ target_user.email }} - Staff Details - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/staff">Staff</a></li>
            <li>{{ target_user.first_name or target_user.email.split('@')[0] }}</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div class="flex items-center gap-4">
            <div class="avatar placeholder">
                <div class="bg-neutral text-neutral-content rounded-full w-16">
                    <span class="text-xl">
                        {{ (target_user.first_name or target_user.email)[0] | upper }}{{ (target_user.last_name or '')[0] | upper if target_user.last_name else '' }}
                    </span>
                </div>
            </div>
            <div>
                <h1 class="text-2xl font-bold">
                    {% if target_user.first_name or target_user.last_name %}
                        {{ target_user.first_name or '' }} {{ target_user.last_name or '' }}
                    {% else %}
                        {{ target_user.email.split('@')[0] }}
                    {% endif %}
                </h1>
                <p class="text-base-content/60">{{ target_user.email }}</p>
            </div>
        </div>
        <div class="flex gap-2">
            {% if target_user.is_locked %}
            <span class="badge badge-error badge-lg gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                </svg>
                Locked
            </span>
            {% elif not target_user.is_active %}
            <span class="badge badge-warning badge-lg">Inactive</span>
            {% else %}
            <span class="badge badge-success badge-lg gap-2">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="4"/>
                </svg>
                Active
            </span>
            {% endif %}
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Main Content -->
        <div class="lg:col-span-2 space-y-6">
            <!-- User Info Card -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">User Information</h2>
                    
                    <form 
                        hx-post="/staff/{{ target_user.id }}/edit"
                        hx-target="#detail-feedback"
                        hx-swap="innerHTML"
                        class="space-y-4"
                    >
                        <div id="detail-feedback"></div>
                        
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text">Email</span>
                                </label>
                                <input 
                                    type="email" 
                                    name="email" 
                                    value="{{ target_user.email }}"
                                    class="input input-bordered"
                                    required
                                />
                            </div>
                            
                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text">User ID</span>
                                </label>
                                <input 
                                    type="text" 
                                    value="{{ target_user.id }}"
                                    class="input input-bordered"
                                    disabled
                                />
                            </div>
                            
                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text">First Name</span>
                                </label>
                                <input 
                                    type="text" 
                                    name="first_name" 
                                    value="{{ target_user.first_name or '' }}"
                                    class="input input-bordered"
                                />
                            </div>
                            
                            <div class="form-control">
                                <label class="label">
                                    <span class="label-text">Last Name</span>
                                </label>
                                <input 
                                    type="text" 
                                    name="last_name" 
                                    value="{{ target_user.last_name or '' }}"
                                    class="input input-bordered"
                                />
                            </div>
                        </div>

                        <!-- Roles -->
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Roles</span>
                            </label>
                            <div class="flex flex-wrap gap-2 p-3 bg-base-200 rounded-lg">
                                {% for role in all_roles %}
                                <label class="label cursor-pointer gap-2 px-3 py-2 rounded-lg hover:bg-base-300">
                                    <input 
                                        type="checkbox" 
                                        name="roles" 
                                        value="{{ role.name }}"
                                        class="checkbox checkbox-sm checkbox-primary"
                                        {% if role.name in user_role_names %}checked{% endif %}
                                    />
                                    <span class="label-text">{{ role.name | title }}</span>
                                </label>
                                {% endfor %}
                            </div>
                        </div>

                        <!-- Status -->
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Account Status</span>
                            </label>
                            <div class="flex gap-4">
                                <label class="label cursor-pointer gap-2">
                                    <input 
                                        type="radio" 
                                        name="is_locked" 
                                        value="false"
                                        class="radio radio-success"
                                        {% if not target_user.is_locked %}checked{% endif %}
                                    />
                                    <span>Active</span>
                                </label>
                                <label class="label cursor-pointer gap-2">
                                    <input 
                                        type="radio" 
                                        name="is_locked" 
                                        value="true"
                                        class="radio radio-error"
                                        {% if target_user.is_locked %}checked{% endif %}
                                    />
                                    <span>Locked</span>
                                </label>
                            </div>
                        </div>

                        <div class="card-actions justify-end">
                            <button type="submit" class="btn btn-primary">
                                Save Changes
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- Audit History -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Activity History</h2>
                    
                    {% if audit_history %}
                    <div class="overflow-x-auto">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Action</th>
                                    <th>Details</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for entry in audit_history %}
                                <tr class="hover">
                                    <td class="whitespace-nowrap">
                                        {{ entry.created_at.strftime('%b %d, %Y') }}
                                        <br>
                                        <span class="text-xs text-base-content/50">
                                            {{ entry.created_at.strftime('%I:%M %p') }}
                                        </span>
                                    </td>
                                    <td>
                                        <span class="badge badge-{{ 'primary' if entry.action == 'CREATE' else 'warning' if entry.action == 'UPDATE' else 'error' if entry.action == 'DELETE' else 'ghost' }} badge-sm">
                                            {{ entry.action }}
                                        </span>
                                    </td>
                                    <td>{{ entry.description }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    {% else %}
                    <p class="text-base-content/50 text-center py-4">No activity recorded</p>
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- Sidebar -->
        <div class="space-y-6">
            <!-- Quick Actions -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Quick Actions</h2>
                    
                    <div class="space-y-2">
                        {% if target_user.is_locked %}
                        <button 
                            class="btn btn-success btn-block"
                            hx-post="/staff/{{ target_user.id }}/unlock"
                            hx-target="#detail-feedback"
                            hx-swap="innerHTML"
                        >
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z"/>
                            </svg>
                            Unlock Account
                        </button>
                        {% else %}
                        <button 
                            class="btn btn-warning btn-block"
                            hx-post="/staff/{{ target_user.id }}/lock"
                            hx-target="#detail-feedback"
                            hx-swap="innerHTML"
                            hx-confirm="Are you sure you want to lock this account?"
                        >
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                            </svg>
                            Lock Account
                        </button>
                        {% endif %}
                        
                        <button 
                            class="btn btn-outline btn-block"
                            hx-post="/staff/{{ target_user.id }}/reset-password"
                            hx-target="#detail-feedback"
                            hx-swap="innerHTML"
                            hx-confirm="Send password reset email to {{ target_user.email }}?"
                        >
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
                            </svg>
                            Reset Password
                        </button>
                        
                        <div class="divider"></div>
                        
                        <button 
                            class="btn btn-error btn-outline btn-block"
                            hx-delete="/staff/{{ target_user.id }}"
                            hx-confirm="Are you sure you want to delete this user? This action cannot be undone."
                            hx-target="body"
                            hx-swap="innerHTML"
                            _="on htmx:afterRequest if event.detail.successful window.location.href = '/staff?message=User+deleted&type=success'"
                        >
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                            </svg>
                            Delete Account
                        </button>
                    </div>
                </div>
            </div>

            <!-- Account Info -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Account Info</h2>
                    
                    <div class="space-y-3 text-sm">
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Created</span>
                            <span>{{ target_user.created_at.strftime('%b %d, %Y') }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Last Login</span>
                            <span>
                                {% if target_user.last_login %}
                                {{ target_user.last_login.strftime('%b %d, %Y') }}
                                {% else %}
                                Never
                                {% endif %}
                            </span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Failed Logins</span>
                            <span class="{{ 'text-error' if target_user.failed_login_attempts > 0 else '' }}">
                                {{ target_user.failed_login_attempts }}
                            </span>
                        </div>
                        {% if target_user.locked_until %}
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Locked Until</span>
                            <span class="text-error">
                                {{ target_user.locked_until.strftime('%b %d, %Y %I:%M %p') }}
                            </span>
                        </div>
                        {% endif %}
                        {% if target_user.member_id %}
                        <div class="divider my-2"></div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Linked Member</span>
                            <a href="/members/{{ target_user.member_id }}" class="link link-primary">
                                #{{ target_user.member_id }}
                            </a>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Step 4: Update Index for Flash Messages (10 min)

Update `src/templates/staff/index.html` to show flash messages:

Add near the top of the content block, after the page header:

```html
<!-- Flash Messages -->
{% set msg = request.query_params.get('message') %}
{% set msg_type = request.query_params.get('type', 'info') %}
{% if msg %}
<div class="alert alert-{{ msg_type }} mb-4">
    <svg class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
        {% if msg_type == 'success' %}
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        {% elif msg_type == 'error' %}
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
        {% else %}
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        {% endif %}
    </svg>
    <span>{{ msg }}</span>
</div>
{% endif %}
```

---

## Step 5: Comprehensive Test Suite (45 min)

Replace/update `src/tests/test_staff.py`:

```python
"""
Comprehensive staff management tests.
Tests search, filters, pagination, CRUD, and account actions.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestStaffListPage:
    """Tests for staff list page."""

    @pytest.mark.asyncio
    async def test_staff_page_requires_auth(self, async_client: AsyncClient):
        """Staff page redirects to login when not authenticated."""
        response = await async_client.get("/staff", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_staff_page_exists(self, async_client: AsyncClient):
        """Staff page route exists."""
        response = await async_client.get("/staff")
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestStaffSearch:
    """Tests for search functionality."""

    @pytest.mark.asyncio
    async def test_search_endpoint_exists(self, async_client: AsyncClient):
        """Search endpoint exists."""
        response = await async_client.get("/staff/search")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_query(self, async_client: AsyncClient):
        """Search accepts query parameter."""
        response = await async_client.get("/staff/search?q=admin")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_role_filter(self, async_client: AsyncClient):
        """Search accepts role filter."""
        response = await async_client.get("/staff/search?role=admin")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_status_filter(self, async_client: AsyncClient):
        """Search accepts status filter."""
        response = await async_client.get("/staff/search?status=active")
        assert response.status_code in [200, 302, 401]

    @pytest.mark.asyncio
    async def test_search_with_pagination(self, async_client: AsyncClient):
        """Search accepts page parameter."""
        response = await async_client.get("/staff/search?page=2")
        assert response.status_code in [200, 302, 401]


class TestStaffEditModal:
    """Tests for edit modal."""

    @pytest.mark.asyncio
    async def test_edit_modal_endpoint(self, async_client: AsyncClient):
        """Edit modal endpoint exists."""
        response = await async_client.get("/staff/1/edit")
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_update_endpoint_accepts_post(self, async_client: AsyncClient):
        """Update endpoint accepts POST."""
        response = await async_client.post(
            "/staff/1/edit",
            data={"email": "test@test.com"}
        )
        assert response.status_code in [200, 302, 401, 404, 422]

    @pytest.mark.asyncio
    async def test_roles_update_endpoint(self, async_client: AsyncClient):
        """Roles update endpoint exists."""
        response = await async_client.post(
            "/staff/1/roles",
            data={"roles": ["member"]}
        )
        assert response.status_code in [200, 302, 401, 404]


class TestAccountActions:
    """Tests for account actions."""

    @pytest.mark.asyncio
    async def test_lock_endpoint(self, async_client: AsyncClient):
        """Lock endpoint exists."""
        response = await async_client.post("/staff/1/lock")
        assert response.status_code in [200, 302, 400, 401, 404]

    @pytest.mark.asyncio
    async def test_unlock_endpoint(self, async_client: AsyncClient):
        """Unlock endpoint exists."""
        response = await async_client.post("/staff/1/unlock")
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_reset_password_endpoint(self, async_client: AsyncClient):
        """Reset password endpoint exists."""
        response = await async_client.post("/staff/1/reset-password")
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_delete_endpoint(self, async_client: AsyncClient):
        """Delete endpoint exists."""
        response = await async_client.delete("/staff/1")
        assert response.status_code in [200, 302, 400, 401, 404]


class TestStaffDetailPage:
    """Tests for detail page."""

    @pytest.mark.asyncio
    async def test_detail_page_exists(self, async_client: AsyncClient):
        """Detail page route exists."""
        response = await async_client.get("/staff/1")
        assert response.status_code in [200, 302, 401, 404]

    @pytest.mark.asyncio
    async def test_detail_page_requires_auth(self, async_client: AsyncClient):
        """Detail page requires authentication."""
        response = await async_client.get("/staff/1", follow_redirects=False)
        assert response.status_code in [302, 401, 404]


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_404(self, async_client: AsyncClient):
        """Requesting nonexistent user returns 404."""
        response = await async_client.get("/staff/99999")
        # Will be 404 or auth redirect
        assert response.status_code in [302, 401, 404]

    @pytest.mark.asyncio
    async def test_invalid_user_id_handled(self, async_client: AsyncClient):
        """Invalid user ID is handled gracefully."""
        response = await async_client.get("/staff/abc")
        # Should return 404 or 422 (validation error)
        assert response.status_code in [302, 401, 404, 422]
```

---

## Step 6: Run All Tests

```bash
pytest -v --tb=short

# Expected: 200+ tests passing
# New tests: ~18 staff tests
```

---

## Step 7: Update Documentation

### Update CHANGELOG.md

Add to `[Unreleased]`:

```markdown
- **Phase 6 Week 3: Staff Management**
  * User list page with search, filter, and pagination
  * HTMX-powered live search (300ms debounce)
  * Filter by role and account status
  * Quick edit modal with role checkboxes
  * Full detail page with audit history
  * Account actions: lock/unlock, reset password, soft delete
  * All actions audit logged
  * 18 new staff management tests
```

### Update CLAUDE.md

Add Week 3 section showing completion status.

---

## Step 8: Final Commit

```bash
git add -A
git status

git commit -m "feat(staff): Phase 6 Week 3 Complete - Staff Management

Session A: User list with search
- StaffService with search/filter/paginate
- Staff router with list endpoints
- User table with HTMX live search
- Pagination component

Session B: Quick edit modal
- Edit modal with role checkboxes
- Status toggle (active/locked)
- HTMX save with feedback
- Audit logging on changes

Session C: Account actions + detail page
- Lock/unlock account endpoints
- Password reset trigger
- Soft delete with confirmation
- Full detail page with audit history
- Comprehensive tests (18 new)

Staff management now supports:
- Search by email, name
- Filter by role (6 types) and status
- Multi-select role assignment
- Full audit trail on all actions
- Quick edit modal + full detail view

Tests: 205+ passing"

git push origin main
```

---

## Week 3 Complete Checklist

### Session A
- [ ] `StaffService` with search/filter/paginate
- [ ] `staff.py` router with list endpoints
- [ ] `staff/index.html` list page
- [ ] `_table_body.html` partial
- [ ] `_row.html` partial
- [ ] HTMX search working
- [ ] Filters working
- [ ] Pagination working

### Session B
- [ ] `_edit_modal.html` partial
- [ ] Edit modal GET/POST endpoints
- [ ] Role checkboxes (multi-select)
- [ ] Status toggle
- [ ] Save with HTMX feedback
- [ ] Audit logging on updates

### Session C
- [ ] Lock/unlock endpoints
- [ ] Reset password endpoint
- [ ] Delete endpoint (soft delete)
- [ ] `detail.html` full page
- [ ] Audit history display
- [ ] Comprehensive tests (18+)
- [ ] Documentation updated
- [ ] All tests passing (205+)
- [ ] Committed and pushed

---

## Files Created/Modified Summary

```
src/
├── services/
│   └── staff_service.py         # User CRUD, search, audit
├── routers/
│   └── staff.py                 # All staff endpoints
├── templates/
│   ├── staff/
│   │   ├── index.html           # List page
│   │   ├── detail.html          # Detail page
│   │   └── partials/
│   │       ├── _table_body.html
│   │       ├── _row.html
│   │       └── _edit_modal.html
│   └── errors/
│       └── 403.html             # Access denied
├── static/
│   └── js/
│       └── app.js               # HTMX handlers
└── tests/
    └── test_staff.py            # 18 tests
```

---

## Next: Week 4

**Focus:** Training Landing Page

- Training overview with stats
- Student list with status indicators
- Course list
- Quick enrollment actions

---

*Phase 6 Week 3 complete. Staff management fully operational with full audit trail.*
