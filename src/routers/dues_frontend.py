"""Frontend routes for dues management."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.enums import MemberClassification, DuesPaymentStatus, DuesPaymentMethod, DuesAdjustmentType, AdjustmentStatus
from src.models import Member
from src.routers.dependencies.auth_cookie import require_auth
from src.services.dues_frontend_service import DuesFrontendService

router = APIRouter(prefix="/dues", tags=["dues-frontend"])

templates = Jinja2Templates(directory="src/templates")


@router.get("", response_class=HTMLResponse)
async def dues_landing(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Dues management landing page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    stats = DuesFrontendService.get_landing_stats(db)

    return templates.TemplateResponse(
        "dues/index.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "format_currency": DuesFrontendService.format_currency,
            "format_period_name": DuesFrontendService.format_period_name,
        },
    )


@router.get("/rates", response_class=HTMLResponse)
async def rates_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Dues rates list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    classifications = list(MemberClassification)
    rates, total = DuesFrontendService.get_all_rates(db, active_only=False)

    return templates.TemplateResponse(
        "dues/rates/index.html",
        {
            "request": request,
            "user": current_user,
            "rates": rates,
            "total": total,
            "classifications": classifications,
            "get_badge_class": DuesFrontendService.get_classification_badge_class,
            "format_currency": DuesFrontendService.format_currency,
            "today": date.today(),
        },
    )


@router.get("/rates/search", response_class=HTMLResponse)
async def rates_search(
    request: Request,
    classification: Optional[str] = Query(None),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX endpoint for rates table filtering."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    classification_enum = None
    if classification:
        try:
            classification_enum = MemberClassification(classification)
        except ValueError:
            pass

    rates, total = DuesFrontendService.get_all_rates(
        db, classification=classification_enum, active_only=active_only
    )

    return templates.TemplateResponse(
        "dues/rates/partials/_table.html",
        {
            "request": request,
            "rates": rates,
            "total": total,
            "get_badge_class": DuesFrontendService.get_classification_badge_class,
            "format_currency": DuesFrontendService.format_currency,
            "today": date.today(),
        },
    )


# --- Periods Routes ---


@router.get("/periods", response_class=HTMLResponse)
async def periods_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Dues periods list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    years = DuesFrontendService.get_available_years(db)
    periods, total = DuesFrontendService.get_all_periods(db)

    # Add current year if not in list
    current_year = date.today().year
    if current_year not in years:
        years.insert(0, current_year)

    return templates.TemplateResponse(
        "dues/periods/index.html",
        {
            "request": request,
            "user": current_user,
            "periods": periods,
            "total": total,
            "years": years,
            "current_year": current_year,
            "format_currency": DuesFrontendService.format_currency,
            "format_period_name": DuesFrontendService.format_period_name,
            "get_status_badge": DuesFrontendService.get_period_status_badge_class,
            "get_status_text": DuesFrontendService.get_period_status_text,
        },
    )


@router.get("/periods/search", response_class=HTMLResponse)
async def periods_search(
    request: Request,
    year: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX endpoint for periods table filtering."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    # Parse status filter
    is_closed = None
    if status == "open":
        is_closed = False
    elif status == "closed":
        is_closed = True

    periods, total = DuesFrontendService.get_all_periods(
        db, year=year, is_closed=is_closed
    )

    return templates.TemplateResponse(
        "dues/periods/partials/_table.html",
        {
            "request": request,
            "periods": periods,
            "total": total,
            "format_currency": DuesFrontendService.format_currency,
            "format_period_name": DuesFrontendService.format_period_name,
            "get_status_badge": DuesFrontendService.get_period_status_badge_class,
            "get_status_text": DuesFrontendService.get_period_status_text,
        },
    )


@router.get("/periods/{period_id}", response_class=HTMLResponse)
async def period_detail(
    request: Request,
    period_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Period detail page with payment summary."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    period_data = DuesFrontendService.get_period_with_stats(db, period_id)
    if not period_data:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "user": current_user},
            status_code=404,
        )

    return templates.TemplateResponse(
        "dues/periods/detail.html",
        {
            "request": request,
            "user": current_user,
            **period_data,
            "format_currency": DuesFrontendService.format_currency,
            "format_period_name": DuesFrontendService.format_period_name,
            "get_status_badge": DuesFrontendService.get_period_status_badge_class,
            "get_status_text": DuesFrontendService.get_period_status_text,
            "get_payment_badge": DuesFrontendService.get_payment_status_badge_class,
        },
    )


@router.post("/periods/generate", response_class=HTMLResponse)
async def generate_periods(
    request: Request,
    year: int = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Generate 12 periods for a year."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    from src.services.dues_period_service import DuesPeriodService

    try:
        periods = DuesPeriodService.generate_year_periods(db, year)
        db.commit()

        # Return updated table via HTMX
        all_periods, total = DuesFrontendService.get_all_periods(db, year=year)

        return templates.TemplateResponse(
            "dues/periods/partials/_table.html",
            {
                "request": request,
                "periods": all_periods,
                "total": total,
                "format_currency": DuesFrontendService.format_currency,
                "format_period_name": DuesFrontendService.format_period_name,
                "get_status_badge": DuesFrontendService.get_period_status_badge_class,
                "get_status_text": DuesFrontendService.get_period_status_text,
                "success_message": f"Generated {len(periods)} periods for {year}",
            },
        )
    except Exception as e:
        db.rollback()
        all_periods, total = DuesFrontendService.get_all_periods(db)
        return templates.TemplateResponse(
            "dues/periods/partials/_table.html",
            {
                "request": request,
                "periods": all_periods,
                "total": total,
                "format_currency": DuesFrontendService.format_currency,
                "format_period_name": DuesFrontendService.format_period_name,
                "get_status_badge": DuesFrontendService.get_period_status_badge_class,
                "get_status_text": DuesFrontendService.get_period_status_text,
                "error_message": str(e),
            },
        )


@router.post("/periods/{period_id}/close", response_class=HTMLResponse)
async def close_period(
    request: Request,
    period_id: int,
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Close a dues period."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    from src.services.dues_period_service import DuesPeriodService

    try:
        period = DuesPeriodService.close_period(
            db,
            period_id=period_id,
            closed_by_id=current_user["id"],
            notes=notes,
        )
        db.commit()

        return RedirectResponse(
            url=f"/dues/periods/{period_id}?success=Period closed successfully",
            status_code=303,
        )
    except Exception as e:
        db.rollback()
        return RedirectResponse(
            url=f"/dues/periods/{period_id}?error={str(e)}",
            status_code=303,
        )


# --- Payments Routes ---


@router.get("/payments", response_class=HTMLResponse)
async def payments_list(
    request: Request,
    period_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Dues payments list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    payments, total = DuesFrontendService.get_all_payments(db, period_id=period_id)

    # Get available periods for filter
    periods, _ = DuesFrontendService.get_all_periods(db, limit=24)

    # Get payment statuses for filter
    statuses = list(DuesPaymentStatus)

    return templates.TemplateResponse(
        "dues/payments/index.html",
        {
            "request": request,
            "user": current_user,
            "payments": payments,
            "total": total,
            "periods": periods,
            "statuses": statuses,
            "selected_period_id": period_id,
            "format_currency": DuesFrontendService.format_currency,
            "format_period_name": DuesFrontendService.format_period_name,
            "get_payment_badge": DuesFrontendService.get_payment_status_badge_class,
            "get_method_display": DuesFrontendService.get_payment_method_display,
        },
    )


@router.get("/payments/search", response_class=HTMLResponse)
async def payments_search(
    request: Request,
    q: Optional[str] = Query(None),
    period_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX endpoint for payments table filtering."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    # Parse status
    status_enum = None
    if status:
        try:
            status_enum = DuesPaymentStatus(status)
        except ValueError:
            pass

    payments, total = DuesFrontendService.get_all_payments(
        db, q=q, period_id=period_id, status=status_enum
    )

    return templates.TemplateResponse(
        "dues/payments/partials/_table.html",
        {
            "request": request,
            "payments": payments,
            "total": total,
            "format_currency": DuesFrontendService.format_currency,
            "format_period_name": DuesFrontendService.format_period_name,
            "get_payment_badge": DuesFrontendService.get_payment_status_badge_class,
            "get_method_display": DuesFrontendService.get_payment_method_display,
        },
    )


@router.get("/payments/member/{member_id}", response_class=HTMLResponse)
async def member_payments(
    request: Request,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Member payment history page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "user": current_user},
            status_code=404,
        )

    summary = DuesFrontendService.get_member_payment_summary(db, member_id)

    return templates.TemplateResponse(
        "dues/payments/member.html",
        {
            "request": request,
            "user": current_user,
            "member": member,
            **summary,
            "format_currency": DuesFrontendService.format_currency,
            "format_period_name": DuesFrontendService.format_period_name,
            "get_payment_badge": DuesFrontendService.get_payment_status_badge_class,
            "get_method_display": DuesFrontendService.get_payment_method_display,
        },
    )


@router.post("/payments/{payment_id}/record", response_class=HTMLResponse)
async def record_payment(
    request: Request,
    payment_id: int,
    amount_paid: str = Form(...),
    payment_method: Optional[str] = Form(None),
    check_number: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Record a payment."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    from src.services.dues_payment_service import DuesPaymentService
    from decimal import Decimal, InvalidOperation

    try:
        amount = Decimal(amount_paid)
        method_enum = None
        if payment_method:
            try:
                method_enum = DuesPaymentMethod(payment_method)
            except ValueError:
                pass

        payment = DuesPaymentService.record_payment(
            db,
            payment_id=payment_id,
            amount_paid=amount,
            payment_method=method_enum,
            check_number=check_number,
            notes=notes,
        )
        db.commit()

        return RedirectResponse(
            url=f"/dues/payments?success=Payment recorded successfully",
            status_code=303,
        )
    except (InvalidOperation, Exception) as e:
        db.rollback()
        return RedirectResponse(
            url=f"/dues/payments?error={str(e)}",
            status_code=303,
        )


# --- Adjustments Routes ---


@router.get("/adjustments", response_class=HTMLResponse)
async def adjustments_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Dues adjustments list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    adjustments, total = DuesFrontendService.get_all_adjustments(db)

    # Get filter options
    statuses = list(AdjustmentStatus)
    types = list(DuesAdjustmentType)

    return templates.TemplateResponse(
        "dues/adjustments/index.html",
        {
            "request": request,
            "user": current_user,
            "adjustments": adjustments,
            "total": total,
            "statuses": statuses,
            "types": types,
            "format_currency": DuesFrontendService.format_currency,
            "get_status_badge": DuesFrontendService.get_adjustment_status_badge_class,
            "get_type_badge": DuesFrontendService.get_adjustment_type_badge_class,
        },
    )


@router.get("/adjustments/search", response_class=HTMLResponse)
async def adjustments_search(
    request: Request,
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    adjustment_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """HTMX endpoint for adjustments table filtering."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    # Parse enums
    status_enum = None
    if status:
        try:
            status_enum = AdjustmentStatus(status)
        except ValueError:
            pass

    type_enum = None
    if adjustment_type:
        try:
            type_enum = DuesAdjustmentType(adjustment_type)
        except ValueError:
            pass

    adjustments, total = DuesFrontendService.get_all_adjustments(
        db, q=q, status=status_enum, adjustment_type=type_enum
    )

    return templates.TemplateResponse(
        "dues/adjustments/partials/_table.html",
        {
            "request": request,
            "adjustments": adjustments,
            "total": total,
            "format_currency": DuesFrontendService.format_currency,
            "get_status_badge": DuesFrontendService.get_adjustment_status_badge_class,
            "get_type_badge": DuesFrontendService.get_adjustment_type_badge_class,
        },
    )


@router.get("/adjustments/{adjustment_id}", response_class=HTMLResponse)
async def adjustment_detail(
    request: Request,
    adjustment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Adjustment detail page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    adjustment = DuesFrontendService.get_adjustment_detail(db, adjustment_id)
    if not adjustment:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "user": current_user},
            status_code=404,
        )

    return templates.TemplateResponse(
        "dues/adjustments/detail.html",
        {
            "request": request,
            "user": current_user,
            "adjustment": adjustment,
            "format_currency": DuesFrontendService.format_currency,
            "get_status_badge": DuesFrontendService.get_adjustment_status_badge_class,
            "get_type_badge": DuesFrontendService.get_adjustment_type_badge_class,
        },
    )


@router.post("/adjustments/{adjustment_id}/approve", response_class=HTMLResponse)
async def approve_adjustment(
    request: Request,
    adjustment_id: int,
    approved: str = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Approve or deny an adjustment."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    from src.services.dues_adjustment_service import DuesAdjustmentService

    try:
        is_approved = approved.lower() == "true"

        adjustment = DuesAdjustmentService.approve_adjustment(
            db,
            adjustment_id=adjustment_id,
            approved=is_approved,
            approved_by_id=current_user["id"],
            notes=notes,
        )
        db.commit()

        action = "approved" if is_approved else "denied"
        return RedirectResponse(
            url=f"/dues/adjustments/{adjustment_id}?success=Adjustment {action}",
            status_code=303,
        )
    except Exception as e:
        db.rollback()
        return RedirectResponse(
            url=f"/dues/adjustments/{adjustment_id}?error={str(e)}",
            status_code=303,
        )
