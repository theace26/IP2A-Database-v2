# Week 11 Session B: Audit UI & Role Permissions

**Project:** UnionCore (IP2A Database v2)
**Phase:** 6 - Frontend Implementation
**Week:** 11 - Audit Trail & Member History UI
**Session:** B (of 3)
**Estimated Duration:** 3-4 hours
**Branch:** `develop` (ALWAYS work on develop, main is frozen for Railway demo)
**Prerequisite:** Week 11 Session A complete (immutability trigger + member_notes table)

---

## Session Overview

This session implements the audit log viewer UI with role-based access control and field-level redaction. Staff will be able to view audit history filtered by their permission level, with sensitive fields automatically masked for non-admin users.

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

# 4. Verify Session A complete
# - audit_logs immutability trigger exists
# - member_notes table exists
# - MemberNoteService working
pytest src/tests/test_audit_immutability.py -v
pytest src/tests/test_member_notes.py -v

# 5. Check current audit_logs structure
# psql: \d audit_logs
```

---

## Tasks

### Task 1: Define Audit Permission Constants (30 min)

**Goal:** Create structured permission system for audit access.

#### 1.1 Create Audit Permissions Module

**File:** `src/core/permissions.py` (create or extend)

```python
"""Permission constants for role-based access control."""
from enum import Enum
from typing import Dict, List


class AuditPermission(str, Enum):
    """Audit-specific permissions."""
    VIEW_OWN = "audit:view_own"              # View entities user touched
    VIEW_MEMBERS = "audit:view_members"       # View all member-related audits
    VIEW_USERS = "audit:view_users"           # View user account audits
    VIEW_ALL = "audit:view_all"               # View everything
    EXPORT = "audit:export"                   # Export audit reports


# Map roles to their audit permissions
ROLE_AUDIT_PERMISSIONS: Dict[str, List[AuditPermission]] = {
    "member": [],  # No audit access
    "staff": [AuditPermission.VIEW_OWN],
    "instructor": [AuditPermission.VIEW_OWN],
    "organizer": [AuditPermission.VIEW_OWN, AuditPermission.VIEW_MEMBERS],
    "officer": [AuditPermission.VIEW_MEMBERS, AuditPermission.VIEW_USERS],
    "admin": [
        AuditPermission.VIEW_ALL, 
        AuditPermission.VIEW_USERS, 
        AuditPermission.EXPORT
    ],
}


def get_audit_permissions(role: str) -> List[AuditPermission]:
    """Get audit permissions for a role."""
    return ROLE_AUDIT_PERMISSIONS.get(role, [])


def has_audit_permission(role: str, permission: AuditPermission) -> bool:
    """Check if a role has a specific audit permission."""
    return permission in get_audit_permissions(role)


# Sensitive fields that should be redacted for non-admin users
SENSITIVE_FIELDS = {
    "ssn",
    "social_security",
    "social_security_number",
    "bank_account",
    "bank_account_number",
    "routing_number",
    "password",
    "password_hash",
    "token_hash",
    "refresh_token",
    "api_key",
    "secret_key",
}


def redact_sensitive_fields(data: dict, user_role: str) -> dict:
    """
    Redact sensitive fields based on user role.
    Admin users see all fields unredacted.
    """
    if data is None:
        return None
    
    if user_role == "admin":
        return data  # Admins see everything
    
    redacted = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            redacted[key] = "[REDACTED]"
        elif isinstance(value, dict):
            redacted[key] = redact_sensitive_fields(value, user_role)
        else:
            redacted[key] = value
    
    return redacted
```

---

### Task 2: Create AuditFrontendService (60 min)

**Goal:** Service layer for querying audit logs with role-based filtering.

**File:** `src/services/audit_frontend_service.py`

```python
"""Frontend service for audit log queries with role-based filtering."""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from src.models.audit_log import AuditLog
from src.models.user import User
from src.core.permissions import (
    AuditPermission, 
    has_audit_permission, 
    redact_sensitive_fields,
    SENSITIVE_FIELDS
)


class AuditFrontendService:
    """Service for audit log frontend queries."""

    # Tables that contain member-related data
    MEMBER_TABLES = {
        "members", "member_notes", "member_employments",
        "dues_payments", "dues_adjustments",
        "grievances", "benevolence_applications",
        "salting_activities", "students",
    }

    # Tables that contain user/system data
    USER_TABLES = {
        "users", "user_sessions", "password_resets",
    }

    def get_audit_logs(
        self,
        db: Session,
        current_user: User,
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Dict[str, Any]:
        """
        Query audit logs with role-based filtering.
        
        Returns:
            {
                "items": [...],
                "total": int,
                "page": int,
                "per_page": int,
                "pages": int,
            }
        """
        query = db.query(AuditLog)
        
        # Apply role-based table filtering
        query = self._apply_role_filter(query, current_user)
        
        # Apply search filters
        if table_name:
            query = query.filter(AuditLog.table_name == table_name)
        
        if record_id:
            query = query.filter(AuditLog.record_id == str(record_id))
        
        if action:
            query = query.filter(AuditLog.action == action.upper())
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if date_from:
            query = query.filter(AuditLog.created_at >= datetime.combine(date_from, datetime.min.time()))
        
        if date_to:
            query = query.filter(AuditLog.created_at <= datetime.combine(date_to, datetime.max.time()))
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    AuditLog.table_name.ilike(search_pattern),
                    AuditLog.changed_by.ilike(search_pattern),
                    AuditLog.notes.ilike(search_pattern),
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(per_page).all()
        
        # Redact sensitive fields based on role
        items = [self._format_log(log, current_user.role) for log in logs]
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }

    def _apply_role_filter(self, query, user: User):
        """Apply table filtering based on user's audit permissions."""
        role = user.role
        
        # Admin with VIEW_ALL sees everything
        if has_audit_permission(role, AuditPermission.VIEW_ALL):
            return query
        
        allowed_tables = set()
        
        # VIEW_MEMBERS permission grants access to member tables
        if has_audit_permission(role, AuditPermission.VIEW_MEMBERS):
            allowed_tables.update(self.MEMBER_TABLES)
        
        # VIEW_USERS permission grants access to user tables
        if has_audit_permission(role, AuditPermission.VIEW_USERS):
            allowed_tables.update(self.USER_TABLES)
        
        # VIEW_OWN grants access only to logs the user created
        if has_audit_permission(role, AuditPermission.VIEW_OWN):
            if allowed_tables:
                # User can see their own logs OR logs from allowed tables
                return query.filter(
                    or_(
                        AuditLog.user_id == user.id,
                        AuditLog.table_name.in_(allowed_tables)
                    )
                )
            else:
                # User can only see their own logs
                return query.filter(AuditLog.user_id == user.id)
        
        # If user has no permissions but has allowed tables
        if allowed_tables:
            return query.filter(AuditLog.table_name.in_(allowed_tables))
        
        # No access - return empty result
        return query.filter(False)  # Always false = no results

    def _format_log(self, log: AuditLog, user_role: str) -> dict:
        """Format audit log with redaction for non-admin users."""
        return {
            "id": log.id,
            "table_name": log.table_name,
            "record_id": log.record_id,
            "action": log.action,
            "old_values": redact_sensitive_fields(log.old_values, user_role),
            "new_values": redact_sensitive_fields(log.new_values, user_role),
            "changed_fields": log.changed_fields,
            "changed_by": log.changed_by,
            "changed_at": log.created_at.isoformat() if log.created_at else None,
            "ip_address": log.ip_address if user_role == "admin" else None,
            "user_agent": None,  # Never expose user agent
            "notes": log.notes,
        }

    def get_entity_history(
        self,
        db: Session,
        current_user: User,
        table_name: str,
        record_id: str,
        limit: int = 20,
    ) -> List[dict]:
        """Get audit history for a specific entity."""
        query = db.query(AuditLog).filter(
            AuditLog.table_name == table_name,
            AuditLog.record_id == str(record_id),
        )
        
        # Apply role filter
        query = self._apply_role_filter(query, current_user)
        
        logs = query.order_by(desc(AuditLog.created_at)).limit(limit).all()
        
        return [self._format_log(log, current_user.role) for log in logs]

    def get_available_tables(self, user: User) -> List[str]:
        """Get list of tables the user can view audits for."""
        role = user.role
        
        if has_audit_permission(role, AuditPermission.VIEW_ALL):
            return sorted(self.MEMBER_TABLES | self.USER_TABLES | {"audit_logs"})
        
        available = set()
        
        if has_audit_permission(role, AuditPermission.VIEW_MEMBERS):
            available.update(self.MEMBER_TABLES)
        
        if has_audit_permission(role, AuditPermission.VIEW_USERS):
            available.update(self.USER_TABLES)
        
        return sorted(available)

    def get_action_types(self) -> List[str]:
        """Get list of possible action types."""
        return ["CREATE", "READ", "UPDATE", "DELETE", "BULK_READ"]

    def get_stats(self, db: Session, current_user: User) -> dict:
        """Get audit statistics for dashboard."""
        from sqlalchemy import func
        from datetime import timedelta
        
        query = db.query(AuditLog)
        query = self._apply_role_filter(query, current_user)
        
        today = date.today()
        week_ago = today - timedelta(days=7)
        
        # Count by action type (last 7 days)
        action_counts = db.query(
            AuditLog.action,
            func.count(AuditLog.id)
        ).filter(
            AuditLog.created_at >= datetime.combine(week_ago, datetime.min.time())
        ).group_by(AuditLog.action).all()
        
        return {
            "total_logs": query.count(),
            "logs_this_week": query.filter(
                AuditLog.created_at >= datetime.combine(week_ago, datetime.min.time())
            ).count(),
            "logs_today": query.filter(
                AuditLog.created_at >= datetime.combine(today, datetime.min.time())
            ).count(),
            "action_breakdown": {action: count for action, count in action_counts},
        }


# Singleton instance
audit_frontend_service = AuditFrontendService()
```

---

### Task 3: Create Audit Log List Page (60 min)

**Goal:** Admin UI page for viewing and filtering audit logs.

#### 3.1 Add Audit Frontend Router

**File:** `src/routers/audit_frontend.py`

```python
"""Frontend routes for audit log viewing."""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
import csv
import io

from src.db.session import get_db
from src.models.user import User
from src.routers.dependencies.auth_cookie import get_current_user_cookie
from src.services.audit_frontend_service import audit_frontend_service
from src.core.permissions import AuditPermission, has_audit_permission
from src.templates import templates

router = APIRouter(prefix="/admin/audit-logs", tags=["audit-frontend"])


@router.get("", response_class=HTMLResponse)
async def audit_logs_page(
    request: Request,
    table_name: Optional[str] = None,
    record_id: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    """Main audit logs page with filtering."""
    # Check user has some audit permission
    user_permissions = audit_frontend_service.get_available_tables(current_user)
    if not user_permissions and current_user.role != "admin":
        return templates.TemplateResponse(
            "errors/403.html",
            {"request": request, "message": "You don't have permission to view audit logs"},
            status_code=403
        )
    
    # Get filtered logs
    result = audit_frontend_service.get_audit_logs(
        db=db,
        current_user=current_user,
        table_name=table_name,
        record_id=record_id,
        action=action,
        date_from=date_from,
        date_to=date_to,
        search=search,
        page=page,
    )
    
    # Get filter options
    available_tables = audit_frontend_service.get_available_tables(current_user)
    action_types = audit_frontend_service.get_action_types()
    stats = audit_frontend_service.get_stats(db, current_user)
    
    # Check export permission
    can_export = has_audit_permission(current_user.role, AuditPermission.EXPORT)
    
    return templates.TemplateResponse(
        "admin/audit_logs.html",
        {
            "request": request,
            "current_user": current_user,
            "page_title": "Audit Logs",
            "logs": result["items"],
            "total": result["total"],
            "page": result["page"],
            "pages": result["pages"],
            "per_page": result["per_page"],
            # Filters
            "available_tables": available_tables,
            "action_types": action_types,
            "selected_table": table_name,
            "selected_action": action,
            "selected_date_from": date_from,
            "selected_date_to": date_to,
            "search_query": search,
            # Stats
            "stats": stats,
            # Permissions
            "can_export": can_export,
        }
    )


@router.get("/search", response_class=HTMLResponse)
async def audit_logs_search(
    request: Request,
    table_name: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    """HTMX endpoint for filtered audit log table."""
    result = audit_frontend_service.get_audit_logs(
        db=db,
        current_user=current_user,
        table_name=table_name,
        action=action,
        date_from=date_from,
        date_to=date_to,
        search=search,
        page=page,
    )
    
    return templates.TemplateResponse(
        "admin/partials/_audit_table.html",
        {
            "request": request,
            "logs": result["items"],
            "total": result["total"],
            "page": result["page"],
            "pages": result["pages"],
        }
    )


@router.get("/detail/{log_id}", response_class=HTMLResponse)
async def audit_log_detail(
    request: Request,
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    """View details of a single audit log entry."""
    from src.models.audit_log import AuditLog
    
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Audit log not found"},
            status_code=404
        )
    
    # Format with redaction
    formatted = audit_frontend_service._format_log(log, current_user.role)
    
    return templates.TemplateResponse(
        "admin/audit_detail.html",
        {
            "request": request,
            "current_user": current_user,
            "page_title": f"Audit Log #{log_id}",
            "log": formatted,
        }
    )


@router.get("/export")
async def export_audit_logs(
    table_name: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    """Export audit logs to CSV (admin only)."""
    if not has_audit_permission(current_user.role, AuditPermission.EXPORT):
        raise HTTPException(status_code=403, detail="Export not permitted")
    
    # Get all matching logs (no pagination for export)
    result = audit_frontend_service.get_audit_logs(
        db=db,
        current_user=current_user,
        table_name=table_name,
        action=action,
        date_from=date_from,
        date_to=date_to,
        page=1,
        per_page=10000,  # Large limit for export
    )
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "ID", "Table", "Record ID", "Action", "Changed By", 
        "Changed At", "Notes", "Old Values", "New Values"
    ])
    
    # Data rows
    for log in result["items"]:
        writer.writerow([
            log["id"],
            log["table_name"],
            log["record_id"],
            log["action"],
            log["changed_by"],
            log["changed_at"],
            log["notes"],
            str(log["old_values"]),
            str(log["new_values"]),
        ])
    
    output.seek(0)
    
    filename = f"audit_logs_{date.today().isoformat()}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/entity/{table_name}/{record_id}", response_class=HTMLResponse)
async def entity_audit_history(
    request: Request,
    table_name: str,
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie),
):
    """HTMX endpoint for inline entity history."""
    logs = audit_frontend_service.get_entity_history(
        db=db,
        current_user=current_user,
        table_name=table_name,
        record_id=record_id,
        limit=10,
    )
    
    return templates.TemplateResponse(
        "components/_audit_history.html",
        {
            "request": request,
            "logs": logs,
            "table_name": table_name,
            "record_id": record_id,
        }
    )
```

#### 3.2 Register Router

**File:** `src/main.py`

```python
from src.routers.audit_frontend import router as audit_frontend_router

# ... in router registration section ...
app.include_router(audit_frontend_router)
```

---

### Task 4: Create Audit Log Templates (45 min)

#### 4.1 Main Audit Logs Page

**File:** `src/templates/admin/audit_logs.html`

```html
{% extends "base_auth.html" %}

{% block title %}Audit Logs - Admin{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
        <div>
            <h1 class="text-2xl font-bold">Audit Logs</h1>
            <p class="text-gray-600">View system activity and change history</p>
        </div>
        {% if can_export %}
        <a href="/admin/audit-logs/export?table_name={{ selected_table or '' }}&action={{ selected_action or '' }}&date_from={{ selected_date_from or '' }}&date_to={{ selected_date_to or '' }}" 
           class="btn btn-outline btn-primary">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export CSV
        </a>
        {% endif %}
    </div>

    <!-- Stats Cards -->
    <div class="stats stats-vertical lg:stats-horizontal shadow w-full">
        <div class="stat">
            <div class="stat-title">Total Logs</div>
            <div class="stat-value">{{ "{:,}".format(stats.total_logs) }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">This Week</div>
            <div class="stat-value text-primary">{{ "{:,}".format(stats.logs_this_week) }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Today</div>
            <div class="stat-value text-secondary">{{ "{:,}".format(stats.logs_today) }}</div>
        </div>
    </div>

    <!-- Filters -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title text-lg">Filters</h2>
            <form class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
                  hx-get="/admin/audit-logs/search"
                  hx-target="#audit-table-container"
                  hx-trigger="change, input delay:300ms from:input[name='search']">
                
                <!-- Table Filter -->
                <div class="form-control">
                    <label class="label"><span class="label-text">Table</span></label>
                    <select name="table_name" class="select select-bordered">
                        <option value="">All Tables</option>
                        {% for table in available_tables %}
                        <option value="{{ table }}" {% if table == selected_table %}selected{% endif %}>
                            {{ table }}
                        </option>
                        {% endfor %}
                    </select>
                </div>

                <!-- Action Filter -->
                <div class="form-control">
                    <label class="label"><span class="label-text">Action</span></label>
                    <select name="action" class="select select-bordered">
                        <option value="">All Actions</option>
                        {% for action in action_types %}
                        <option value="{{ action }}" {% if action == selected_action %}selected{% endif %}>
                            {{ action }}
                        </option>
                        {% endfor %}
                    </select>
                </div>

                <!-- Date From -->
                <div class="form-control">
                    <label class="label"><span class="label-text">From Date</span></label>
                    <input type="date" name="date_from" class="input input-bordered"
                           value="{{ selected_date_from or '' }}">
                </div>

                <!-- Date To -->
                <div class="form-control">
                    <label class="label"><span class="label-text">To Date</span></label>
                    <input type="date" name="date_to" class="input input-bordered"
                           value="{{ selected_date_to or '' }}">
                </div>

                <!-- Search -->
                <div class="form-control md:col-span-2">
                    <label class="label"><span class="label-text">Search</span></label>
                    <input type="text" name="search" placeholder="Search by user, table, or notes..."
                           class="input input-bordered" value="{{ search_query or '' }}">
                </div>

                <!-- Clear Button -->
                <div class="form-control justify-end">
                    <a href="/admin/audit-logs" class="btn btn-ghost">Clear Filters</a>
                </div>
            </form>
        </div>
    </div>

    <!-- Audit Log Table -->
    <div id="audit-table-container">
        {% include "admin/partials/_audit_table.html" %}
    </div>
</div>
{% endblock %}
```

#### 4.2 Audit Table Partial

**File:** `src/templates/admin/partials/_audit_table.html`

```html
<div class="card bg-base-100 shadow">
    <div class="card-body">
        <div class="flex justify-between items-center mb-4">
            <span class="text-sm text-gray-600">
                Showing {{ logs|length }} of {{ "{:,}".format(total) }} logs
            </span>
        </div>

        <div class="overflow-x-auto">
            <table class="table table-zebra">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Table</th>
                        <th>Record</th>
                        <th>Action</th>
                        <th>Changed By</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in logs %}
                    <tr>
                        <td class="text-sm">
                            {{ log.changed_at[:19].replace('T', ' ') if log.changed_at else 'N/A' }}
                        </td>
                        <td>
                            <span class="badge badge-ghost">{{ log.table_name }}</span>
                        </td>
                        <td class="font-mono text-sm">{{ log.record_id }}</td>
                        <td>
                            {% if log.action == 'CREATE' %}
                            <span class="badge badge-success">{{ log.action }}</span>
                            {% elif log.action == 'UPDATE' %}
                            <span class="badge badge-warning">{{ log.action }}</span>
                            {% elif log.action == 'DELETE' %}
                            <span class="badge badge-error">{{ log.action }}</span>
                            {% elif log.action == 'READ' %}
                            <span class="badge badge-info">{{ log.action }}</span>
                            {% else %}
                            <span class="badge">{{ log.action }}</span>
                            {% endif %}
                        </td>
                        <td>{{ log.changed_by or 'System' }}</td>
                        <td>
                            <a href="/admin/audit-logs/detail/{{ log.id }}" 
                               class="btn btn-xs btn-ghost">
                                View
                            </a>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6" class="text-center text-gray-500 py-8">
                            No audit logs found matching your criteria
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        {% if pages > 1 %}
        <div class="flex justify-center mt-4">
            <div class="join">
                {% if page > 1 %}
                <button class="join-item btn btn-sm"
                        hx-get="/admin/audit-logs/search?page={{ page - 1 }}"
                        hx-target="#audit-table-container"
                        hx-include="form">
                    «
                </button>
                {% endif %}
                
                <button class="join-item btn btn-sm btn-active">
                    Page {{ page }} of {{ pages }}
                </button>
                
                {% if page < pages %}
                <button class="join-item btn btn-sm"
                        hx-get="/admin/audit-logs/search?page={{ page + 1 }}"
                        hx-target="#audit-table-container"
                        hx-include="form">
                    »
                </button>
                {% endif %}
            </div>
        </div>
        {% endif %}
    </div>
</div>
```

#### 4.3 Audit Detail Page

**File:** `src/templates/admin/audit_detail.html`

```html
{% extends "base_auth.html" %}

{% block title %}{{ page_title }} - Admin{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/admin/audit-logs">Audit Logs</a></li>
            <li>Log #{{ log.id }}</li>
        </ul>
    </div>

    <!-- Header -->
    <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold">Audit Log #{{ log.id }}</h1>
        <a href="/admin/audit-logs" class="btn btn-ghost">← Back to Logs</a>
    </div>

    <!-- Summary Card -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Summary</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                    <div class="text-sm text-gray-500">Table</div>
                    <div class="font-medium">{{ log.table_name }}</div>
                </div>
                <div>
                    <div class="text-sm text-gray-500">Record ID</div>
                    <div class="font-mono">{{ log.record_id }}</div>
                </div>
                <div>
                    <div class="text-sm text-gray-500">Action</div>
                    <div>
                        {% if log.action == 'CREATE' %}
                        <span class="badge badge-success badge-lg">{{ log.action }}</span>
                        {% elif log.action == 'UPDATE' %}
                        <span class="badge badge-warning badge-lg">{{ log.action }}</span>
                        {% elif log.action == 'DELETE' %}
                        <span class="badge badge-error badge-lg">{{ log.action }}</span>
                        {% else %}
                        <span class="badge badge-lg">{{ log.action }}</span>
                        {% endif %}
                    </div>
                </div>
                <div>
                    <div class="text-sm text-gray-500">Changed By</div>
                    <div class="font-medium">{{ log.changed_by or 'System' }}</div>
                </div>
                <div>
                    <div class="text-sm text-gray-500">Timestamp</div>
                    <div>{{ log.changed_at[:19].replace('T', ' ') if log.changed_at else 'N/A' }}</div>
                </div>
                {% if log.ip_address %}
                <div>
                    <div class="text-sm text-gray-500">IP Address</div>
                    <div class="font-mono text-sm">{{ log.ip_address }}</div>
                </div>
                {% endif %}
                {% if log.notes %}
                <div class="col-span-2">
                    <div class="text-sm text-gray-500">Notes</div>
                    <div>{{ log.notes }}</div>
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    <!-- Values Comparison -->
    {% if log.action == 'UPDATE' %}
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Old Values -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title text-error">Before (Old Values)</h2>
                <pre class="bg-base-200 p-4 rounded-lg overflow-x-auto text-sm">{{ log.old_values | tojson(indent=2) if log.old_values else 'N/A' }}</pre>
            </div>
        </div>

        <!-- New Values -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title text-success">After (New Values)</h2>
                <pre class="bg-base-200 p-4 rounded-lg overflow-x-auto text-sm">{{ log.new_values | tojson(indent=2) if log.new_values else 'N/A' }}</pre>
            </div>
        </div>
    </div>
    {% elif log.action == 'CREATE' %}
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title text-success">Created Values</h2>
            <pre class="bg-base-200 p-4 rounded-lg overflow-x-auto text-sm">{{ log.new_values | tojson(indent=2) if log.new_values else 'N/A' }}</pre>
        </div>
    </div>
    {% elif log.action == 'DELETE' %}
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title text-error">Deleted Values</h2>
            <pre class="bg-base-200 p-4 rounded-lg overflow-x-auto text-sm">{{ log.old_values | tojson(indent=2) if log.old_values else 'N/A' }}</pre>
        </div>
    </div>
    {% endif %}

    <!-- Changed Fields -->
    {% if log.changed_fields %}
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Changed Fields</h2>
            <div class="flex flex-wrap gap-2">
                {% for field in log.changed_fields %}
                <span class="badge badge-outline">{{ field }}</span>
                {% endfor %}
            </div>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}
```

---

### Task 5: Add Sidebar Navigation (10 min)

**File:** `src/templates/components/_sidebar.html`

Add under Admin section:
```html
<!-- Admin Section -->
{% if current_user.role in ['admin', 'officer'] %}
<li>
    <details>
        <summary>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Admin
        </summary>
        <ul>
            <li><a href="/admin/audit-logs">Audit Logs</a></li>
        </ul>
    </details>
</li>
{% endif %}
```

---

### Task 6: Write Tests (30 min)

**File:** `src/tests/test_audit_frontend.py`

```python
"""Tests for audit frontend functionality."""
import pytest
from datetime import date, timedelta
from src.services.audit_frontend_service import audit_frontend_service
from src.core.permissions import (
    AuditPermission, 
    has_audit_permission, 
    redact_sensitive_fields,
    get_audit_permissions,
)


class TestAuditPermissions:
    """Tests for audit permission system."""

    def test_admin_has_all_permissions(self):
        """Admin should have VIEW_ALL and EXPORT."""
        perms = get_audit_permissions("admin")
        assert AuditPermission.VIEW_ALL in perms
        assert AuditPermission.EXPORT in perms

    def test_staff_has_view_own_only(self):
        """Staff should only have VIEW_OWN."""
        perms = get_audit_permissions("staff")
        assert AuditPermission.VIEW_OWN in perms
        assert AuditPermission.VIEW_ALL not in perms
        assert AuditPermission.EXPORT not in perms

    def test_officer_has_member_and_user_view(self):
        """Officer should have VIEW_MEMBERS and VIEW_USERS."""
        perms = get_audit_permissions("officer")
        assert AuditPermission.VIEW_MEMBERS in perms
        assert AuditPermission.VIEW_USERS in perms

    def test_member_has_no_permissions(self):
        """Regular members should have no audit access."""
        perms = get_audit_permissions("member")
        assert len(perms) == 0


class TestSensitiveFieldRedaction:
    """Tests for field redaction."""

    def test_admin_sees_all_fields(self):
        """Admin should see sensitive fields unredacted."""
        data = {"name": "John", "ssn": "123-45-6789"}
        result = redact_sensitive_fields(data, "admin")
        assert result["ssn"] == "123-45-6789"

    def test_staff_sees_redacted_ssn(self):
        """Non-admin should see SSN redacted."""
        data = {"name": "John", "ssn": "123-45-6789"}
        result = redact_sensitive_fields(data, "staff")
        assert result["name"] == "John"
        assert result["ssn"] == "[REDACTED]"

    def test_multiple_sensitive_fields(self):
        """Multiple sensitive fields should all be redacted."""
        data = {
            "name": "John",
            "ssn": "123-45-6789",
            "bank_account": "9876543210",
            "password_hash": "abc123",
        }
        result = redact_sensitive_fields(data, "officer")
        assert result["name"] == "John"
        assert result["ssn"] == "[REDACTED]"
        assert result["bank_account"] == "[REDACTED]"
        assert result["password_hash"] == "[REDACTED]"

    def test_none_input_returns_none(self):
        """None input should return None."""
        result = redact_sensitive_fields(None, "staff")
        assert result is None


class TestAuditFrontendService:
    """Tests for AuditFrontendService."""

    def test_admin_sees_all_tables(self, db_session, admin_user):
        """Admin should see all available tables."""
        tables = audit_frontend_service.get_available_tables(admin_user)
        assert "members" in tables
        assert "users" in tables

    def test_staff_sees_limited_tables(self, db_session, staff_user):
        """Staff should see limited table list."""
        tables = audit_frontend_service.get_available_tables(staff_user)
        # Staff with VIEW_OWN only doesn't get table list (only their own logs)
        # This depends on implementation - adjust assertion as needed
        assert isinstance(tables, list)

    def test_get_action_types(self):
        """Should return all action types."""
        actions = audit_frontend_service.get_action_types()
        assert "CREATE" in actions
        assert "READ" in actions
        assert "UPDATE" in actions
        assert "DELETE" in actions


class TestAuditFrontendAPI:
    """Tests for audit frontend API endpoints."""

    def test_audit_page_requires_auth(self, client):
        """Audit logs page requires authentication."""
        response = client.get("/admin/audit-logs")
        assert response.status_code in [401, 302]

    def test_admin_can_access_audit_page(self, client, admin_auth_cookies):
        """Admin can access audit logs page."""
        response = client.get("/admin/audit-logs", cookies=admin_auth_cookies)
        assert response.status_code == 200
        assert b"Audit Logs" in response.content

    def test_export_requires_permission(self, client, staff_auth_cookies):
        """Export requires EXPORT permission."""
        response = client.get("/admin/audit-logs/export", cookies=staff_auth_cookies)
        assert response.status_code == 403

    def test_admin_can_export(self, client, admin_auth_cookies):
        """Admin can export audit logs."""
        response = client.get("/admin/audit-logs/export", cookies=admin_auth_cookies)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
```

---

## Acceptance Criteria

- [ ] AuditPermission enum defined with VIEW_OWN, VIEW_MEMBERS, VIEW_USERS, VIEW_ALL, EXPORT
- [ ] Role-to-permission mapping implemented
- [ ] Sensitive field redaction working for non-admin users
- [ ] AuditFrontendService with role-based query filtering
- [ ] Audit logs list page at /admin/audit-logs
- [ ] HTMX filtering by table, action, date range, search
- [ ] Audit detail page showing before/after values
- [ ] Export to CSV (admin only)
- [ ] Sidebar navigation includes Audit Logs link
- [ ] All tests pass (~15 new tests)

---

## Files Created

```
src/core/permissions.py
src/services/audit_frontend_service.py
src/routers/audit_frontend.py
src/templates/admin/audit_logs.html
src/templates/admin/audit_detail.html
src/templates/admin/partials/_audit_table.html
src/tests/test_audit_frontend.py
```

## Files Modified

```
src/main.py                              # Register audit_frontend router
src/templates/components/_sidebar.html   # Add Admin > Audit Logs nav
```

---

## Next Session Preview

**Week 11 Session C: Inline History & Member Notes UI** will add:
- Reusable `_audit_history.html` partial
- "Recent Activity" section on member detail page
- Notes section on member detail page
- Add note modal with visibility selector

---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** 

### Before Ending This Session:

Scan all documentation in `/app/*`. Update *ANY* & *ALL* relevant documentation as necessary with current progress for the historical record. Do not forget to update ADRs, Roadmap, Checklist, again only if necessary.

**Documentation Checklist:**

| Document | Updated? | Notes |
|----------|----------|-------|
| CLAUDE.md | [ ] | Update Week 11 Session B status |
| CHANGELOG.md | [ ] | Add audit UI entry |
| CONTINUITY.md | [ ] | Update current status |
| IP2A_MILESTONE_CHECKLIST.md | [ ] | Mark 11.2, 11.3 complete |
| IP2A_BACKEND_ROADMAP.md | [ ] | Update Week 11 progress |
| ADR-012 (Audit Logging) | [ ] | Mark UI implementation complete |
| Session log created | [ ] | `docs/reports/session-logs/` |

This ensures historical record-keeping and project continuity ("bus factor" protection).

---

*End of instruction document*
