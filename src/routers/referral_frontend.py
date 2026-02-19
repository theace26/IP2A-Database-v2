"""
Frontend routes for referral book and registration management.

Created: February 4, 2026 (Week 26)
Phase 7 - Referral & Dispatch System
"""

from typing import Optional

from fastapi import APIRouter, Depends, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.routers.dependencies.auth_cookie import require_auth
from src.services.referral_frontend_service import ReferralFrontendService

router = APIRouter(prefix="/referral", tags=["referral-frontend"])

templates = Jinja2Templates(directory="src/templates")


# ============================================================================
# Main Pages
# ============================================================================


@router.get("", response_class=HTMLResponse)
async def referral_landing(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Referral & Dispatch overview page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = ReferralFrontendService(db)
    stats = service.get_landing_stats()

    return templates.TemplateResponse(
        "referral/landing.html",
        {
            "request": request,
            "current_user": current_user,
            "stats": stats,
        },
    )


@router.get("/books", response_class=HTMLResponse)
async def books_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
    sort: str = Query("name"),
    order: str = Query("asc"),
):
    """All referral books list."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Validate sort/order
    allowed_sort_columns = [
        "name",
        "classification",
        "region",
        "book_number",
        "active_count",
        "dispatched_count",
        "is_active",
    ]
    if sort not in allowed_sort_columns:
        sort = "name"
    if order not in ("asc", "desc"):
        order = "asc"

    service = ReferralFrontendService(db)
    books = service.get_books_overview(sort=sort, order=order)

    # HTMX request — return partial only
    if (
        request.headers.get("HX-Request")
        and request.headers.get("HX-Target") == "books-table-container"
    ):
        return templates.TemplateResponse(
            "partials/referral/_books_table.html",
            {
                "request": request,
                "current_user": current_user,
                "books": books,
                "current_sort": sort,
                "current_order": order,
            },
        )

    return templates.TemplateResponse(
        "referral/books.html",
        {
            "request": request,
            "current_user": current_user,
            "books": books,
            "current_sort": sort,
            "current_order": order,
        },
    )


@router.get("/books/{book_id}", response_class=HTMLResponse)
async def book_detail(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Single book detail with registered members."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = ReferralFrontendService(db)
    detail = service.get_book_detail(book_id)

    if not detail:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "current_user": current_user},
            status_code=404,
        )

    return templates.TemplateResponse(
        "referral/book_detail.html",
        {
            "request": request,
            "current_user": current_user,
            "book": detail["book"],
            "stats": detail["stats"],
            "queue": detail["queue"],
            "service": service,
        },
    )


@router.get("/registrations", response_class=HTMLResponse)
async def registrations_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
    book_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    sort: str = Query("registration_number"),
    order: str = Query("asc"),
):
    """Registration list with filtering."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Validate sort/order
    allowed_sort_columns = [
        "member_name",
        "card_number",
        "book_name",
        "registration_number",
        "registration_date",
        "status",
        "check_marks",
    ]
    if sort not in allowed_sort_columns:
        sort = "registration_number"
    if order not in ("asc", "desc"):
        order = "asc"

    service = ReferralFrontendService(db)
    filters = {
        "book_id": book_id,
        "status": status,
        "search": search,
        "filter": filter,
    }
    registrations = service.get_registrations(
        filters=filters, page=page, sort=sort, order=order
    )

    # Get all books for filter dropdown
    books = service.get_books_overview()

    # If HTMX request, return partial
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/referral/_registrations_table.html",
            {
                "request": request,
                "current_user": current_user,
                "registrations": registrations,
                "service": service,
                "current_sort": sort,
                "current_order": order,
            },
        )

    return templates.TemplateResponse(
        "referral/registrations.html",
        {
            "request": request,
            "current_user": current_user,
            "registrations": registrations,
            "books": books,
            "filters": filters,
            "service": service,
            "current_sort": sort,
            "current_order": order,
        },
    )


@router.get("/registrations/{registration_id}", response_class=HTMLResponse)
async def registration_detail(
    registration_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Single registration detail."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = ReferralFrontendService(db)
    detail = service.get_registration_detail(registration_id)

    if not detail:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "current_user": current_user},
            status_code=404,
        )

    return templates.TemplateResponse(
        "referral/registration_detail.html",
        {
            "request": request,
            "current_user": current_user,
            "registration": detail["registration"],
            "member": detail["member"],
            "book": detail["book"],
            "queue_status": detail["queue_status"],
            "history": detail["history"],
            "service": service,
        },
    )


# ============================================================================
# HTMX Partials
# ============================================================================


@router.get("/partials/stats", response_class=HTMLResponse)
async def stats_partial(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: referral stats cards."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/login?next=/referral"},
        )

    service = ReferralFrontendService(db)
    stats = service.get_landing_stats()

    return templates.TemplateResponse(
        "partials/referral/_stats.html",
        {"request": request, "stats": stats},
    )


@router.get("/partials/books-overview", response_class=HTMLResponse)
async def books_overview_partial(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: books overview for landing page."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/login?next=/referral"},
        )

    service = ReferralFrontendService(db)
    books = service.get_books_overview()

    return templates.TemplateResponse(
        "partials/referral/_books_overview.html",
        {"request": request, "books": books},
    )


@router.get("/partials/books-table", response_class=HTMLResponse)
async def books_table_partial(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
    active_only: bool = Query(True),
    search: Optional[str] = Query(None),
    sort: str = Query("name"),
    order: str = Query("asc"),
):
    """HTMX partial: filtered books table."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/login?next=/referral"},
        )

    # Validate sort/order
    allowed_sort_columns = [
        "name",
        "classification",
        "region",
        "book_number",
        "active_count",
        "dispatched_count",
        "is_active",
    ]
    if sort not in allowed_sort_columns:
        sort = "name"
    if order not in ("asc", "desc"):
        order = "asc"

    service = ReferralFrontendService(db)
    books = service.get_books_overview(active_only=active_only, sort=sort, order=order)

    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        books = [
            b
            for b in books
            if search_lower in b.get("name", "").lower()
            or search_lower in b.get("code", "").lower()
        ]

    return templates.TemplateResponse(
        "partials/referral/_books_table.html",
        {
            "request": request,
            "current_user": current_user,
            "books": books,
            "current_sort": sort,
            "current_order": order,
        },
    )


@router.get("/books/{book_id}/partials/stats", response_class=HTMLResponse)
async def book_stats_partial(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: book stats for book detail page."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/login?next=/referral"},
        )

    service = ReferralFrontendService(db)
    stats = service.get_book_stats(book_id)

    if not stats:
        return HTMLResponse("Book not found", status_code=404)

    return templates.TemplateResponse(
        "partials/referral/_book_stats.html",
        {"request": request, "stats": stats},
    )


@router.get("/books/{book_id}/partials/queue", response_class=HTMLResponse)
async def book_queue_partial(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
):
    """HTMX partial: book queue table."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/login?next=/referral"},
        )

    service = ReferralFrontendService(db)
    detail = service.get_book_detail(book_id)

    if not detail:
        return HTMLResponse("Book not found", status_code=404)

    queue = detail["queue"]

    # Apply filters
    if search:
        search_lower = search.lower()
        queue = [
            q
            for q in queue
            if search_lower in q.get("member_name", "").lower()
            or search_lower in q.get("member_number", "").lower()
        ]

    if status_filter and status_filter != "all":
        if status_filter == "exempt":
            queue = [q for q in queue if q.get("is_exempt")]
        else:
            queue = [
                q for q in queue if str(q.get("status", "")).lower() == status_filter
            ]

    return templates.TemplateResponse(
        "partials/referral/_queue_table.html",
        {"request": request, "queue": queue, "service": service},
    )


@router.get("/partials/register-modal", response_class=HTMLResponse)
async def register_modal_partial(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
    book_id: Optional[int] = Query(None),
):
    """HTMX partial: register member modal form."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/login?next=/referral"},
        )

    service = ReferralFrontendService(db)
    books = service.get_active_books_for_dropdown()

    return templates.TemplateResponse(
        "partials/referral/_register_modal.html",
        {
            "request": request,
            "books": books,
            "book_id": book_id,
        },
    )


@router.get("/partials/re-sign-modal/{registration_id}", response_class=HTMLResponse)
async def re_sign_modal_partial(
    registration_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: re-sign confirmation modal."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/login?next=/referral"},
        )

    service = ReferralFrontendService(db)
    detail = service.get_registration_detail(registration_id)

    if not detail:
        return HTMLResponse("Registration not found", status_code=404)

    return templates.TemplateResponse(
        "partials/referral/_re_sign_modal.html",
        {
            "request": request,
            "registration": detail["registration"],
        },
    )


@router.get("/partials/resign-modal/{registration_id}", response_class=HTMLResponse)
async def resign_modal_partial(
    registration_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: resign confirmation modal."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/login?next=/referral"},
        )

    service = ReferralFrontendService(db)
    detail = service.get_registration_detail(registration_id)

    if not detail:
        return HTMLResponse("Registration not found", status_code=404)

    return templates.TemplateResponse(
        "partials/referral/_resign_modal.html",
        {
            "request": request,
            "registration": detail["registration"],
        },
    )


@router.get("/partials/member-search", response_class=HTMLResponse)
async def member_search_partial(
    request: Request,
    member_search: str = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX partial: member search typeahead results."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/login?next=/referral"},
        )

    service = ReferralFrontendService(db)
    members = service.search_members(member_search)

    if not members:
        return HTMLResponse(
            '<div class="text-sm text-base-content/60">No members found</div>'
        )

    html = '<div class="menu bg-base-200 rounded-box mt-1 shadow">'
    for member in members:
        html += f"""
        <div class="menu-item p-2 hover:bg-base-300 cursor-pointer"
             data-member-id="{member['id']}"
             data-member-name="{member['name']}">
            <div class="font-semibold">{member['name']}</div>
            <div class="text-xs text-base-content/60">{member['member_number']}</div>
        </div>
        """
    html += "</div>"

    return HTMLResponse(html)


# ============================================================================
# Form Submissions
# ============================================================================


@router.post("/registrations", response_class=HTMLResponse)
async def create_registration(
    request: Request,
    member_id: int = Form(...),
    book_id: int = Form(...),
    registration_method: str = Form("in_person"),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Process member registration form."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/login?next=/referral"},
        )

    service = ReferralFrontendService(db)
    result = service.register_member(
        {
            "member_id": member_id,
            "book_id": book_id,
            "registration_method": registration_method,
            "notes": notes,
            "performed_by_id": current_user["id"],
        }
    )

    if result.get("success"):
        # Close modal and show success message
        return HTMLResponse("""
            <script>
                document.getElementById('register-modal').close();
                showToast('Member registered successfully', 'success');
                window.location.reload();
            </script>
        """)
    else:
        # Show error in modal
        error_msg = result.get("error", "Registration failed")
        return HTMLResponse(f"""
            <div class="alert alert-error">
                <span>{error_msg}</span>
            </div>
        """)


@router.post("/registrations/{registration_id}/re-sign", response_class=HTMLResponse)
async def re_sign_registration(
    registration_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Process re-sign action."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/login?next=/referral"},
        )

    service = ReferralFrontendService(db)
    result = service.re_sign_member(registration_id, current_user["id"])

    if result.get("success"):
        return HTMLResponse("""
            <script>
                document.getElementById('re-sign-modal').close();
                showToast('Member re-signed successfully', 'success');
                window.location.reload();
            </script>
        """)
    else:
        error_msg = result.get("error", "Re-sign failed")
        return HTMLResponse(f"""
            <div class="alert alert-error">
                <span>{error_msg}</span>
            </div>
        """)


@router.post("/registrations/{registration_id}/resign", response_class=HTMLResponse)
async def resign_registration(
    registration_id: int,
    request: Request,
    reason: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Process resign action."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse(
            "Session expired",
            status_code=401,
            headers={"HX-Redirect": "/login?next=/referral"},
        )

    service = ReferralFrontendService(db)
    result = service.resign_member(registration_id, current_user["id"], reason)

    if result.get("success"):
        return HTMLResponse("""
            <script>
                document.getElementById('resign-modal').close();
                showToast('Member resigned from book', 'success');
                window.location.reload();
            </script>
        """)
    else:
        error_msg = result.get("error", "Resignation failed")
        return HTMLResponse(f"""
            <div class="alert alert-error">
                <span>{error_msg}</span>
            </div>
        """)
