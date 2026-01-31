"""Frontend routes for audit log viewing."""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import csv
import io

from src.db.session import get_db
from src.models.user import User
from src.routers.dependencies.auth_cookie import get_current_user_model
from src.services.audit_frontend_service import audit_frontend_service
from src.core.permissions import AuditPermission, has_audit_permission

templates = Jinja2Templates(directory="src/templates")

router = APIRouter(prefix="/admin/audit-logs", tags=["audit-frontend"])


@router.get("", response_class=HTMLResponse)
def audit_logs_page(
    request: Request,
    table_name: Optional[str] = None,
    record_id: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_model),
):
    """Main audit logs page with filtering."""
    # Check user has some audit permission
    user_permissions = audit_frontend_service.get_available_tables(current_user)
    primary_role = audit_frontend_service._get_primary_role(current_user)

    if not user_permissions and primary_role != "admin":
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
    can_export = has_audit_permission(primary_role, AuditPermission.EXPORT)

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
def audit_logs_search(
    request: Request,
    table_name: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_model),
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
def audit_log_detail(
    request: Request,
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_model),
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
    primary_role = audit_frontend_service._get_primary_role(current_user)
    formatted = audit_frontend_service._format_log(log, primary_role)

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
def export_audit_logs(
    table_name: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_model),
):
    """Export audit logs to CSV (admin only)."""
    primary_role = audit_frontend_service._get_primary_role(current_user)

    if not has_audit_permission(primary_role, AuditPermission.EXPORT):
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
def entity_audit_history(
    request: Request,
    table_name: str,
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_model),
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
