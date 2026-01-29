"""Frontend routes for dues management."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.enums import MemberClassification
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
