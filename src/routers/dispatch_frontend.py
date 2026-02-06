"""
Dispatch Frontend Router - Staff-facing UI for dispatch operations.

Created: February 4, 2026 (Week 27)
Phase 7 - Referral & Dispatch System

Provides HTML pages for the daily dispatch workflow:
- Dashboard with live stats
- Labor request management
- Morning referral processing
- Active dispatches tracking
- Queue management
- Enforcement monitoring
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.routers.dependencies.auth_cookie import require_auth
from src.services.dispatch_frontend_service import DispatchFrontendService
from src.services.referral_frontend_service import ReferralFrontendService
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="src/templates")

router = APIRouter(tags=["Dispatch Frontend"])


def get_template_context(request: Request, current_user=None, **kwargs):
    """Get base template context."""
    context = {
        "request": request,
        "current_user": current_user,
    }
    context.update(kwargs)
    return context


# --- Dispatch Routes ---


@router.get("/dispatch", response_class=HTMLResponse)
async def dispatch_dashboard(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Dispatch operations dashboard."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    stats = service.get_dashboard_stats()
    time_context = service.get_time_context()
    pending_requests = service.get_requests(filters={"status": "open"}, per_page=5)

    context = get_template_context(
        request,
        current_user=current_user,
        stats=stats,
        time_context=time_context,
        pending_requests=pending_requests["items"],
        request_status_badge=service.request_status_badge,
    )

    return templates.TemplateResponse("dispatch/dashboard.html", context)


@router.get("/dispatch/requests", response_class=HTMLResponse)
async def dispatch_requests(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    book_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
):
    """Labor request list with filtering."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)

    filters = {
        "status": status,
        "book_id": book_id,
        "search": search,
    }

    requests_data = service.get_requests(filters=filters, page=page)

    context = get_template_context(
        request,
        current_user=current_user,
        labor_requests=requests_data["items"],
        pagination=requests_data,
        filters=filters,
        request_status_badge=service.request_status_badge,
    )

    # If HTMX request, return partial
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/dispatch/_request_table.html", context
        )

    return templates.TemplateResponse("dispatch/requests.html", context)


@router.get("/dispatch/requests/{request_id}", response_class=HTMLResponse)
async def dispatch_request_detail(
    request_id: int,
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Single labor request detail with candidates and bids."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    labor_request = service.get_request_detail(request_id)

    if not labor_request:
        raise HTTPException(status_code=404, detail="Labor request not found")

    context = get_template_context(
        request,
        current_user=current_user,
        labor_request=labor_request["request"],
        candidates=labor_request["candidates"],
        bids=labor_request["bids"],
        dispatches=labor_request["dispatches"],
        time_context=service.get_time_context(),
        request_status_badge=service.request_status_badge,
        bid_status_badge=service.bid_status_badge,
    )

    return templates.TemplateResponse("dispatch/request_detail.html", context)


@router.get("/dispatch/morning-referral", response_class=HTMLResponse)
async def morning_referral(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Morning referral processing page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    time_context = service.get_time_context()
    pending_bids = service.get_pending_bids()

    context = get_template_context(
        request,
        current_user=current_user,
        time_context=time_context,
        pending_bids=pending_bids,
        bid_status_badge=service.bid_status_badge,
    )

    return templates.TemplateResponse("dispatch/morning_referral.html", context)


@router.get("/dispatch/active", response_class=HTMLResponse)
async def active_dispatches(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
):
    """Active dispatches list."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    filters = {"status": status, "search": search}
    dispatches_data = service.get_active_dispatches(filters=filters, page=page)

    context = get_template_context(
        request,
        current_user=current_user,
        dispatches=dispatches_data["items"],
        pagination=dispatches_data,
        filters=filters,
        dispatch_status_badge=service.dispatch_status_badge,
    )

    # If HTMX request, return partial
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/dispatch/_dispatch_table.html", context
        )

    return templates.TemplateResponse("dispatch/active.html", context)


@router.get("/dispatch/queue", response_class=HTMLResponse)
async def dispatch_queue(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
    book_id: Optional[int] = None,
):
    """Queue management page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    ref_service = ReferralFrontendService(db)

    books = ref_service.get_books_overview()
    queue = service.get_queue(book_id=book_id)

    context = get_template_context(
        request,
        current_user=current_user,
        books=books,
        queue=queue,
        default_book_id=book_id or (books[0]["id"] if books else None),
    )

    # If HTMX request, return partial
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/dispatch/_queue_table.html", context
        )

    return templates.TemplateResponse("dispatch/queue.html", context)


@router.get("/dispatch/enforcement", response_class=HTMLResponse)
async def enforcement_dashboard(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Enforcement dashboard."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    enforcement = service.get_enforcement_summary()
    suspensions = service.get_suspensions()

    context = get_template_context(
        request,
        current_user=current_user,
        enforcement=enforcement,
        suspensions=suspensions,
    )

    return templates.TemplateResponse("dispatch/enforcement.html", context)


# --- HTMX Partials ---


@router.get("/dispatch/partials/stats")
async def dispatch_stats_partial(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """HTMX partial: dashboard stats."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    stats = service.get_dashboard_stats()

    context = get_template_context(request, current_user=current_user, stats=stats)

    return templates.TemplateResponse("partials/dispatch/_stats_cards.html", context)


@router.get("/dispatch/partials/activity-feed")
async def dispatch_activity_partial(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """HTMX partial: today's activity feed. Auto-refreshes every 30s."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    activity = service.get_todays_activity()

    context = get_template_context(
        request, current_user=current_user, activity=activity
    )

    return templates.TemplateResponse("partials/dispatch/_activity_feed.html", context)


@router.get("/dispatch/partials/pending-requests")
async def pending_requests_partial(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """HTMX partial: pending requests cards."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    pending_requests = service.get_requests(filters={"status": "open"}, per_page=10)

    context = get_template_context(
        request,
        current_user=current_user,
        pending_requests=pending_requests["items"],
        request_status_badge=service.request_status_badge,
    )

    return templates.TemplateResponse(
        "partials/dispatch/_pending_requests.html", context
    )


@router.get("/dispatch/partials/bid-queue")
async def bid_queue_partial(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """HTMX partial: morning referral bid queue."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    bids = service.get_pending_bids()

    context = get_template_context(
        request,
        current_user=current_user,
        bids=bids,
        bid_status_badge=service.bid_status_badge,
    )

    return templates.TemplateResponse("partials/dispatch/_bid_queue.html", context)


@router.get("/dispatch/partials/queue-table")
async def queue_table_partial(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
    book_id: Optional[int] = None,
):
    """HTMX partial: queue table for specific book."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    queue = service.get_queue(book_id=book_id)

    context = get_template_context(request, current_user=current_user, queue=queue)

    return templates.TemplateResponse("partials/dispatch/_queue_table.html", context)


# --- Exemption Routes (Week 32) ---


@router.get("/dispatch/exemptions", response_class=HTMLResponse)
async def dispatch_exemptions(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
    exempt_reason: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
):
    """List all exemptions with search/filter."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    stats = service.get_exemption_stats()
    filters = {
        "exempt_reason": exempt_reason,
        "search": search,
        "status": status,
    }
    exemptions_data = service.get_exemptions(filters=filters, page=page)

    context = get_template_context(
        request,
        current_user=current_user,
        stats=stats,
        exemptions=exemptions_data["items"],
        pagination=exemptions_data,
        filters=filters,
        format_exemption_badge=service.format_exemption_badge,
    )

    # If HTMX request, return partial
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "dispatch/partials/_exemptions_table.html", context
        )

    return templates.TemplateResponse("dispatch/exemptions.html", context)


@router.get("/dispatch/exemptions/{registration_id}", response_class=HTMLResponse)
async def dispatch_exemption_detail(
    registration_id: int,
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Single exemption detail with edit form."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    exemption = service.get_exemption_detail(registration_id)

    if not exemption:
        raise HTTPException(status_code=404, detail="Exemption not found")

    context = get_template_context(
        request,
        current_user=current_user,
        exemption=exemption,
        format_exemption_badge=service.format_exemption_badge,
    )

    return templates.TemplateResponse("dispatch/exemption_detail.html", context)


@router.post("/dispatch/exemptions/create", response_class=HTMLResponse)
async def dispatch_exemption_create(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Create new exemption — Staff+ only."""
    from datetime import date
    from src.db.enums import ExemptReason
    from src.models.book_registration import BookRegistration
    from src.services.audit_service import audit_service

    if isinstance(current_user, RedirectResponse):
        return current_user

    # Check role - require staff or higher
    user_roles = [r.lower() for r in (current_user.get("roles") or [])]
    if not any(r in user_roles for r in ["admin", "officer", "staff"]):
        raise HTTPException(status_code=403, detail="Staff access required")

    # Get form data
    form = await request.form()
    registration_id = int(form.get("registration_id"))
    exempt_reason = form.get("exempt_reason")
    start_date_str = form.get("start_date")
    end_date_str = form.get("end_date")
    notes = form.get("notes")

    # Find registration
    registration = (
        db.query(BookRegistration)
        .filter(BookRegistration.id == registration_id)
        .first()
    )

    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Update exemption fields
    registration.is_exempt = True
    registration.exempt_reason = ExemptReason(exempt_reason) if exempt_reason else None
    registration.exempt_start_date = (
        date.fromisoformat(start_date_str) if start_date_str else date.today()
    )
    registration.exempt_end_date = (
        date.fromisoformat(end_date_str) if end_date_str else None
    )
    if notes:
        registration.notes = notes

    db.commit()

    # Audit log
    audit_service.log_create(
        db=db,
        table_name="book_registrations",
        record_id=registration.id,
        new_values={
            "is_exempt": True,
            "exempt_reason": exempt_reason,
            "exempt_start_date": str(registration.exempt_start_date),
            "exempt_end_date": str(registration.exempt_end_date)
            if registration.exempt_end_date
            else None,
        },
        user_id=current_user.get("id"),
    )

    return RedirectResponse(
        url=f"/dispatch/exemptions/{registration.id}", status_code=303
    )


@router.post(
    "/dispatch/exemptions/{registration_id}/deactivate", response_class=HTMLResponse
)
async def dispatch_exemption_deactivate(
    registration_id: int,
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Deactivate (soft-end) an exemption — Staff+ only."""
    from datetime import date
    from src.models.book_registration import BookRegistration
    from src.services.audit_service import audit_service

    if isinstance(current_user, RedirectResponse):
        return current_user

    # Check role - require staff or higher
    user_roles = [r.lower() for r in (current_user.get("roles") or [])]
    if not any(r in user_roles for r in ["admin", "officer", "staff"]):
        raise HTTPException(status_code=403, detail="Staff access required")

    # Find registration
    registration = (
        db.query(BookRegistration)
        .filter(
            BookRegistration.id == registration_id,
            BookRegistration.is_exempt.is_(True),
        )
        .first()
    )

    if not registration:
        raise HTTPException(status_code=404, detail="Exemption not found")

    # Deactivate by setting end date to today and is_exempt to False
    old_values = {
        "is_exempt": registration.is_exempt,
        "exempt_end_date": str(registration.exempt_end_date)
        if registration.exempt_end_date
        else None,
    }

    registration.is_exempt = False
    registration.exempt_end_date = date.today()

    db.commit()

    # Audit log
    audit_service.log_update(
        db=db,
        table_name="book_registrations",
        record_id=registration.id,
        old_values=old_values,
        new_values={
            "is_exempt": False,
            "exempt_end_date": str(registration.exempt_end_date),
        },
        user_id=current_user.get("id"),
    )

    # Return updated partial or redirect
    if request.headers.get("HX-Request"):
        context = get_template_context(
            request,
            current_user=current_user,
            message="Exemption deactivated successfully",
        )
        return templates.TemplateResponse(
            "dispatch/partials/_exemption_deactivated.html", context
        )

    return RedirectResponse(url="/dispatch/exemptions", status_code=303)


# --- Reports Navigation (Week 32) ---


@router.get("/dispatch/reports", response_class=HTMLResponse)
async def dispatch_reports(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Reports navigation dashboard."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    categories = service.get_report_categories()

    # Calculate totals
    total_reports = sum(c["total"] for c in categories)
    available_reports = sum(c["available_count"] for c in categories)

    context = get_template_context(
        request,
        current_user=current_user,
        categories=categories,
        total_reports=total_reports,
        available_reports=available_reports,
    )

    return templates.TemplateResponse("dispatch/reports_landing.html", context)


# --- Check Mark Routes (Week 32) ---


@router.get("/dispatch/checkmarks/{member_id}/history", response_class=HTMLResponse)
async def dispatch_checkmark_history(
    member_id: int,
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """HTMX partial: check mark history for a specific member."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DispatchFrontendService(db)
    summary = service.get_member_checkmark_summary(member_id)

    context = get_template_context(
        request,
        current_user=current_user,
        member_id=member_id,
        checkmark_summary=summary,
    )

    return templates.TemplateResponse(
        "dispatch/partials/_checkmark_history.html", context
    )


@router.post("/dispatch/checkmarks/record", response_class=HTMLResponse)
async def dispatch_checkmark_record(
    request: Request,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Staff+ action: record a new check mark."""
    from datetime import datetime
    from src.models.book_registration import BookRegistration
    from src.services.audit_service import audit_service

    if isinstance(current_user, RedirectResponse):
        return current_user

    # Check role - require staff or higher
    user_roles = [r.lower() for r in (current_user.get("roles") or [])]
    if not any(r in user_roles for r in ["admin", "officer", "staff"]):
        raise HTTPException(status_code=403, detail="Staff access required")

    # Get form data
    form = await request.form()
    registration_id = int(form.get("registration_id"))
    reason = form.get("reason")
    dispatch_id = form.get("dispatch_id")

    # Find registration
    registration = (
        db.query(BookRegistration)
        .filter(BookRegistration.id == registration_id)
        .first()
    )

    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Validate - don't allow 4th check mark
    if registration.check_marks >= 3:
        raise HTTPException(
            status_code=400, detail="Member has already been rolled off (3 check marks)"
        )

    # Record check mark
    old_count = registration.check_marks
    registration.check_marks += 1
    registration.last_check_mark_date = datetime.now().date()
    registration.last_check_mark_at = datetime.now()

    # If 3rd check mark, roll off
    if registration.check_marks >= 3:
        from src.db.enums import RegistrationStatus, RolloffReason

        registration.status = RegistrationStatus.ROLLED_OFF
        registration.roll_off_reason = RolloffReason.CHECK_MARKS
        registration.roll_off_date = datetime.now()

    db.commit()

    # Audit log
    audit_service.log_update(
        db=db,
        table_name="book_registrations",
        record_id=registration.id,
        old_values={"check_marks": old_count},
        new_values={
            "check_marks": registration.check_marks,
            "reason": reason,
            "dispatch_id": dispatch_id,
        },
        user_id=current_user.get("id"),
    )

    # Return updated partial
    if request.headers.get("HX-Request"):
        service = DispatchFrontendService(db)
        summary = service.get_member_checkmark_summary(registration.member_id)
        context = get_template_context(
            request,
            current_user=current_user,
            member_id=registration.member_id,
            checkmark_summary=summary,
            message=f"Check mark recorded. Member now has {registration.check_marks} check marks.",
        )
        return templates.TemplateResponse(
            "dispatch/partials/_checkmark_history.html", context
        )

    return RedirectResponse(url="/dispatch/enforcement", status_code=303)
