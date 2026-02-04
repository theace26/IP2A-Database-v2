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
from src.routers.dependencies.auth_cookie import require_auth, get_current_user_model
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

    context = get_template_context(request, current_user=current_user, activity=activity)

    return templates.TemplateResponse(
        "partials/dispatch/_activity_feed.html", context
    )


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
