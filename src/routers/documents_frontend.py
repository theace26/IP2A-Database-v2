"""
Documents Frontend Router - Pages for document management.
"""

from fastapi import APIRouter, Depends, Request, Query, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.db.session import get_db
from src.routers.dependencies.auth_cookie import require_auth
from src.models import FileAttachment, Member, Student, Grievance, SALTingActivity, BenevolenceApplication
from src.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents-frontend"])
templates = Jinja2Templates(directory="src/templates")


# Entity type configurations
ENTITY_TYPES = {
    "member": {"model": Member, "name": "Members", "icon": "users"},
    "student": {"model": Student, "name": "Students", "icon": "academic-cap"},
    "grievance": {"model": Grievance, "name": "Grievances", "icon": "document-text"},
    "salting": {"model": SALTingActivity, "name": "SALTing", "icon": "clipboard-list"},
    "benevolence": {"model": BenevolenceApplication, "name": "Benevolence", "icon": "heart"},
}


def format_file_size(size: int) -> str:
    """Format file size in human readable format."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / (1024 * 1024 * 1024):.1f} GB"


def get_file_icon(content_type: str) -> str:
    """Get icon class based on content type."""
    if content_type.startswith("image/"):
        return "photo"
    elif content_type == "application/pdf":
        return "document-text"
    elif content_type.startswith("text/"):
        return "document"
    elif "spreadsheet" in content_type or "excel" in content_type:
        return "table-cells"
    elif "word" in content_type or "document" in content_type:
        return "document-text"
    return "paper-clip"


# ============================================================
# Documents Landing Page
# ============================================================


@router.get("", response_class=HTMLResponse)
async def documents_landing(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Documents landing page - currently shows feature not implemented."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Feature not implemented - show placeholder page
    return templates.TemplateResponse(
        "documents/not_implemented.html",
        {
            "request": request,
            "user": current_user,
        },
    )


# ============================================================
# Upload Page
# ============================================================


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(
    request: Request,
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Upload page - currently shows feature not implemented."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Feature not implemented - show placeholder page
    return templates.TemplateResponse(
        "documents/not_implemented.html",
        {
            "request": request,
            "user": current_user,
        },
    )


@router.post("/upload", response_class=HTMLResponse)
async def handle_upload(
    request: Request,
    file: UploadFile = File(...),
    entity_type: str = Form(...),
    entity_id: int = Form(...),
    category: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Handle file upload via HTMX."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    try:
        # Read file content
        content = await file.read()
        size = len(content)

        # Create file attachment
        from io import BytesIO
        file_obj = BytesIO(content)

        service = DocumentService(db)
        attachment = service.upload_document(
            file_data=file_obj,
            filename=file.filename or "unnamed",
            content_type=file.content_type or "application/octet-stream",
            size=size,
            record_type=entity_type,
            record_id=entity_id,
            category=category,
        )

        if attachment:
            return templates.TemplateResponse(
                "documents/partials/_upload_success.html",
                {
                    "request": request,
                    "document": attachment,
                    "format_file_size": format_file_size,
                },
            )
        else:
            return templates.TemplateResponse(
                "documents/partials/_upload_error.html",
                {
                    "request": request,
                    "error": "Failed to upload file",
                },
            )

    except Exception as e:
        return templates.TemplateResponse(
            "documents/partials/_upload_error.html",
            {
                "request": request,
                "error": str(e),
            },
        )


# ============================================================
# Browse Page
# ============================================================


@router.get("/browse", response_class=HTMLResponse)
async def browse_page(
    request: Request,
    entity_type: Optional[str] = Query("all"),
    entity_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Browse documents - currently shows feature not implemented."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Feature not implemented - show placeholder page
    return templates.TemplateResponse(
        "documents/not_implemented.html",
        {
            "request": request,
            "user": current_user,
        },
    )


# ============================================================
# Download Redirect
# ============================================================


@router.get("/{document_id}/download")
async def download_redirect(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Redirect to presigned download URL."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DocumentService(db)
    url = service.get_download_url(document_id, expiry=3600)

    if url:
        return RedirectResponse(url=url)

    # Fall back to direct download
    from fastapi.responses import StreamingResponse
    result = service.download_document(document_id)
    if result:
        content, filename, content_type = result
        return StreamingResponse(
            content,
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return RedirectResponse(url="/documents/browse?error=not_found")


# ============================================================
# Delete Document
# ============================================================


@router.post("/{document_id}/delete", response_class=HTMLResponse)
async def delete_document(
    request: Request,
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Delete document (soft delete)."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = DocumentService(db)
    success = service.delete_document(document_id, soft_delete=True)

    if success:
        return templates.TemplateResponse(
            "documents/partials/_delete_success.html",
            {
                "request": request,
                "document_id": document_id,
            },
        )
    else:
        return templates.TemplateResponse(
            "documents/partials/_delete_error.html",
            {
                "request": request,
                "error": "Failed to delete document",
            },
        )
