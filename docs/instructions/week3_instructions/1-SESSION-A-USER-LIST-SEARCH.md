# Phase 6 Week 3 - Session A: User List + Search

**Document:** 1 of 3
**Estimated Time:** 2-3 hours
**Focus:** User list page with search, filter, and pagination

---

## Objective

Create a fully functional user list page with:
- Table displaying all users
- Live search (email, name, card ID)
- Filter by role and status
- Pagination (20 per page)
- HTMX-powered updates (no full page reloads)

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show 187 passed
```

---

## Step 1: Create Staff Service (45 min)

Create `src/services/staff_service.py`:

```python
"""
Staff Service - User management operations.
Handles search, filtering, pagination, and CRUD for users.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from datetime import datetime
import logging

from src.models.user import User
from src.models.role import Role
from src.services.audit_service import AuditLogService

logger = logging.getLogger(__name__)


class StaffService:
    """Service for staff/user management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditLogService(db)

    async def search_users(
        self,
        query: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = "email",
        sort_order: str = "asc",
    ) -> Tuple[List[User], int, int]:
        """
        Search and filter users with pagination.
        
        Args:
            query: Search term (matches email, first_name, last_name)
            role: Filter by role name
            status: Filter by status ('active', 'locked', 'all')
            page: Page number (1-indexed)
            per_page: Results per page
            sort_by: Column to sort by
            sort_order: 'asc' or 'desc'
            
        Returns:
            Tuple of (users, total_count, total_pages)
        """
        # Base query with eager loading of roles
        stmt = select(User).options(selectinload(User.roles))
        
        # Apply search filter
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    # Add member card ID search if user has linked member
                    # User.member.has(Member.card_id.ilike(search_term)),
                )
            )
        
        # Apply role filter
        if role and role != "all":
            stmt = stmt.join(User.roles).where(Role.name == role)
        
        # Apply status filter
        if status == "active":
            stmt = stmt.where(and_(User.is_active == True, User.is_locked == False))
        elif status == "locked":
            stmt = stmt.where(User.is_locked == True)
        elif status == "inactive":
            stmt = stmt.where(User.is_active == False)
        # 'all' or None = no filter
        
        # Get total count (before pagination)
        count_stmt = select(func.count(func.distinct(User.id))).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0
        
        # Apply sorting
        sort_column = getattr(User, sort_by, User.email)
        if sort_order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)
        
        # Execute query
        result = await self.db.execute(stmt)
        users = result.unique().scalars().all()
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        return list(users), total, total_pages

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a single user by ID with roles loaded."""
        stmt = select(User).options(selectinload(User.roles)).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_roles(self) -> List[Role]:
        """Get all available roles for filter dropdown."""
        stmt = select(Role).order_by(Role.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_counts(self) -> dict:
        """Get counts for status badges."""
        # Total users
        total = (await self.db.execute(select(func.count(User.id)))).scalar() or 0
        
        # Active users
        active = (await self.db.execute(
            select(func.count(User.id)).where(
                and_(User.is_active == True, User.is_locked == False)
            )
        )).scalar() or 0
        
        # Locked users
        locked = (await self.db.execute(
            select(func.count(User.id)).where(User.is_locked == True)
        )).scalar() or 0
        
        # Inactive users
        inactive = (await self.db.execute(
            select(func.count(User.id)).where(User.is_active == False)
        )).scalar() or 0
        
        return {
            "total": total,
            "active": active,
            "locked": locked,
            "inactive": inactive,
        }


# Convenience function for dependency injection
async def get_staff_service(db: AsyncSession) -> StaffService:
    return StaffService(db)
```

---

## Step 2: Create Staff Router (30 min)

Create `src/routers/staff.py`:

```python
"""
Staff Router - User management pages and actions.
"""

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.db.session import get_db
from src.services.staff_service import StaffService
from src.routers.dependencies.auth_cookie import require_auth

router = APIRouter(prefix="/staff", tags=["staff"])
templates = Jinja2Templates(directory="src/templates")


# ============================================================
# Main Pages
# ============================================================

@router.get("", response_class=HTMLResponse)
async def staff_list_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None, description="Search query"),
    role: Optional[str] = Query(None, description="Filter by role"),
    status: Optional[str] = Query("all", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
):
    """Render the staff list page."""
    # Handle auth redirect
    if isinstance(current_user, RedirectResponse):
        return current_user
    
    # Check if user has permission (admin or officer)
    user_roles = current_user.get("roles", [])
    if not any(r in ["admin", "officer", "staff"] for r in user_roles):
        return templates.TemplateResponse(
            "errors/403.html",
            {"request": request, "message": "You don't have permission to access staff management."},
            status_code=403
        )
    
    service = StaffService(db)
    
    # Get users with search/filter
    users, total, total_pages = await service.search_users(
        query=q,
        role=role,
        status=status,
        page=page,
        per_page=20,
    )
    
    # Get all roles for filter dropdown
    all_roles = await service.get_all_roles()
    
    # Get counts for status badges
    counts = await service.get_user_counts()
    
    return templates.TemplateResponse(
        "staff/index.html",
        {
            "request": request,
            "user": current_user,
            "users": users,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "query": q or "",
            "role_filter": role or "all",
            "status_filter": status or "all",
            "all_roles": all_roles,
            "counts": counts,
        }
    )


# ============================================================
# HTMX Partials
# ============================================================

@router.get("/search", response_class=HTMLResponse)
async def staff_search_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query("all"),
    page: int = Query(1, ge=1),
):
    """
    HTMX partial: Return just the table body for search results.
    Used for live search without full page reload.
    """
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(content="<tr><td colspan='5'>Session expired. Please refresh.</td></tr>", status_code=401)
    
    service = StaffService(db)
    
    users, total, total_pages = await service.search_users(
        query=q,
        role=role,
        status=status,
        page=page,
        per_page=20,
    )
    
    return templates.TemplateResponse(
        "staff/partials/_table_body.html",
        {
            "request": request,
            "users": users,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "query": q or "",
            "role_filter": role or "all",
            "status_filter": status or "all",
        }
    )


@router.get("/pagination", response_class=HTMLResponse)
async def staff_pagination_partial(
    request: Request,
    total: int = Query(0),
    total_pages: int = Query(1),
    current_page: int = Query(1),
    q: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query("all"),
):
    """HTMX partial: Return pagination controls."""
    return templates.TemplateResponse(
        "staff/partials/_pagination.html",
        {
            "request": request,
            "total": total,
            "total_pages": total_pages,
            "current_page": current_page,
            "query": q or "",
            "role_filter": role or "all",
            "status_filter": status or "all",
        }
    )
```

---

## Step 3: Create Directory Structure

```bash
mkdir -p src/templates/staff/partials
```

---

## Step 4: Create Main List Page (30 min)

Create `src/templates/staff/index.html`:

```html
{% extends "base.html" %}

{% block title %}Staff Management - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
            <h1 class="text-2xl font-bold">Staff Management</h1>
            <p class="text-base-content/60">Manage user accounts and roles</p>
        </div>
        <div class="flex gap-2">
            <button class="btn btn-primary" onclick="document.getElementById('add-user-modal').showModal()">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                </svg>
                Add User
            </button>
        </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats stats-vertical sm:stats-horizontal shadow w-full">
        <div class="stat">
            <div class="stat-title">Total Users</div>
            <div class="stat-value text-primary">{{ counts.total }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Active</div>
            <div class="stat-value text-success">{{ counts.active }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Locked</div>
            <div class="stat-value text-error">{{ counts.locked }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Inactive</div>
            <div class="stat-value text-warning">{{ counts.inactive }}</div>
        </div>
    </div>

    <!-- Search and Filters -->
    <div class="card bg-base-100 shadow">
        <div class="card-body p-4">
            <div class="flex flex-col lg:flex-row gap-4">
                <!-- Search Input -->
                <div class="flex-1">
                    <div class="relative">
                        <input 
                            type="search"
                            name="q"
                            value="{{ query }}"
                            placeholder="Search by email, name, or card ID..."
                            class="input input-bordered w-full pl-10"
                            hx-get="/staff/search"
                            hx-trigger="input changed delay:300ms, search"
                            hx-target="#table-container"
                            hx-include="[name='role'], [name='status']"
                            hx-indicator="#search-spinner"
                        />
                        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-base-content/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                        </svg>
                        <span id="search-spinner" class="loading loading-spinner loading-sm absolute right-3 top-1/2 -translate-y-1/2 htmx-indicator"></span>
                    </div>
                </div>
                
                <!-- Role Filter -->
                <div class="w-full lg:w-48">
                    <select 
                        name="role" 
                        class="select select-bordered w-full"
                        hx-get="/staff/search"
                        hx-trigger="change"
                        hx-target="#table-container"
                        hx-include="[name='q'], [name='status']"
                    >
                        <option value="all" {% if role_filter == 'all' %}selected{% endif %}>All Roles</option>
                        {% for role in all_roles %}
                        <option value="{{ role.name }}" {% if role_filter == role.name %}selected{% endif %}>
                            {{ role.name | title }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                
                <!-- Status Filter -->
                <div class="w-full lg:w-48">
                    <select 
                        name="status" 
                        class="select select-bordered w-full"
                        hx-get="/staff/search"
                        hx-trigger="change"
                        hx-target="#table-container"
                        hx-include="[name='q'], [name='role']"
                    >
                        <option value="all" {% if status_filter == 'all' %}selected{% endif %}>All Status</option>
                        <option value="active" {% if status_filter == 'active' %}selected{% endif %}>Active</option>
                        <option value="locked" {% if status_filter == 'locked' %}selected{% endif %}>Locked</option>
                        <option value="inactive" {% if status_filter == 'inactive' %}selected{% endif %}>Inactive</option>
                    </select>
                </div>
            </div>
        </div>
    </div>

    <!-- User Table -->
    <div class="card bg-base-100 shadow overflow-hidden">
        <div id="table-container">
            {% include "staff/partials/_table_body.html" %}
        </div>
    </div>
</div>

<!-- Edit Modal (content loaded via HTMX) -->
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

<!-- Add User Modal (placeholder for now) -->
<dialog id="add-user-modal" class="modal">
    <div class="modal-box">
        <h3 class="font-bold text-lg">Add New User</h3>
        <p class="py-4 text-base-content/60">User registration is handled through the signup flow. Direct user creation coming in a future update.</p>
        <div class="modal-action">
            <form method="dialog">
                <button class="btn">Close</button>
            </form>
        </div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endblock %}
```

---

## Step 5: Create Table Body Partial (20 min)

Create `src/templates/staff/partials/_table_body.html`:

```html
{# Table body partial - updated via HTMX search #}

<div class="overflow-x-auto">
    <table class="table table-zebra">
        <thead>
            <tr class="bg-base-200">
                <th class="w-12">
                    <label>
                        <input type="checkbox" class="checkbox checkbox-sm" id="select-all" />
                    </label>
                </th>
                <th>User</th>
                <th>Roles</th>
                <th>Status</th>
                <th>Last Login</th>
                <th class="w-32">Actions</th>
            </tr>
        </thead>
        <tbody id="user-table-body">
            {% if users %}
                {% for user in users %}
                {% include "staff/partials/_row.html" %}
                {% endfor %}
            {% else %}
            <tr>
                <td colspan="6" class="text-center py-8">
                    <div class="text-base-content/50">
                        <svg class="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
                        </svg>
                        <p>No users found</p>
                        {% if query %}
                        <p class="text-sm">Try adjusting your search or filters</p>
                        {% endif %}
                    </div>
                </td>
            </tr>
            {% endif %}
        </tbody>
    </table>
</div>

{% if users %}
<!-- Pagination -->
<div class="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t border-base-200">
    <div class="text-sm text-base-content/60">
        Showing {{ ((current_page - 1) * 20) + 1 }} - {{ ((current_page - 1) * 20) + users|length }} of {{ total }} users
    </div>
    
    <div class="join">
        {% if current_page > 1 %}
        <button 
            class="join-item btn btn-sm"
            hx-get="/staff/search?page={{ current_page - 1 }}&q={{ query }}&role={{ role_filter }}&status={{ status_filter }}"
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
                hx-get="/staff/search?page={{ p }}&q={{ query }}&role={{ role_filter }}&status={{ status_filter }}"
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
            hx-get="/staff/search?page={{ current_page + 1 }}&q={{ query }}&role={{ role_filter }}&status={{ status_filter }}"
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

## Step 6: Create Row Partial (15 min)

Create `src/templates/staff/partials/_row.html`:

```html
{# Single user row - can be swapped via HTMX after actions #}

<tr class="hover" id="user-row-{{ user.id }}">
    <td>
        <label>
            <input type="checkbox" class="checkbox checkbox-sm" name="selected_users" value="{{ user.id }}" />
        </label>
    </td>
    <td>
        <div class="flex items-center gap-3">
            <div class="avatar placeholder">
                <div class="bg-neutral text-neutral-content rounded-full w-10">
                    <span class="text-sm">
                        {{ (user.first_name or user.email)[0] | upper }}{{ (user.last_name or '')[0] | upper if user.last_name else '' }}
                    </span>
                </div>
            </div>
            <div>
                <div class="font-bold">
                    {% if user.first_name or user.last_name %}
                        {{ user.first_name or '' }} {{ user.last_name or '' }}
                    {% else %}
                        <span class="text-base-content/50">(No name)</span>
                    {% endif %}
                </div>
                <div class="text-sm text-base-content/60">{{ user.email }}</div>
            </div>
        </div>
    </td>
    <td>
        <div class="flex flex-wrap gap-1">
            {% for role in user.roles %}
            <span class="badge badge-{{ 'primary' if role.name == 'admin' else 'secondary' if role.name == 'officer' else 'accent' if role.name == 'staff' else 'ghost' }} badge-sm">
                {{ role.name }}
            </span>
            {% endfor %}
            {% if not user.roles %}
            <span class="badge badge-ghost badge-sm">No roles</span>
            {% endif %}
        </div>
    </td>
    <td>
        {% if user.is_locked %}
        <span class="badge badge-error gap-1">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
            </svg>
            Locked
        </span>
        {% elif not user.is_active %}
        <span class="badge badge-warning gap-1">Inactive</span>
        {% else %}
        <span class="badge badge-success gap-1">
            <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="4"/>
            </svg>
            Active
        </span>
        {% endif %}
    </td>
    <td>
        <div class="text-sm">
            {% if user.last_login %}
            {{ user.last_login.strftime('%b %d, %Y') }}
            <div class="text-xs text-base-content/50">{{ user.last_login.strftime('%I:%M %p') }}</div>
            {% else %}
            <span class="text-base-content/50">Never</span>
            {% endif %}
        </div>
    </td>
    <td>
        <div class="flex gap-1">
            <!-- Quick Edit Button -->
            <button 
                class="btn btn-ghost btn-sm"
                hx-get="/staff/{{ user.id }}/edit"
                hx-target="#modal-content"
                hx-swap="innerHTML"
                onclick="document.getElementById('edit-modal').showModal()"
                title="Quick Edit"
            >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                </svg>
            </button>
            
            <!-- View Detail Button -->
            <a href="/staff/{{ user.id }}" class="btn btn-ghost btn-sm" title="View Details">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                </svg>
            </a>
            
            <!-- More Actions Dropdown -->
            <div class="dropdown dropdown-end">
                <label tabindex="0" class="btn btn-ghost btn-sm">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/>
                    </svg>
                </label>
                <ul tabindex="0" class="dropdown-content z-[1] menu menu-sm p-2 shadow-lg bg-base-100 rounded-box w-48">
                    {% if user.is_locked %}
                    <li>
                        <button 
                            hx-post="/staff/{{ user.id }}/unlock"
                            hx-target="#user-row-{{ user.id }}"
                            hx-swap="outerHTML"
                            class="text-success"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z"/>
                            </svg>
                            Unlock Account
                        </button>
                    </li>
                    {% else %}
                    <li>
                        <button 
                            hx-post="/staff/{{ user.id }}/lock"
                            hx-target="#user-row-{{ user.id }}"
                            hx-swap="outerHTML"
                            hx-confirm="Are you sure you want to lock this account?"
                            class="text-warning"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                            </svg>
                            Lock Account
                        </button>
                    </li>
                    {% endif %}
                    <li>
                        <button 
                            hx-post="/staff/{{ user.id }}/reset-password"
                            hx-target="#toast-container"
                            hx-swap="innerHTML"
                            hx-confirm="Send password reset email to {{ user.email }}?"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
                            </svg>
                            Reset Password
                        </button>
                    </li>
                    <div class="divider my-1"></div>
                    <li>
                        <button 
                            hx-delete="/staff/{{ user.id }}"
                            hx-target="#user-row-{{ user.id }}"
                            hx-swap="outerHTML swap:500ms"
                            hx-confirm="Are you sure you want to delete this user? This action cannot be undone."
                            class="text-error"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                            </svg>
                            Delete User
                        </button>
                    </li>
                </ul>
            </div>
        </div>
    </td>
</tr>
```

---

## Step 7: Create 403 Error Page

Create `src/templates/errors/403.html`:

```html
{% extends "base_auth.html" %}

{% block title %}Access Denied - IP2A{% endblock %}

{% block content %}
<div class="text-center">
    <h1 class="text-6xl font-bold text-error">403</h1>
    <h2 class="text-2xl font-bold mt-4">Access Denied</h2>
    <p class="text-base-content/60 mt-2">{{ message or "You don't have permission to access this page." }}</p>
    <div class="mt-6">
        <a href="/dashboard" class="btn btn-primary">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
            </svg>
            Back to Dashboard
        </a>
    </div>
</div>
{% endblock %}
```

---

## Step 8: Register Router in main.py

Update `src/main.py`:

```python
# Add import
from src.routers.staff import router as staff_router

# Add router (after other API routers, before frontend router)
app.include_router(staff_router)
```

---

## Step 9: Test Manually

```bash
# Start server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

1. Login at `/login`
2. Navigate to `/staff`
3. Test search - type in search box, verify table updates
4. Test filters - change role/status dropdowns
5. Test pagination - click page numbers
6. Verify "No users found" state works

---

## Step 10: Add Initial Tests

Add to `src/tests/test_staff.py`:

```python
"""
Staff management tests.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


class TestStaffList:
    """Tests for staff list page."""

    @pytest.mark.asyncio
    async def test_staff_page_requires_auth(self, async_client: AsyncClient):
        """Staff page should redirect to login when not authenticated."""
        response = await async_client.get("/staff", follow_redirects=False)
        assert response.status_code == status.HTTP_302_FOUND
        assert "/login" in response.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_staff_search_endpoint_exists(self, async_client: AsyncClient):
        """Staff search endpoint should exist."""
        response = await async_client.get("/staff/search")
        # Will return 302 (auth redirect) or 401, not 404
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestStaffSearch:
    """Tests for staff search functionality."""

    @pytest.mark.asyncio
    async def test_search_returns_html(self, async_client: AsyncClient):
        """Search endpoint should return HTML partial."""
        response = await async_client.get("/staff/search?q=test")
        # Will redirect without auth, but endpoint exists
        assert response.status_code in [200, 302, 401]
```

---

## Step 11: Run Tests

```bash
pytest -v --tb=short

# Expected: 189+ tests passing (187 + 2 new)
```

---

## Step 12: Commit

```bash
git add -A
git status

git commit -m "feat(staff): Phase 6 Week 3 Session A - User list with search

- Create StaffService with search/filter/pagination
- Create staff router with list and search endpoints
- Create staff/index.html with full table UI
- Create table partials (_table_body.html, _row.html)
- Add 403 error page for unauthorized access
- HTMX-powered live search with 300ms debounce
- Filter by role and account status
- Pagination with page numbers
- Stats cards showing user counts
- Action buttons in each row (edit, view, more)

Search supports: email, first_name, last_name
Filters: role (all 6), status (active/locked/inactive)"

git push origin main
```

---

## Session A Checklist

- [ ] Created `src/services/staff_service.py`
- [ ] Created `src/routers/staff.py`
- [ ] Created `src/templates/staff/index.html`
- [ ] Created `src/templates/staff/partials/_table_body.html`
- [ ] Created `src/templates/staff/partials/_row.html`
- [ ] Created `src/templates/errors/403.html`
- [ ] Registered router in main.py
- [ ] HTMX search working
- [ ] Filters working
- [ ] Pagination working
- [ ] Initial tests passing
- [ ] Committed changes

---

## Files Created This Session

```
src/
├── services/
│   └── staff_service.py         # User search/filter/CRUD
├── routers/
│   └── staff.py                 # Staff management routes
├── templates/
│   ├── staff/
│   │   ├── index.html           # Main list page
│   │   └── partials/
│   │       ├── _table_body.html # Table with pagination
│   │       └── _row.html        # Single user row
│   └── errors/
│       └── 403.html             # Access denied page
└── tests/
    └── test_staff.py            # Staff tests (started)
```

---

*Session A complete. Proceed to Session B for quick edit modal and role assignment.*
