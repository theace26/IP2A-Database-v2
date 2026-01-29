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
    """Documents landing page with overview and quick actions."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Get document counts by entity type
    entity_counts = {}
    for entity_type in ENTITY_TYPES.keys():
        stmt = select(func.count(FileAttachment.id)).where(
            FileAttachment.record_type == entity_type,
            FileAttachment.is_deleted == False,
        )
        result = await db.execute(stmt)
        entity_counts[entity_type] = result.scalar() or 0

    # Get total document count
    total_stmt = select(func.count(FileAttachment.id)).where(
        FileAttachment.is_deleted == False
    )
    total_result = await db.execute(total_stmt)
    total_count = total_result.scalar() or 0

    # Get recent documents
    recent_stmt = (
        select(FileAttachment)
        .where(FileAttachment.is_deleted == False)
        .order_by(FileAttachment.created_at.desc())
        .limit(10)
    )
    recent_result = await db.execute(recent_stmt)
    recent_docs = recent_result.scalars().all()

    return templates.TemplateResponse(
        "documents/index.html",
        {
            "request": request,
            "user": current_user,
            "entity_types": ENTITY_TYPES,
            "entity_counts": entity_counts,
            "total_count": total_count,
            "recent_docs": recent_docs,
            "format_file_size": format_file_size,
            "get_file_icon": get_file_icon,
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
    """Upload page with drag-drop zone."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    return templates.TemplateResponse(
        "documents/upload.html",
        {
            "request": request,
            "user": current_user,
            "entity_types": ENTITY_TYPES,
            "selected_entity_type": entity_type,
            "selected_entity_id": entity_id,
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
    """Browse documents with filters."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    page_size = 20

    # Build query
    stmt = select(FileAttachment).where(FileAttachment.is_deleted == False)

    if entity_type and entity_type != "all":
        stmt = stmt.where(FileAttachment.record_type == entity_type)

    if entity_id:
        stmt = stmt.where(FileAttachment.record_id == entity_id)

    # Count total
    count_stmt = select(func.count(FileAttachment.id)).where(FileAttachment.is_deleted == False)
    if entity_type and entity_type != "all":
        count_stmt = count_stmt.where(FileAttachment.record_type == entity_type)
    if entity_id:
        count_stmt = count_stmt.where(FileAttachment.record_id == entity_id)

    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0
    total_pages = (total + page_size - 1) // page_size

    # Get documents
    stmt = stmt.order_by(FileAttachment.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    documents = result.scalars().all()

    # Check if HTMX request
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "documents/partials/_file_list.html",
            {
                "request": request,
                "documents": documents,
                "format_file_size": format_file_size,
                "get_file_icon": get_file_icon,
                "entity_type": entity_type,
                "page": page,
                "total_pages": total_pages,
                "total": total,
            },
        )

    return templates.TemplateResponse(
        "documents/browse.html",
        {
            "request": request,
            "user": current_user,
            "entity_types": ENTITY_TYPES,
            "documents": documents,
            "format_file_size": format_file_size,
            "get_file_icon": get_file_icon,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "page": page,
            "total_pages": total_pages,
            "total": total,
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
