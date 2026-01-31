"""Frontend routes for user profile management."""
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.models.user import User
from src.routers.dependencies.auth_cookie import get_current_user_model
from src.services.profile_service import profile_service

templates = Jinja2Templates(directory="src/templates")
router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_class=HTMLResponse)
def profile_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_model),
):
    """User profile page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

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


@router.get("/change-password", response_class=HTMLResponse)
def change_password_page(
    request: Request,
    current_user: User = Depends(get_current_user_model),
):
    """Change password page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    return templates.TemplateResponse(
        "profile/change_password.html",
        {
            "request": request,
            "current_user": current_user,
            "page_title": "Change Password",
        }
    )


@router.post("/change-password")
def update_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_model),
):
    """Process password change."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Validate passwords match
    if new_password != confirm_password:
        return templates.TemplateResponse(
            "profile/change_password.html",
            {
                "request": request,
                "current_user": current_user,
                "page_title": "Change Password",
                "error": "New passwords do not match",
            },
            status_code=400
        )

    # Attempt password change
    success, message = profile_service.change_password(
        db, current_user, current_password, new_password
    )

    if not success:
        return templates.TemplateResponse(
            "profile/change_password.html",
            {
                "request": request,
                "current_user": current_user,
                "page_title": "Change Password",
                "error": message,
            },
            status_code=400
        )

    # Redirect to profile with success message
    return RedirectResponse(
        url="/profile?message=Password+changed+successfully",
        status_code=303
    )
