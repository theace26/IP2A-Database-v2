# Week 12 Session A: Settings & User Profile

**Project:** UnionCore (IP2A Database v2)
**Phase:** 6 - Frontend Implementation
**Week:** 12 - Settings & Profile
**Session:** A (of 2)
**Estimated Duration:** 3-4 hours
**Branch:** `develop` (ALWAYS work on develop, main is frozen for Railway demo)
**Prerequisite:** Week 11 complete (Audit Trail & Member History UI)

---

## Session Overview

This session implements user profile management and system settings pages. Users will be able to view their profile, change their password, and admins will have access to system configuration.

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

# 4. Verify Week 11 complete
pytest src/tests/test_audit_frontend.py -v
pytest src/tests/test_member_notes.py -v
pytest src/tests/test_inline_history.py -v
```

---

## Tasks

### Task 1: Create User Profile Service (30 min)

**Goal:** Service layer for user profile operations.

**File:** `src/services/profile_service.py`

```python
"""Service layer for user profile management."""
from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from src.models.user import User
from src.services.audit_service import audit_service

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ProfileService:
    """Service for user profile operations."""

    def get_profile(self, db: Session, user_id: int) -> Optional[User]:
        """Get user profile by ID."""
        return db.query(User).filter(User.id == user_id).first()

    def update_profile(
        self,
        db: Session,
        user: User,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> User:
        """Update user profile information."""
        old_values = {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": getattr(user, 'phone', None),
        }
        
        if email is not None:
            user.email = email
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if phone is not None and hasattr(user, 'phone'):
            user.phone = phone
        
        new_values = {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": getattr(user, 'phone', None),
        }
        
        # Audit the update
        audit_service.log_update(
            db=db,
            table_name="users",
            record_id=user.id,
            user_id=user.id,
            old_values=old_values,
            new_values=new_values,
        )
        
        db.commit()
        db.refresh(user)
        return user

    def change_password(
        self,
        db: Session,
        user: User,
        current_password: str,
        new_password: str,
    ) -> tuple[bool, str]:
        """
        Change user password.
        
        Returns:
            (success: bool, message: str)
        """
        # Verify current password
        if not pwd_context.verify(current_password, user.password_hash):
            return False, "Current password is incorrect"
        
        # Validate new password
        if len(new_password) < 8:
            return False, "New password must be at least 8 characters"
        
        if new_password == current_password:
            return False, "New password must be different from current password"
        
        # Hash and save new password
        user.password_hash = pwd_context.hash(new_password)
        
        # Audit the password change (don't log actual password)
        audit_service.log_update(
            db=db,
            table_name="users",
            record_id=user.id,
            user_id=user.id,
            old_values={"password": "[CHANGED]"},
            new_values={"password": "[CHANGED]"},
            notes="Password changed by user",
        )
        
        db.commit()
        return True, "Password changed successfully"

    def get_user_activity_summary(self, db: Session, user_id: int) -> dict:
        """Get summary of user's recent activity."""
        from src.models.audit_log import AuditLog
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Count actions this week
        action_counts = db.query(
            AuditLog.action,
            func.count(AuditLog.id)
        ).filter(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= week_ago
        ).group_by(AuditLog.action).all()
        
        # Get last login (from audit log or session)
        last_login = db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.table_name == "user_sessions",
            AuditLog.action == "CREATE"
        ).order_by(AuditLog.created_at.desc()).first()
        
        return {
            "actions_this_week": dict(action_counts),
            "total_actions_this_week": sum(c for _, c in action_counts),
            "last_login": last_login.created_at if last_login else None,
        }


# Singleton instance
profile_service = ProfileService()
```

---

### Task 2: Create Profile Frontend Router (45 min)

**File:** `src/routers/profile_frontend.py`

```python
"""Frontend routes for user profile management."""
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models.user import User
from src.routers.dependencies.auth_cookie import get_current_user_cookie
from src.services.profile_service import profile_service
from src.templates import templates

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    """User profile page."""
    activity = profile_service.get_user_activity_summary(db, current_user.id)
    
    return templates.TemplateResponse(
        "profile/index.html",
        {
            "request": request,
            "current_user": current_user,
            "page_title": "My Profile",
            "activity": activity,
        }
    )


@router.get("/edit", response_class=HTMLResponse)
async def edit_profile_page(
    request: Request,
    current_user: User = Depends(get_current_user_cookie),
):
    """Edit profile page."""
    return templates.TemplateResponse(
        "profile/edit.html",
        {
            "request": request,
            "current_user": current_user,
            "page_title": "Edit Profile",
        }
    )


@router.post("/edit", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    email: str = Form(...),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    """Update user profile."""
    try:
        profile_service.update_profile(
            db=db,
            user=current_user,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
        )
        
        # Redirect with success message
        return RedirectResponse(
            url="/profile?message=Profile+updated+successfully",
            status_code=303
        )
    except Exception as e:
        return templates.TemplateResponse(
            "profile/edit.html",
            {
                "request": request,
                "current_user": current_user,
                "page_title": "Edit Profile",
                "error": str(e),
            }
        )


@router.get("/password", response_class=HTMLResponse)
async def change_password_page(
    request: Request,
    current_user: User = Depends(get_current_user_cookie),
):
    """Change password page."""
    return templates.TemplateResponse(
        "profile/password.html",
        {
            "request": request,
            "current_user": current_user,
            "page_title": "Change Password",
        }
    )


@router.post("/password", response_class=HTMLResponse)
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    """Process password change."""
    # Validate confirmation matches
    if new_password != confirm_password:
        return templates.TemplateResponse(
            "profile/password.html",
            {
                "request": request,
                "current_user": current_user,
                "page_title": "Change Password",
                "error": "New passwords do not match",
            }
        )
    
    success, message = profile_service.change_password(
        db=db,
        user=current_user,
        current_password=current_password,
        new_password=new_password,
    )
    
    if success:
        return RedirectResponse(
            url="/profile?message=Password+changed+successfully",
            status_code=303
        )
    else:
        return templates.TemplateResponse(
            "profile/password.html",
            {
                "request": request,
                "current_user": current_user,
                "page_title": "Change Password",
                "error": message,
            }
        )


@router.get("/activity", response_class=HTMLResponse)
async def activity_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    """User's own activity log."""
    from src.services.audit_frontend_service import audit_frontend_service
    
    result = audit_frontend_service.get_audit_logs(
        db=db,
        current_user=current_user,
        user_id=current_user.id,  # Filter to own activity
        page=1,
        per_page=50,
    )
    
    return templates.TemplateResponse(
        "profile/activity.html",
        {
            "request": request,
            "current_user": current_user,
            "page_title": "My Activity",
            "logs": result["items"],
            "total": result["total"],
        }
    )
```

---

### Task 3: Create Profile Templates (60 min)

#### 3.1 Profile Index Page

**File:** `src/templates/profile/index.html`

```html
{% extends "base_auth.html" %}

{% block title %}{{ page_title }}{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto space-y-6">
    <!-- Success Message -->
    {% if request.query_params.get('message') %}
    <div class="alert alert-success">
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{{ request.query_params.get('message') | replace('+', ' ') }}</span>
    </div>
    {% endif %}

    <!-- Profile Header -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <div class="flex items-center gap-6">
                <!-- Avatar -->
                <div class="avatar placeholder">
                    <div class="bg-primary text-primary-content rounded-full w-24">
                        <span class="text-3xl">
                            {{ current_user.first_name[0] if current_user.first_name else current_user.email[0] | upper }}
                        </span>
                    </div>
                </div>
                
                <!-- Info -->
                <div class="flex-1">
                    <h1 class="text-2xl font-bold">
                        {% if current_user.first_name %}
                        {{ current_user.first_name }} {{ current_user.last_name or '' }}
                        {% else %}
                        {{ current_user.email }}
                        {% endif %}
                    </h1>
                    <p class="text-gray-600">{{ current_user.email }}</p>
                    <div class="badge badge-primary mt-2">{{ current_user.role | title }}</div>
                </div>
                
                <!-- Actions -->
                <div class="flex gap-2">
                    <a href="/profile/edit" class="btn btn-outline btn-sm">
                        Edit Profile
                    </a>
                    <a href="/profile/password" class="btn btn-outline btn-sm">
                        Change Password
                    </a>
                </div>
            </div>
        </div>
    </div>

    <!-- Profile Details -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Account Info -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title">Account Information</h2>
                <div class="space-y-3 mt-4">
                    <div class="flex justify-between">
                        <span class="text-gray-600">Email</span>
                        <span class="font-medium">{{ current_user.email }}</span>
                    </div>
                    <div class="divider my-1"></div>
                    <div class="flex justify-between">
                        <span class="text-gray-600">Role</span>
                        <span class="font-medium">{{ current_user.role | title }}</span>
                    </div>
                    <div class="divider my-1"></div>
                    <div class="flex justify-between">
                        <span class="text-gray-600">Account Status</span>
                        <span class="badge badge-success">Active</span>
                    </div>
                    <div class="divider my-1"></div>
                    <div class="flex justify-between">
                        <span class="text-gray-600">Member Since</span>
                        <span class="font-medium">
                            {{ current_user.created_at.strftime('%B %d, %Y') if current_user.created_at else 'N/A' }}
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Activity Summary -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex justify-between items-center">
                    <h2 class="card-title">Recent Activity</h2>
                    <a href="/profile/activity" class="link link-primary text-sm">View All →</a>
                </div>
                
                <div class="stats stats-vertical shadow mt-4">
                    <div class="stat">
                        <div class="stat-title">Actions This Week</div>
                        <div class="stat-value text-primary">{{ activity.total_actions_this_week }}</div>
                    </div>
                    {% if activity.last_login %}
                    <div class="stat">
                        <div class="stat-title">Last Login</div>
                        <div class="stat-value text-lg">
                            {{ activity.last_login.strftime('%b %d, %Y') }}
                        </div>
                        <div class="stat-desc">
                            {{ activity.last_login.strftime('%I:%M %p') }}
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>

    <!-- Quick Links -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Quick Links</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <a href="/dashboard" class="btn btn-ghost btn-outline">
                    Dashboard
                </a>
                <a href="/profile/activity" class="btn btn-ghost btn-outline">
                    My Activity
                </a>
                {% if current_user.role in ['admin', 'officer'] %}
                <a href="/admin/audit-logs" class="btn btn-ghost btn-outline">
                    System Logs
                </a>
                {% endif %}
                {% if current_user.role == 'admin' %}
                <a href="/admin/settings" class="btn btn-ghost btn-outline">
                    System Settings
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

#### 3.2 Edit Profile Page

**File:** `src/templates/profile/edit.html`

```html
{% extends "base_auth.html" %}

{% block title %}{{ page_title }}{% endblock %}

{% block content %}
<div class="max-w-xl mx-auto">
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h1 class="card-title text-2xl mb-4">Edit Profile</h1>
            
            {% if error %}
            <div class="alert alert-error mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{{ error }}</span>
            </div>
            {% endif %}
            
            <form method="POST" action="/profile/edit" class="space-y-4">
                <!-- Email -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Email Address</span>
                    </label>
                    <input type="email" name="email" 
                           class="input input-bordered" 
                           value="{{ current_user.email }}"
                           required>
                </div>
                
                <!-- First Name -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">First Name</span>
                    </label>
                    <input type="text" name="first_name" 
                           class="input input-bordered" 
                           value="{{ current_user.first_name or '' }}">
                </div>
                
                <!-- Last Name -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Last Name</span>
                    </label>
                    <input type="text" name="last_name" 
                           class="input input-bordered" 
                           value="{{ current_user.last_name or '' }}">
                </div>
                
                <!-- Phone (if exists) -->
                {% if current_user.phone is defined %}
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Phone Number</span>
                    </label>
                    <input type="tel" name="phone" 
                           class="input input-bordered" 
                           value="{{ current_user.phone or '' }}"
                           placeholder="(555) 555-5555">
                </div>
                {% endif %}
                
                <!-- Actions -->
                <div class="flex gap-4 mt-6">
                    <a href="/profile" class="btn btn-ghost">Cancel</a>
                    <button type="submit" class="btn btn-primary flex-1">
                        Save Changes
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

#### 3.3 Change Password Page

**File:** `src/templates/profile/password.html`

```html
{% extends "base_auth.html" %}

{% block title %}{{ page_title }}{% endblock %}

{% block content %}
<div class="max-w-xl mx-auto">
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h1 class="card-title text-2xl mb-4">Change Password</h1>
            
            {% if error %}
            <div class="alert alert-error mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{{ error }}</span>
            </div>
            {% endif %}
            
            <form method="POST" action="/profile/password" class="space-y-4">
                <!-- Current Password -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Current Password</span>
                    </label>
                    <input type="password" name="current_password" 
                           class="input input-bordered" 
                           required
                           autocomplete="current-password">
                </div>
                
                <!-- New Password -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">New Password</span>
                    </label>
                    <input type="password" name="new_password" 
                           class="input input-bordered" 
                           required
                           minlength="8"
                           autocomplete="new-password">
                    <label class="label">
                        <span class="label-text-alt text-gray-500">
                            Minimum 8 characters
                        </span>
                    </label>
                </div>
                
                <!-- Confirm Password -->
                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Confirm New Password</span>
                    </label>
                    <input type="password" name="confirm_password" 
                           class="input input-bordered" 
                           required
                           minlength="8"
                           autocomplete="new-password">
                </div>
                
                <!-- Password Requirements -->
                <div class="alert">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <div>
                        <div class="text-sm font-medium">Password Requirements:</div>
                        <ul class="text-xs mt-1 list-disc list-inside">
                            <li>At least 8 characters long</li>
                            <li>Must be different from current password</li>
                        </ul>
                    </div>
                </div>
                
                <!-- Actions -->
                <div class="flex gap-4 mt-6">
                    <a href="/profile" class="btn btn-ghost">Cancel</a>
                    <button type="submit" class="btn btn-primary flex-1">
                        Change Password
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

#### 3.4 Activity Page

**File:** `src/templates/profile/activity.html`

```html
{% extends "base_auth.html" %}

{% block title %}{{ page_title }}{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
        <div>
            <h1 class="text-2xl font-bold">My Activity</h1>
            <p class="text-gray-600">Your recent actions in the system</p>
        </div>
        <a href="/profile" class="btn btn-ghost">← Back to Profile</a>
    </div>

    <!-- Activity List -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <div class="text-sm text-gray-600 mb-4">
                Showing {{ logs|length }} of {{ total }} activities
            </div>
            
            {% if logs %}
            <div class="overflow-x-auto">
                <table class="table table-zebra">
                    <thead>
                        <tr>
                            <th>Date/Time</th>
                            <th>Action</th>
                            <th>Table</th>
                            <th>Record</th>
                            <th>Notes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for log in logs %}
                        <tr>
                            <td class="text-sm">
                                {{ log.changed_at[:19].replace('T', ' ') if log.changed_at else 'N/A' }}
                            </td>
                            <td>
                                {% if log.action == 'CREATE' %}
                                <span class="badge badge-success badge-sm">{{ log.action }}</span>
                                {% elif log.action == 'UPDATE' %}
                                <span class="badge badge-warning badge-sm">{{ log.action }}</span>
                                {% elif log.action == 'DELETE' %}
                                <span class="badge badge-error badge-sm">{{ log.action }}</span>
                                {% else %}
                                <span class="badge badge-sm">{{ log.action }}</span>
                                {% endif %}
                            </td>
                            <td>{{ log.table_name }}</td>
                            <td class="font-mono text-sm">{{ log.record_id }}</td>
                            <td class="text-sm text-gray-600">{{ log.notes or '-' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <div class="text-center py-8 text-gray-500">
                No activity recorded yet
            </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
```

---

### Task 4: Create System Settings (Admin Only) (45 min)

**File:** `src/routers/settings_frontend.py`

```python
"""Frontend routes for system settings (admin only)."""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models.user import User
from src.routers.dependencies.auth_cookie import get_current_user_cookie
from src.templates import templates

router = APIRouter(prefix="/admin/settings", tags=["settings"])


def require_admin(current_user: User = Depends(get_current_user_cookie)):
    """Dependency that requires admin role."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """System settings page (admin only)."""
    from src.config.settings import settings
    
    # Get system info
    system_info = {
        "app_name": settings.APP_NAME if hasattr(settings, 'APP_NAME') else "UnionCore",
        "environment": settings.ENVIRONMENT if hasattr(settings, 'ENVIRONMENT') else "development",
        "database_url": _mask_url(settings.DATABASE_URL) if hasattr(settings, 'DATABASE_URL') else "Not configured",
        "stripe_configured": bool(settings.STRIPE_SECRET_KEY) if hasattr(settings, 'STRIPE_SECRET_KEY') else False,
        "s3_configured": bool(settings.S3_BUCKET_NAME) if hasattr(settings, 'S3_BUCKET_NAME') else False,
    }
    
    # Get user counts
    from src.models.user import User as UserModel
    user_stats = {
        "total_users": db.query(UserModel).count(),
        "active_users": db.query(UserModel).filter(UserModel.is_active == True).count(),
        "admin_users": db.query(UserModel).filter(UserModel.role == "admin").count(),
    }
    
    return templates.TemplateResponse(
        "admin/settings.html",
        {
            "request": request,
            "current_user": current_user,
            "page_title": "System Settings",
            "system_info": system_info,
            "user_stats": user_stats,
        }
    )


def _mask_url(url: str) -> str:
    """Mask sensitive parts of database URL."""
    if not url:
        return "Not configured"
    if "@" in url:
        # Mask password
        parts = url.split("@")
        if ":" in parts[0]:
            protocol_user = parts[0].rsplit(":", 1)
            return f"{protocol_user[0]}:****@{parts[1]}"
    return url
```

**File:** `src/templates/admin/settings.html`

```html
{% extends "base_auth.html" %}

{% block title %}{{ page_title }}{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto space-y-6">
    <!-- Header -->
    <div>
        <h1 class="text-2xl font-bold">System Settings</h1>
        <p class="text-gray-600">View system configuration and status</p>
    </div>

    <!-- System Status -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">System Status</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <div class="stat bg-base-200 rounded-lg">
                    <div class="stat-title">Environment</div>
                    <div class="stat-value text-lg">
                        {{ system_info.environment | title }}
                    </div>
                </div>
                <div class="stat bg-base-200 rounded-lg">
                    <div class="stat-title">Stripe</div>
                    <div class="stat-value text-lg">
                        {% if system_info.stripe_configured %}
                        <span class="text-success">Configured</span>
                        {% else %}
                        <span class="text-warning">Not Configured</span>
                        {% endif %}
                    </div>
                </div>
                <div class="stat bg-base-200 rounded-lg">
                    <div class="stat-title">S3 Storage</div>
                    <div class="stat-value text-lg">
                        {% if system_info.s3_configured %}
                        <span class="text-success">Configured</span>
                        {% else %}
                        <span class="text-warning">Not Configured</span>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- User Statistics -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">User Statistics</h2>
            <div class="stats stats-vertical lg:stats-horizontal shadow mt-4">
                <div class="stat">
                    <div class="stat-title">Total Users</div>
                    <div class="stat-value">{{ user_stats.total_users }}</div>
                </div>
                <div class="stat">
                    <div class="stat-title">Active Users</div>
                    <div class="stat-value text-success">{{ user_stats.active_users }}</div>
                </div>
                <div class="stat">
                    <div class="stat-title">Admin Users</div>
                    <div class="stat-value text-primary">{{ user_stats.admin_users }}</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Configuration -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Configuration</h2>
            <div class="overflow-x-auto mt-4">
                <table class="table">
                    <tbody>
                        <tr>
                            <td class="font-medium">Application Name</td>
                            <td>{{ system_info.app_name }}</td>
                        </tr>
                        <tr>
                            <td class="font-medium">Database</td>
                            <td class="font-mono text-sm">{{ system_info.database_url }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="alert alert-info mt-4">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span>To modify system settings, update environment variables and restart the application.</span>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

### Task 5: Register Routers and Update Navigation (15 min)

#### 5.1 Register Routers

**File:** `src/main.py`

```python
from src.routers.profile_frontend import router as profile_frontend_router
from src.routers.settings_frontend import router as settings_frontend_router

# ... in router registration section ...
app.include_router(profile_frontend_router)
app.include_router(settings_frontend_router)
```

#### 5.2 Update Sidebar Navigation

**File:** `src/templates/components/_sidebar.html`

Add profile link to user dropdown or create user menu:

```html
<!-- User Menu (bottom of sidebar) -->
<div class="mt-auto pt-4 border-t">
    <ul class="menu">
        <li>
            <a href="/profile">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                My Profile
            </a>
        </li>
        {% if current_user.role == 'admin' %}
        <li>
            <a href="/admin/settings">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                System Settings
            </a>
        </li>
        {% endif %}
    </ul>
</div>
```

---

### Task 6: Write Tests (30 min)

**File:** `src/tests/test_profile.py`

```python
"""Tests for user profile functionality."""
import pytest


class TestProfileService:
    """Tests for ProfileService."""

    def test_get_profile(self, db_session, test_user):
        """Should retrieve user profile."""
        from src.services.profile_service import profile_service
        profile = profile_service.get_profile(db_session, test_user.id)
        assert profile is not None
        assert profile.id == test_user.id

    def test_update_profile(self, db_session, test_user):
        """Should update user profile."""
        from src.services.profile_service import profile_service
        updated = profile_service.update_profile(
            db_session, test_user,
            first_name="Updated",
            last_name="User"
        )
        assert updated.first_name == "Updated"
        assert updated.last_name == "User"

    def test_change_password_wrong_current(self, db_session, test_user):
        """Should reject wrong current password."""
        from src.services.profile_service import profile_service
        success, message = profile_service.change_password(
            db_session, test_user,
            current_password="wrongpassword",
            new_password="newpassword123"
        )
        assert success == False
        assert "incorrect" in message.lower()

    def test_change_password_too_short(self, db_session, test_user):
        """Should reject short password."""
        from src.services.profile_service import profile_service
        success, message = profile_service.change_password(
            db_session, test_user,
            current_password="correctpassword",  # Adjust to actual test password
            new_password="short"
        )
        assert success == False
        assert "8 characters" in message


class TestProfileFrontend:
    """Tests for profile frontend routes."""

    def test_profile_page_requires_auth(self, client):
        """Profile page requires authentication."""
        response = client.get("/profile")
        assert response.status_code in [401, 302]

    def test_profile_page_renders(self, client, auth_cookies):
        """Profile page renders for authenticated user."""
        response = client.get("/profile", cookies=auth_cookies)
        assert response.status_code == 200
        assert b"My Profile" in response.content

    def test_edit_profile_page(self, client, auth_cookies):
        """Edit profile page renders."""
        response = client.get("/profile/edit", cookies=auth_cookies)
        assert response.status_code == 200
        assert b"Edit Profile" in response.content

    def test_password_page(self, client, auth_cookies):
        """Change password page renders."""
        response = client.get("/profile/password", cookies=auth_cookies)
        assert response.status_code == 200
        assert b"Change Password" in response.content

    def test_activity_page(self, client, auth_cookies):
        """Activity page renders."""
        response = client.get("/profile/activity", cookies=auth_cookies)
        assert response.status_code == 200
        assert b"My Activity" in response.content


class TestSystemSettings:
    """Tests for system settings (admin only)."""

    def test_settings_requires_admin(self, client, staff_auth_cookies):
        """Settings page requires admin role."""
        response = client.get("/admin/settings", cookies=staff_auth_cookies)
        assert response.status_code == 403

    def test_admin_can_view_settings(self, client, admin_auth_cookies):
        """Admin can view settings page."""
        response = client.get("/admin/settings", cookies=admin_auth_cookies)
        assert response.status_code == 200
        assert b"System Settings" in response.content
```

---

## Acceptance Criteria

- [ ] Profile service with get, update, change password
- [ ] Profile page shows user info and activity summary
- [ ] Edit profile page allows updating email, name
- [ ] Change password validates current password
- [ ] Change password enforces minimum length
- [ ] Activity page shows user's own audit logs
- [ ] System settings page (admin only)
- [ ] Settings shows system status and configuration
- [ ] Sidebar includes profile and settings links
- [ ] All tests pass (~15 new tests)

---

## Files Created

```
src/services/profile_service.py
src/routers/profile_frontend.py
src/routers/settings_frontend.py
src/templates/profile/index.html
src/templates/profile/edit.html
src/templates/profile/password.html
src/templates/profile/activity.html
src/templates/admin/settings.html
src/tests/test_profile.py
```

## Files Modified

```
src/main.py                              # Register profile + settings routers
src/templates/components/_sidebar.html   # Add profile + settings links
```

---

## Next Session Preview

**Week 12 Session B: Email Preferences & Notifications** (optional) will add:
- Email notification preferences
- Notification settings UI
- Email templates for system events

Or proceed to **Deployment Preparation** for Railway production setup.

---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** 

### Before Ending This Session:

Scan all documentation in `/app/*`. Update *ANY* & *ALL* relevant documentation as necessary with current progress for the historical record. Do not forget to update ADRs, Roadmap, Checklist, again only if necessary.

**Documentation Checklist:**

| Document | Updated? | Notes |
|----------|----------|-------|
| CLAUDE.md | [ ] | Update to v0.8.3, mark Week 12 Session A complete |
| CHANGELOG.md | [ ] | Add profile + settings entry |
| CONTINUITY.md | [ ] | Update current status |
| IP2A_MILESTONE_CHECKLIST.md | [ ] | Update Week 12 progress |
| IP2A_BACKEND_ROADMAP.md | [ ] | Update roadmap status |
| Session log created | [ ] | `docs/reports/session-logs/` |

This ensures historical record-keeping and project continuity ("bus factor" protection).

---

*End of instruction document*
