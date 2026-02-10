"""
View As API for developer role impersonation.
Allows developers to view the UI as if they were a different role.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse

from src.routers.dependencies.auth_cookie import require_auth
from src.db.enums import RoleType

router = APIRouter(prefix="/api/v1/view-as", tags=["view-as"])


AVAILABLE_ROLES = [
    RoleType.ADMIN.value,
    RoleType.OFFICER.value,
    RoleType.STAFF.value,
    RoleType.ORGANIZER.value,
    RoleType.INSTRUCTOR.value,
    RoleType.MEMBER.value,
]


@router.post("/set/{role}")
async def set_view_as(
    role: str,
    request: Request,
    current_user: dict = Depends(require_auth),
):
    """
    Set the viewing_as role in the session.
    Only developer role can use this endpoint.
    """
    # Check if user is developer
    if "developer" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=403, detail="Only developer role can use View As feature"
        )

    # Validate role
    if role not in AVAILABLE_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Available roles: {', '.join(AVAILABLE_ROLES)}",
        )

    # Set viewing_as in session
    request.session["viewing_as"] = role

    return JSONResponse(
        content={
            "status": "success",
            "viewing_as": role,
            "message": f"Now viewing as: {role}",
        }
    )


@router.post("/clear")
async def clear_view_as(
    request: Request,
    current_user: dict = Depends(require_auth),
):
    """Clear the viewing_as role from the session."""
    # Check if user is developer
    if "developer" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=403, detail="Only developer role can use View As feature"
        )

    # Clear viewing_as from session
    if "viewing_as" in request.session:
        del request.session["viewing_as"]

    return JSONResponse(
        content={
            "status": "success",
            "viewing_as": None,
            "message": "Cleared View As - now viewing as Developer",
        }
    )


@router.get("/current")
async def get_current_view_as(
    request: Request,
    current_user: dict = Depends(require_auth),
):
    """Get the current viewing_as role from the session."""
    # Check if user is developer
    if "developer" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=403, detail="Only developer role can use View As feature"
        )

    viewing_as = request.session.get("viewing_as")

    return JSONResponse(
        content={
            "status": "success",
            "viewing_as": viewing_as,
            "available_roles": AVAILABLE_ROLES,
        }
    )
