"""
Referral Reports API Router for Phase 7.

Created: February 5, 2026 (Week 33A)
Updated: February 5, 2026 (Week 33B - Dispatch reports added)
Phase 7 - Referral & Dispatch System

Endpoints for generating out-of-work list and dispatch reports (PDF/Excel).
"""

from typing import Optional
from datetime import date
from io import BytesIO

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.routers.dependencies.auth import get_current_user
from src.models.user import User
from src.services.referral_report_service import ReferralReportService

router = APIRouter()


@router.get("/out-of-work/book/{book_id}")
def get_out_of_work_by_book(
    book_id: int,
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    tier: Optional[int] = Query(None, ge=1, le=4),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate out-of-work list for a specific book.

    Args:
        book_id: The referral book ID
        format: Output format (pdf or xlsx)
        tier: Optional tier filter (1-4)

    Returns:
        PDF or Excel file as streaming response
    """
    service = ReferralReportService(db)

    if format == "pdf":
        buffer = service.render_out_of_work_by_book_pdf(book_id, tier)
        if buffer is None:
            raise HTTPException(status_code=404, detail="Book not found")
        media_type = "application/pdf"
        tier_suffix = f"_tier{tier}" if tier else ""
        filename = f"out_of_work_book_{book_id}{tier_suffix}.pdf"
    else:
        buffer = service.render_out_of_work_by_book_excel(book_id, tier)
        if buffer is None:
            raise HTTPException(status_code=404, detail="Book not found")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        tier_suffix = f"_tier{tier}" if tier else ""
        filename = f"out_of_work_book_{book_id}{tier_suffix}.xlsx"

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/out-of-work/all-books")
def get_out_of_work_all_books(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate combined out-of-work list across all books.

    Args:
        format: Output format (pdf or xlsx)

    Returns:
        PDF or Excel file as streaming response
    """
    service = ReferralReportService(db)

    if format == "pdf":
        buffer = service.render_out_of_work_all_books_pdf()
        media_type = "application/pdf"
        filename = "out_of_work_all_books.pdf"
    else:
        buffer = service.render_out_of_work_all_books_excel()
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "out_of_work_all_books.xlsx"

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/out-of-work/summary")
def get_out_of_work_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate out-of-work summary (counts per book per tier).

    Returns:
        PDF file as streaming response (summary is PDF-only)
    """
    service = ReferralReportService(db)
    buffer = service.render_out_of_work_summary_pdf()

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=out_of_work_summary.pdf"},
    )


@router.get("/member/{member_id}/registrations")
def get_member_registrations(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate registration overview for a specific member.

    Args:
        member_id: The member ID

    Returns:
        PDF file as streaming response
    """
    service = ReferralReportService(db)
    buffer = service.render_member_registrations_pdf(member_id)

    if buffer is None:
        raise HTTPException(status_code=404, detail="Member not found")

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=member_{member_id}_registrations.pdf"
        },
    )


# --- Week 33B: Dispatch & Labor Request Reports ---


@router.get("/dispatch-log")
def get_dispatch_log(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(
        None, description="End date, defaults to start_date"
    ),
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate daily dispatch log for a date range.

    Args:
        start_date: Start date (required)
        end_date: End date (optional, defaults to start_date for single day)
        format: Output format (pdf or xlsx)

    Returns:
        PDF or Excel file as streaming response
    """
    service = ReferralReportService(db)

    if format == "pdf":
        buffer = service.render_daily_dispatch_log_pdf(start_date, end_date)
        media_type = "application/pdf"
        date_str = start_date.strftime("%Y%m%d")
        filename = f"dispatch_log_{date_str}.pdf"
    else:
        buffer = service.render_daily_dispatch_log_excel(start_date, end_date)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        date_str = start_date.strftime("%Y%m%d")
        filename = f"dispatch_log_{date_str}.xlsx"

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/member/{member_id}/dispatch-history")
def get_member_dispatch_history(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate dispatch history for a specific member.

    Args:
        member_id: The member ID

    Returns:
        PDF file as streaming response
    """
    service = ReferralReportService(db)
    buffer = service.render_member_dispatch_history_pdf(member_id)

    if buffer is None:
        raise HTTPException(status_code=404, detail="Member not found")

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=member_{member_id}_dispatch_history.pdf"
        },
    )


@router.get("/labor-requests")
def get_labor_request_status(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    status: Optional[str] = Query(
        None, description="Filter by status: OPEN, FILLED, CANCELLED, EXPIRED"
    ),
    start_date: Optional[date] = Query(
        None, description="Filter by request date (start)"
    ),
    end_date: Optional[date] = Query(None, description="Filter by request date (end)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate labor request status report.

    Args:
        format: Output format (pdf or xlsx)
        status: Optional status filter
        start_date/end_date: Optional date range filter

    Returns:
        PDF or Excel file as streaming response
    """
    service = ReferralReportService(db)

    if format == "pdf":
        buffer = service.render_labor_request_status_pdf(status, start_date, end_date)
        media_type = "application/pdf"
        filename = "labor_request_status.pdf"
    else:
        buffer = service.render_labor_request_status_excel(status, start_date, end_date)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "labor_request_status.xlsx"

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/morning-referral")
def get_morning_referral_sheet(
    target_date: Optional[date] = Query(
        None, description="Processing date (defaults to today)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate morning referral processing sheet.

    THIS IS THE MOST CRITICAL DAILY REPORT.
    Dispatchers print this every morning to process referrals.

    Args:
        target_date: The morning being processed (defaults to today)

    Returns:
        PDF file as streaming response (landscape format)
    """
    service = ReferralReportService(db)
    buffer = service.render_morning_referral_sheet_pdf(target_date)

    effective_date = target_date or date.today()
    date_str = effective_date.strftime("%Y%m%d")

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=morning_referral_{date_str}.pdf"
        },
    )


@router.get("/active-dispatches")
def get_active_dispatches(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate active dispatches report.

    Args:
        format: Output format (pdf or xlsx)

    Returns:
        PDF or Excel file as streaming response
    """
    service = ReferralReportService(db)

    if format == "pdf":
        buffer = service.render_active_dispatches_pdf()
        media_type = "application/pdf"
        filename = "active_dispatches.pdf"
    else:
        buffer = service.render_active_dispatches_excel()
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "active_dispatches.xlsx"

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# --- Week 34: Employer & Registration Reports ---


@router.get("/employers/active")
def get_employer_active_list(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    contract_code: Optional[str] = Query(None, description="Filter by contract code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate employer active list report.

    Shows employers with open labor requests or currently dispatched workers.

    Args:
        format: Output format (pdf or xlsx)
        contract_code: Optional contract code filter (e.g., 'WIREPERSON')

    Returns:
        PDF or Excel file as streaming response
    """
    service = ReferralReportService(db)

    if format == "pdf":
        buffer = service.render_employer_active_list_pdf(contract_code)
        media_type = "application/pdf"
        filename = "employer_active_list.pdf"
    else:
        buffer = service.render_employer_active_list_excel(contract_code)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "employer_active_list.xlsx"

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/employers/{employer_id}/dispatch-history")
def get_employer_dispatch_history(
    employer_id: int,
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate dispatch history for a specific employer.

    Args:
        employer_id: The employer ID
        format: Output format (pdf or xlsx)
        start_date/end_date: Optional date range (defaults to current year)

    Returns:
        PDF or Excel file as streaming response
    """
    service = ReferralReportService(db)

    if format == "pdf":
        buffer = service.render_employer_dispatch_history_pdf(
            employer_id, start_date, end_date
        )
        if buffer is None:
            raise HTTPException(status_code=404, detail="Employer not found")
        media_type = "application/pdf"
        filename = f"employer_{employer_id}_dispatch_history.pdf"
    else:
        buffer = service.render_employer_dispatch_history_excel(
            employer_id, start_date, end_date
        )
        if buffer is None:
            raise HTTPException(status_code=404, detail="Employer not found")
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"employer_{employer_id}_dispatch_history.xlsx"

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/registrations/history")
def get_registration_history(
    format: str = Query("xlsx", pattern="^xlsx$"),  # Excel only
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    activity_type: Optional[str] = Query(
        None, description="Filter by activity type (REGISTER, RE_SIGN, etc.)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate registration activity history report.

    NOTE: Excel only - this report is too data-dense for PDF.

    Args:
        format: Output format (xlsx only)
        book_id: Optional book ID filter
        start_date/end_date: Date range (defaults to last 30 days)
        activity_type: Filter by activity type

    Returns:
        Excel file as streaming response (2 sheets: Activity Log, Summary)
    """
    service = ReferralReportService(db)

    buffer = service.render_registration_history_excel(
        book_id, start_date, end_date, activity_type
    )

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=registration_history.xlsx"},
    )


@router.get("/check-marks")
def get_check_mark_report(
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate check mark status report.

    Shows all members with 1+ check marks, organized by book.
    Highlights members at the 2-mark limit (one more = roll-off).

    Args:
        book_id: Optional book ID filter

    Returns:
        PDF file as streaming response
    """
    service = ReferralReportService(db)
    buffer = service.render_check_mark_report_pdf(book_id)

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=check_mark_report.pdf"},
    )


@router.get("/re-sign-due")
def get_re_sign_due_list(
    days_ahead: int = Query(7, ge=1, le=30, description="Show members due within N days"),
    include_overdue: bool = Query(True, description="Include overdue members"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate re-sign due list report.

    THIS IS A CRITICAL DAILY REPORT.
    Members who miss their 30-day re-sign deadline are dropped from ALL books.

    Args:
        days_ahead: Show members due within this many days (default 7)
        include_overdue: Include already-overdue members (default True)

    Returns:
        PDF file as streaming response
    """
    service = ReferralReportService(db)
    buffer = service.render_re_sign_due_list_pdf(days_ahead, include_overdue)

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=re_sign_due_list.pdf"},
    )


# =====================================================================
# WEEK 36 P1 REPORTS: Registration & Book Analytics
# =====================================================================


@router.get("/registration-activity-summary")
def get_registration_activity_summary(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate registration activity summary report.

    Shows aggregate registration, drop, re-sign, and dispatch activity by period.

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Date range (defaults to last 30 days)
        book_id: Optional book filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_registration_activity_summary(start_date, end_date, book_id)
    elif format == "xlsx":
        buffer = service.render_registration_activity_summary_excel(
            start_date, end_date, book_id
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=registration_activity_summary.xlsx"
            },
        )
    else:
        buffer = service.render_registration_activity_summary_pdf(
            start_date, end_date, book_id
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=registration_activity_summary.pdf"
            },
        )


@router.get("/registration-by-classification")
def get_registration_by_classification(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    snapshot_date: Optional[date] = Query(None, description="Snapshot date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate registration by classification report.

    Breakdown of active registrations by member classification.

    Args:
        format: Output format (pdf, xlsx, or json)
        snapshot_date: Date for snapshot (defaults to today)
        book_id: Optional book filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_registration_by_classification(snapshot_date, book_id)
    elif format == "xlsx":
        buffer = service.render_registration_by_classification_excel(
            snapshot_date, book_id
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=registration_by_classification.xlsx"
            },
        )
    else:
        buffer = service.render_registration_by_classification_pdf(snapshot_date, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=registration_by_classification.pdf"
            },
        )


@router.get("/re-registration-analysis")
def get_re_registration_analysis(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    reason: Optional[str] = Query(None, description="Filter by reason keyword"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate re-registration analysis report.

    Patterns of re-registration — short calls, 90-day cycles, voluntary.

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Date range (defaults to last 90 days)
        book_id: Optional book filter
        reason: Optional reason keyword filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_re_registration_analysis(start_date, end_date, book_id, reason)
    elif format == "xlsx":
        buffer = service.render_re_registration_analysis_excel(
            start_date, end_date, book_id, reason
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=re_registration_analysis.xlsx"
            },
        )
    else:
        buffer = service.render_re_registration_analysis_pdf(
            start_date, end_date, book_id, reason
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=re_registration_analysis.pdf"
            },
        )


@router.get("/registration-duration")
def get_registration_duration(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate registration duration report.

    Average time on book before dispatch or drop.
    Access: Officer+ (sensitive analytics).

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Date range (defaults to last 90 days)
        book_id: Optional book filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_registration_duration(start_date, end_date, book_id)
    elif format == "xlsx":
        buffer = service.render_registration_duration_excel(start_date, end_date, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=registration_duration.xlsx"
            },
        )
    else:
        buffer = service.render_registration_duration_pdf(start_date, end_date, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=registration_duration.pdf"
            },
        )


@router.get("/book-health-summary")
def get_book_health_summary(
    format: str = Query("pdf", pattern="^(pdf|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate book health summary report.

    Per-book dashboard stats — health indicators.
    Access: Officer+ (sensitive analytics).

    Args:
        format: Output format (pdf or json) — landscape PDF
        start_date/end_date: Period (defaults to last 30 days)
        book_id: Optional book filter (defaults to all)

    Returns:
        PDF or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_book_health_summary(start_date, end_date, book_id)
    else:
        buffer = service.render_book_health_summary_pdf(start_date, end_date, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=book_health_summary.pdf"
            },
        )


@router.get("/book-comparison")
def get_book_comparison(
    book_ids: str = Query(..., description="Comma-separated book IDs (min 2)"),
    format: str = Query("pdf", pattern="^(pdf|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate book comparison report.

    Side-by-side metrics for selected books.
    Access: Officer+ (sensitive analytics).

    Args:
        book_ids: Comma-separated book IDs (e.g., "1,2,3")
        format: Output format (pdf or json)
        start_date/end_date: Period (defaults to last 30 days)

    Returns:
        PDF or JSON response
    """
    # Parse book_ids
    try:
        ids = [int(x.strip()) for x in book_ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid book_ids format")

    if len(ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 books required")

    service = ReferralReportService(db)

    if format == "json":
        return service.get_book_comparison(ids, start_date, end_date)
    else:
        buffer = service.render_book_comparison_pdf(ids, start_date, end_date)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=book_comparison.pdf"},
        )


@router.get("/book-position/{book_id}")
def get_book_position_report(
    book_id: int,
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    tier: Optional[int] = Query(None, ge=1, le=4, description="Filter by tier"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate book position report (detailed queue).

    Full position listing for a specific book.
    CRITICAL: APN displayed as DECIMAL(10,2) — never truncated.

    Args:
        book_id: The book ID (required)
        format: Output format (pdf, xlsx, or json)
        tier: Optional tier filter
        status: Optional status filter (defaults to REGISTERED)

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        data = service.get_book_position_report(book_id, tier, status)
        if not data:
            raise HTTPException(status_code=404, detail="Book not found")
        return data
    elif format == "xlsx":
        buffer = service.render_book_position_report_excel(book_id, tier, status)
        if buffer is None:
            raise HTTPException(status_code=404, detail="Book not found")
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=book_{book_id}_position.xlsx"
            },
        )
    else:
        buffer = service.render_book_position_report_pdf(book_id, tier, status)
        if buffer is None:
            raise HTTPException(status_code=404, detail="Book not found")
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=book_{book_id}_position.pdf"
            },
        )


@router.get("/book-turnover")
def get_book_turnover(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    granularity: str = Query("weekly", pattern="^(weekly|monthly)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate book turnover report.

    Registrations in vs out by period — measures churn.
    Access: Officer+ (sensitive analytics).

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to last 90 days)
        book_id: Optional book filter
        granularity: weekly or monthly

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_book_turnover(start_date, end_date, book_id, granularity)
    elif format == "xlsx":
        buffer = service.render_book_turnover_excel(
            start_date, end_date, book_id, granularity
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=book_turnover.xlsx"},
        )
    else:
        buffer = service.render_book_turnover_pdf(
            start_date, end_date, book_id, granularity
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=book_turnover.pdf"},
        )


@router.get("/check-mark-summary")
def get_check_mark_summary(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate check mark summary report.

    Aggregate check mark statistics by book and period.
    Color coding: Yellow (1 CM), Orange (2 CM), Red (rolled off).

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to last 30 days)
        book_id: Optional book filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_check_mark_summary(start_date, end_date, book_id)
    elif format == "xlsx":
        buffer = service.render_check_mark_summary_excel(start_date, end_date, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=check_mark_summary.xlsx"
            },
        )
    else:
        buffer = service.render_check_mark_summary_pdf(start_date, end_date, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=check_mark_summary.pdf"
            },
        )


@router.get("/check-mark-trend")
def get_check_mark_trend(
    format: str = Query("pdf", pattern="^(pdf|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate check mark trend report.

    Check mark issuance over time with trend analysis.
    Access: Officer+ (sensitive analytics).

    Args:
        format: Output format (pdf or json)
        start_date/end_date: Period (min 3 months for trend, defaults to 90 days)
        book_id: Optional book filter

    Returns:
        PDF or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_check_mark_trend(start_date, end_date, book_id)
    else:
        buffer = service.render_check_mark_trend_pdf(start_date, end_date, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=check_mark_trend.pdf"},
        )


# =====================================================================
# WEEK 37 P1 REPORTS: Dispatch Operations & Employer Analytics
# =====================================================================


@router.get("/weekly-dispatch-summary")
def get_weekly_dispatch_summary(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    employer_id: Optional[int] = Query(None, description="Filter by employer ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate weekly dispatch summary report.

    Dispatches per week with breakdown by book and employer.
    Access: Staff+

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to last 4 weeks)
        book_id: Optional book filter
        employer_id: Optional employer filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_weekly_dispatch_summary(start_date, end_date, book_id, employer_id)
    elif format == "xlsx":
        buffer = service.render_weekly_dispatch_summary_excel(
            start_date, end_date, book_id, employer_id
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=weekly_dispatch_summary.xlsx"
            },
        )
    else:
        buffer = service.render_weekly_dispatch_summary_pdf(
            start_date, end_date, book_id, employer_id
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=weekly_dispatch_summary.pdf"
            },
        )


@router.get("/monthly-dispatch-summary")
def get_monthly_dispatch_summary(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate monthly dispatch summary report.

    Dispatches per month with trend indicators.
    Access: Officer+

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to last 12 months)
        book_id: Optional book filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_monthly_dispatch_summary(start_date, end_date, book_id)
    elif format == "xlsx":
        buffer = service.render_monthly_dispatch_summary_excel(start_date, end_date, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=monthly_dispatch_summary.xlsx"
            },
        )
    else:
        buffer = service.render_monthly_dispatch_summary_pdf(start_date, end_date, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=monthly_dispatch_summary.pdf"
            },
        )


@router.get("/dispatch-by-agreement-type")
def get_dispatch_by_agreement_type(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate dispatch by agreement type report.

    Breakdown of dispatches by PLA, CWA, TERO, and standard agreement types.
    Access: Officer+

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to 90 days)
        book_id: Optional book filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_dispatch_by_agreement_type(start_date, end_date, book_id)
    elif format == "xlsx":
        buffer = service.render_dispatch_by_agreement_type_excel(
            start_date, end_date, book_id
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=dispatch_by_agreement_type.xlsx"
            },
        )
    else:
        buffer = service.render_dispatch_by_agreement_type_pdf(start_date, end_date, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=dispatch_by_agreement_type.pdf"
            },
        )


@router.get("/dispatch-duration-analysis")
def get_dispatch_duration_analysis(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    employer_id: Optional[int] = Query(None, description="Filter by employer ID"),
    group_by: str = Query("book", pattern="^(book|employer|classification)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate dispatch duration analysis report.

    Average dispatch length by book, employer, or classification.
    Access: Officer+

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to 90 days)
        book_id: Optional book filter
        employer_id: Optional employer filter
        group_by: Grouping (book, employer, or classification)

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_dispatch_duration_analysis(
            start_date, end_date, book_id, employer_id, group_by
        )
    elif format == "xlsx":
        buffer = service.render_dispatch_duration_analysis_excel(
            start_date, end_date, book_id, employer_id, group_by
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=dispatch_duration_analysis.xlsx"
            },
        )
    else:
        buffer = service.render_dispatch_duration_analysis_pdf(
            start_date, end_date, book_id, employer_id, group_by
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=dispatch_duration_analysis.pdf"
            },
        )


@router.get("/short-call-analysis")
def get_short_call_analysis(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    employer_id: Optional[int] = Query(None, description="Filter by employer ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate short call analysis report.

    Short call frequency, average duration, re-registration patterns.
    Business rule: ≤3 days = treated as Long Call (Rule 9).
    Max 2 short call dispatches per registration cycle.
    Access: Staff+

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to 90 days)
        book_id: Optional book filter
        employer_id: Optional employer filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_short_call_analysis(start_date, end_date, book_id, employer_id)
    elif format == "xlsx":
        buffer = service.render_short_call_analysis_excel(
            start_date, end_date, book_id, employer_id
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=short_call_analysis.xlsx"},
        )
    else:
        buffer = service.render_short_call_analysis_pdf(
            start_date, end_date, book_id, employer_id
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=short_call_analysis.pdf"},
        )


@router.get("/employer-utilization")
def get_employer_utilization(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    employer_id: Optional[int] = Query(None, description="Filter by employer ID"),
    contract_code: Optional[str] = Query(None, description="Filter by contract code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate employer utilization report.

    Requests vs dispatches per employer — fill rate and utilization metrics.
    Color coding: Green (>90% fill), Yellow (70-90%), Red (<70%).
    Access: Officer+

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to 90 days)
        employer_id: Optional employer filter
        contract_code: Optional contract code filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_employer_utilization(
            start_date, end_date, employer_id, contract_code
        )
    elif format == "xlsx":
        buffer = service.render_employer_utilization_excel(
            start_date, end_date, employer_id, contract_code
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=employer_utilization.xlsx"
            },
        )
    else:
        buffer = service.render_employer_utilization_pdf(
            start_date, end_date, employer_id, contract_code
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=employer_utilization.pdf"},
        )


@router.get("/employer-request-patterns")
def get_employer_request_patterns(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    employer_id: Optional[int] = Query(None, description="Filter by employer ID"),
    contract_code: Optional[str] = Query(None, description="Filter by contract code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate employer request patterns report.

    Frequency, average size, and seasonal trends of employer labor requests.
    Access: Officer+

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to 6 months for trend)
        employer_id: Optional employer filter
        contract_code: Optional contract code filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_employer_request_patterns(
            start_date, end_date, employer_id, contract_code
        )
    elif format == "xlsx":
        buffer = service.render_employer_request_patterns_excel(
            start_date, end_date, employer_id, contract_code
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=employer_request_patterns.xlsx"
            },
        )
    else:
        buffer = service.render_employer_request_patterns_pdf(
            start_date, end_date, employer_id, contract_code
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=employer_request_patterns.pdf"
            },
        )


@router.get("/top-employers")
def get_top_employers(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(20, ge=5, le=100, description="Number of employers to return"),
    sort_by: str = Query("dispatches", pattern="^(dispatches|requests|fill_rate)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate top employers report.

    Ranked employers by dispatch volume, request frequency, or fill rate.
    Access: Officer+

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to 90 days)
        limit: Number of employers to return (5-100, default 20)
        sort_by: Sort metric (dispatches, requests, fill_rate)

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_top_employers(start_date, end_date, limit, sort_by)
    elif format == "xlsx":
        buffer = service.render_top_employers_excel(start_date, end_date, limit, sort_by)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=top_employers.xlsx"},
        )
    else:
        buffer = service.render_top_employers_pdf(start_date, end_date, limit, sort_by)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=top_employers.pdf"},
        )


@router.get("/employer-compliance")
def get_employer_compliance(
    format: str = Query("pdf", pattern="^(pdf|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    employer_id: Optional[int] = Query(None, description="Filter by employer ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate employer compliance report.

    Foreperson-by-name requests, agreement adherence, blackout violations.
    SENSITIVE DATA — Anti-collusion data (Rule 13), blackout (Rule 12).
    Access: Officer+ only (no Excel export — sensitive).

    Args:
        format: Output format (pdf or json only)
        start_date/end_date: Period (defaults to 90 days)
        employer_id: Optional employer filter

    Returns:
        PDF or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_employer_compliance(start_date, end_date, employer_id)
    else:
        buffer = service.render_employer_compliance_pdf(start_date, end_date, employer_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=employer_compliance.pdf"},
        )


@router.get("/member-dispatch-frequency")
def get_member_dispatch_frequency(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    min_dispatches: int = Query(0, ge=0, description="Minimum dispatch threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate member dispatch frequency report.

    Dispatch count per member over period — identifies patterns and outliers.
    Access: Officer+ (member names visible).

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to 90 days)
        book_id: Optional book filter
        min_dispatches: Minimum dispatch count threshold

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_member_dispatch_frequency(
            start_date, end_date, book_id, min_dispatches
        )
    elif format == "xlsx":
        buffer = service.render_member_dispatch_frequency_excel(
            start_date, end_date, book_id, min_dispatches
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=member_dispatch_frequency.xlsx"
            },
        )
    else:
        buffer = service.render_member_dispatch_frequency_pdf(
            start_date, end_date, book_id, min_dispatches
        )
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=member_dispatch_frequency.pdf"
            },
        )


# =========================================================================
# WEEK 38 P1 REPORTS: Compliance, Operational & Cross-Book Analytics
# =========================================================================


@router.get("/internet-bidding-activity")
def get_internet_bidding_activity(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    member_id: Optional[int] = Query(None, description="Filter by member ID"),
    status: Optional[str] = Query(None, description="Filter by status (accepted/rejected/pending)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate internet bidding activity report.

    Tracks web bid submissions, acceptances, rejections, and ban tracking.
    Business rule: Rule 8 — 5:30 PM to 7:00 AM window. 2nd rejection in 12 months = lose privileges 1 year.
    Access: Staff+

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to 90 days)
        member_id: Optional member filter
        status: Optional status filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_internet_bidding_activity(start_date, end_date, member_id, status)
    elif format == "xlsx":
        buffer = service.render_internet_bidding_activity_excel(start_date, end_date, member_id, status)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=internet_bidding_activity.xlsx"},
        )
    else:
        buffer = service.render_internet_bidding_activity_pdf(start_date, end_date, member_id, status)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=internet_bidding_activity.pdf"},
        )


@router.get("/exempt-status")
def get_exempt_status_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    snapshot_date: Optional[date] = Query(None, description="Snapshot date (YYYY-MM-DD)"),
    exempt_type: Optional[str] = Query(None, description="Filter by exempt type"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate exempt status report.

    Members currently on exempt status by type.
    Business rule: Rule 14 — exempt members retain position but are not eligible for dispatch.
    Access: Staff+

    Args:
        format: Output format (pdf, xlsx, or json)
        snapshot_date: Snapshot date (defaults to today)
        exempt_type: Optional exempt type filter
        book_id: Optional book filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_exempt_status_report(snapshot_date, exempt_type, book_id)
    elif format == "xlsx":
        buffer = service.render_exempt_status_report_excel(snapshot_date, exempt_type, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=exempt_status.xlsx"},
        )
    else:
        buffer = service.render_exempt_status_report_pdf(snapshot_date, exempt_type, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=exempt_status.pdf"},
        )


@router.get("/penalty-report")
def get_penalty_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    penalty_type: Optional[str] = Query(None, description="Filter by penalty type"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate penalty report.

    All penalty actions over period — check marks, bid rejections, quit/discharge roll-offs.
    Access: Officer+ (sensitive compliance data)

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to 90 days)
        penalty_type: Optional penalty type filter
        book_id: Optional book filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_penalty_report(start_date, end_date, penalty_type, book_id)
    elif format == "xlsx":
        buffer = service.render_penalty_report_excel(start_date, end_date, penalty_type, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=penalty_report.xlsx"},
        )
    else:
        buffer = service.render_penalty_report_pdf(start_date, end_date, penalty_type, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=penalty_report.pdf"},
        )


@router.get("/foreperson-by-name-audit")
def get_foreperson_by_name_audit(
    format: str = Query("pdf", pattern="^(pdf|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    employer_id: Optional[int] = Query(None, description="Filter by employer ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate foreperson by-name audit report.

    By-name request tracking for anti-collusion compliance review.
    Business rules: Rule 13 — anti-collusion. Rule 12 — 2-week blackout after quit/discharge.
    SENSITIVE: Officer+ only. PDF only (no Excel export).

    Args:
        format: Output format (pdf or json only)
        start_date/end_date: Period (defaults to 90 days)
        employer_id: Optional employer filter

    Returns:
        PDF or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_foreperson_by_name_audit(start_date, end_date, employer_id)
    else:
        buffer = service.render_foreperson_by_name_audit_pdf(start_date, end_date, employer_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=foreperson_by_name_audit.pdf"},
        )


@router.get("/queue-wait-time")
def get_queue_wait_time_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    snapshot_date: Optional[date] = Query(None, description="Snapshot date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate queue wait time report.

    Average wait time by book — identifies bottlenecks and longest-waiting members.
    Access: Staff+

    Args:
        format: Output format (pdf, xlsx, or json)
        snapshot_date: Snapshot date (defaults to today)
        book_id: Optional book filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_queue_wait_time_report(snapshot_date, book_id)
    elif format == "xlsx":
        buffer = service.render_queue_wait_time_report_excel(snapshot_date, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=queue_wait_time.xlsx"},
        )
    else:
        buffer = service.render_queue_wait_time_report_pdf(snapshot_date, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=queue_wait_time.pdf"},
        )


@router.get("/morning-referral-history")
def get_morning_referral_history(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate morning referral history report.

    Historical log of morning referral processing — what was dispatched each morning.
    Business rule: Rule 2 — processing order: Wire 8:30 AM → S&C 9:00 AM → Tradeshow 9:30 AM.
    Access: Staff+

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to 2 weeks)
        book_id: Optional book filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_morning_referral_history(start_date, end_date, book_id)
    elif format == "xlsx":
        buffer = service.render_morning_referral_history_excel(start_date, end_date, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=morning_referral_history.xlsx"},
        )
    else:
        buffer = service.render_morning_referral_history_pdf(start_date, end_date, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=morning_referral_history.pdf"},
        )


@router.get("/unfilled-requests")
def get_unfilled_request_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status (unfilled/partially_filled)"),
    employer_id: Optional[int] = Query(None, description="Filter by employer ID"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate unfilled request report.

    Labor requests not fully filled — aging analysis and root cause.
    Access: Staff+

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to 30 days)
        status: Optional status filter
        employer_id: Optional employer filter
        book_id: Optional book filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_unfilled_request_report(start_date, end_date, status, employer_id, book_id)
    elif format == "xlsx":
        buffer = service.render_unfilled_request_report_excel(start_date, end_date, status, employer_id, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=unfilled_requests.xlsx"},
        )
    else:
        buffer = service.render_unfilled_request_report_pdf(start_date, end_date, status, employer_id, book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=unfilled_requests.pdf"},
        )


@router.get("/referral-agent-activity")
def get_referral_agent_activity(
    format: str = Query("pdf", pattern="^(pdf|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    staff_member_id: Optional[int] = Query(None, description="Filter by staff member ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate referral agent activity report.

    Dispatches processed per staff member — workload distribution.
    Access: Officer+ (performance data). PDF only (no Excel export).

    Args:
        format: Output format (pdf or json only)
        start_date/end_date: Period (defaults to 30 days)
        staff_member_id: Optional staff filter

    Returns:
        PDF or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_referral_agent_activity(start_date, end_date, staff_member_id)
    else:
        buffer = service.render_referral_agent_activity_pdf(start_date, end_date, staff_member_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=referral_agent_activity.pdf"},
        )


@router.get("/multi-book-members")
def get_multi_book_members(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    snapshot_date: Optional[date] = Query(None, description="Snapshot date (YYYY-MM-DD)"),
    min_books: int = Query(2, ge=2, description="Minimum number of books"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate multi-book members report.

    Members registered on multiple books simultaneously — validates cross-classification rules.
    Business rule: Rule 5 — one registration per classification. Multiple classifications allowed.
    CRITICAL: Display APN as DECIMAL(10,2) — never truncate.
    Access: Staff+

    Args:
        format: Output format (pdf, xlsx, or json)
        snapshot_date: Snapshot date (defaults to today)
        min_books: Minimum book count threshold

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_multi_book_members(snapshot_date, min_books)
    elif format == "xlsx":
        buffer = service.render_multi_book_members_excel(snapshot_date, min_books)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=multi_book_members.xlsx"},
        )
    else:
        buffer = service.render_multi_book_members_pdf(snapshot_date, min_books)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=multi_book_members.pdf"},
        )


@router.get("/book-transfers")
def get_book_transfer_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx|json)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    source_book_id: Optional[int] = Query(None, description="Filter by source book ID"),
    destination_book_id: Optional[int] = Query(None, description="Filter by destination book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate book transfer report.

    Members who moved between books — re-registration patterns after dispatch/drop.
    Access: Officer+

    Args:
        format: Output format (pdf, xlsx, or json)
        start_date/end_date: Period (defaults to 90 days)
        source_book_id: Optional source book filter
        destination_book_id: Optional destination book filter

    Returns:
        PDF, Excel, or JSON response
    """
    service = ReferralReportService(db)

    if format == "json":
        return service.get_book_transfer_report(start_date, end_date, source_book_id, destination_book_id)
    elif format == "xlsx":
        buffer = service.render_book_transfer_report_excel(start_date, end_date, source_book_id, destination_book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=book_transfers.xlsx"},
        )
    else:
        buffer = service.render_book_transfer_report_pdf(start_date, end_date, source_book_id, destination_book_id)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=book_transfers.pdf"},
        )


# ========================================
# WEEK 40: P2 BATCH 1 - REGISTRATION & BOOK ANALYTICS (12 endpoints)
# ========================================


@router.get("/registration-aging")
def get_registration_aging_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    as_of_date: Optional[date] = Query(None, description="As-of date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Registration Aging Report — Duration buckets per book.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_registration_aging_report(format, book_id, as_of_date)

    filename = f"registration_aging.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/registration-turnover")
def get_registration_turnover_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Registration Turnover Report — In vs out per period.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_registration_turnover_report(format, start_date, end_date, book_id)

    filename = f"registration_turnover.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/re-sign-compliance")
def get_re_sign_compliance_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-Sign Compliance Report — Rule 7 analytics.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_re_sign_compliance_report(format, book_id, start_date, end_date)

    filename = f"re_sign_compliance.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/re-registration-patterns")
def get_re_registration_patterns_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-Registration Pattern Analysis — Rule 6 trigger analysis.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_re_registration_patterns_report(format, start_date, end_date, book_id)

    filename = f"re_registration_patterns.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/inactive-registrations")
def get_inactive_registrations_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    inactive_days: int = Query(60, description="Inactivity threshold in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Inactive Registration Report — Stale registrations.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_inactive_registrations_report(format, book_id, inactive_days)

    filename = f"inactive_registrations.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/cross-book-registration")
def get_cross_book_registration_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cross-Book Registration Analysis — Multi-book members (Rule 5).

    Access: Officer+
    """
    service = ReferralReportService(db)
    result = service.generate_cross_book_registration_report(format)

    filename = f"cross_book_registration.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/classification-demand-gap")
def get_classification_demand_gap_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Classification Demand Gap — Supply vs demand.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_classification_demand_gap_report(format, start_date, end_date)

    filename = f"classification_demand_gap.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/book-comparison-dashboard")
def get_book_comparison_dashboard_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Book Comparison Dashboard — Cross-book metrics.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_book_comparison_report(format)

    filename = f"book_comparison.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/tier-distribution")
def get_tier_distribution_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tier Distribution Report — Book tier breakdown.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_tier_distribution_report(format)

    filename = f"tier_distribution.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/book-capacity-trends")
def get_book_capacity_trends_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    period: str = Query("weekly", pattern="^(weekly|monthly)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Book Capacity Trends — Registration trends.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_book_capacity_trends_report(format, book_id, period)

    filename = f"book_capacity_trends.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/apn-wait-time")
def get_apn_wait_time_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """APN Wait Time Distribution — Wait time histogram.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_apn_wait_time_report(format, book_id)

    filename = f"apn_wait_time.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/seasonal-registration")
def get_seasonal_registration_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    year: Optional[int] = Query(None, description="Year (YYYY)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seasonal Registration Patterns — Seasonal patterns.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_seasonal_registration_report(format, year)

    filename = f"seasonal_registration.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ========================================
# WEEK 41: P2 BATCH 2 - DISPATCH & ANALYTICS (19 endpoints)
# ========================================


@router.get("/dispatch-success-rate")
def get_dispatch_success_rate_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dispatch Success Rate Report — Fill completion metrics.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_dispatch_success_rate_report(format, start_date, end_date, book_id)

    filename = f"dispatch_success_rate.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/time-to-fill")
def get_time_to_fill_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Time-to-Fill Analysis — Average days to fill requests.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_time_to_fill_report(format, start_date, end_date, book_id)

    filename = f"time_to_fill.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/dispatch-method-comparison")
def get_dispatch_method_comparison_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dispatch Method Comparison — Web bid vs phone vs walk-in.

    Access: Officer+
    """
    service = ReferralReportService(db)
    result = service.generate_dispatch_method_comparison_report(format, start_date, end_date)

    filename = f"dispatch_method_comparison.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/dispatch-geographic")
def get_dispatch_geographic_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Geographic Distribution — Dispatches by region and location.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_dispatch_geographic_report(format, start_date, end_date)

    filename = f"dispatch_geographic.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/termination-reason-analysis")
def get_termination_reason_analysis_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Termination Reason Analysis — Dispatch end reasons and patterns.

    Access: Officer+
    """
    service = ReferralReportService(db)
    result = service.generate_termination_reason_analysis_report(format, start_date, end_date, book_id)

    filename = f"termination_reason_analysis.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/return-dispatch")
def get_return_dispatch_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    employer_id: Optional[int] = Query(None, description="Filter by employer ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return Dispatch Report — Members returning to same employer.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_return_dispatch_report(format, start_date, end_date, employer_id)

    filename = f"return_dispatch.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/employer-growth-trends")
def get_employer_growth_trends_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    contract_code: Optional[str] = Query(None, description="Filter by contract code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Employer Growth Trends — New and growing employers.

    Access: Officer+ only
    """
    service = ReferralReportService(db)
    result = service.generate_employer_growth_trends_report(format, start_date, end_date, contract_code)

    filename = f"employer_growth_trends.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/employer-workforce-size")
def get_employer_workforce_size_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Employer Workforce Size — Dispatch counts per employer.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_employer_workforce_size_report(format)

    filename = f"employer_workforce_size.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/new-employer-activity")
def get_new_employer_activity_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """New Employer Activity — First-time employers.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_new_employer_activity_report(format, start_date, end_date)

    filename = f"new_employer_activity.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/contract-code-utilization")
def get_contract_code_utilization_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Contract Code Utilization — Dispatch volume by contract type.

    Access: Officer+
    """
    service = ReferralReportService(db)
    result = service.generate_contract_code_utilization_report(format, start_date, end_date)

    filename = f"contract_code_utilization.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/queue-velocity")
def get_queue_velocity_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Queue Velocity Report — Position movement rate per book.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_queue_velocity_report(format, book_id)

    filename = f"queue_velocity.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/peak-demand")
def get_peak_demand_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Peak Demand Analysis — Demand spikes and patterns.

    Access: Officer+
    """
    service = ReferralReportService(db)
    result = service.generate_peak_demand_report(format, start_date, end_date)

    filename = f"peak_demand.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/check-mark-patterns")
def get_check_mark_patterns_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check Mark Pattern Analysis — Rule 10 enforcement tracking.

    Access: Officer+ (sensitive)
    """
    service = ReferralReportService(db)
    result = service.generate_check_mark_patterns_report(format, start_date, end_date, book_id)

    filename = f"check_mark_patterns.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/check-mark-exceptions")
def get_check_mark_exceptions_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check Mark Exceptions Report — Rule 11 exemptions.

    Access: Officer+
    """
    service = ReferralReportService(db)
    result = service.generate_check_mark_exceptions_report(format, start_date, end_date, book_id)

    filename = f"check_mark_exceptions.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/internet-bidding-analytics")
def get_internet_bidding_analytics_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Internet Bidding Analytics — Rule 8 compliance metrics.

    Access: Officer+
    """
    service = ReferralReportService(db)
    result = service.generate_internet_bidding_analytics_report(format, start_date, end_date, book_id)

    filename = f"internet_bidding_analytics.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/exemption-status")
def get_exemption_status_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    snapshot_date: Optional[date] = Query(None, description="Snapshot date (YYYY-MM-DD)"),
    exemption_type: Optional[str] = Query(None, description="Filter by exemption type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exemption Status Report — Rule 14 exemptions.

    Access: Staff+
    """
    service = ReferralReportService(db)
    result = service.generate_exemption_status_report(format, snapshot_date, exemption_type)

    filename = f"exemption_status.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/agreement-type-performance")
def get_agreement_type_performance_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Agreement Type Performance — Rule 4 (PLA/CWA/TERO) metrics.

    Access: Officer+ only
    """
    service = ReferralReportService(db)
    result = service.generate_agreement_type_performance_report(format, start_date, end_date)

    filename = f"agreement_type_performance.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/foreperson-by-name")
def get_foreperson_by_name_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    employer_id: Optional[int] = Query(None, description="Filter by employer ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Foreperson By-Name Analysis — Rule 13 anti-collusion tracking.

    Access: Officer+ only
    """
    service = ReferralReportService(db)
    result = service.generate_foreperson_by_name_report(format, start_date, end_date, employer_id)

    filename = f"foreperson_by_name.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/blackout-period-tracking")
def get_blackout_period_tracking_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    member_id: Optional[int] = Query(None, description="Filter by member ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Blackout Period Tracking — Rule 12 enforcement.

    Access: Officer+ only
    """
    service = ReferralReportService(db)
    result = service.generate_blackout_period_tracking_report(format, start_date, end_date, member_id)

    filename = f"blackout_period_tracking.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ========================================
# WEEK 42: P3 REPORTS - PROJECTIONS & ANALYTICS (10 endpoints)
# ========================================


@router.get("/workforce-projection")
def get_workforce_projection(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    projection_months: int = Query(6, ge=1, le=24, description="Months to project ahead"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Workforce Projection — Predictive staffing levels by book.

    Access: Officer+ only
    """
    service = ReferralReportService(db)
    result = service.generate_workforce_projection_report(format, projection_months)

    filename = f"workforce_projection.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/dispatch-forecast")
def get_dispatch_forecast(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    forecast_weeks: int = Query(12, ge=1, le=52, description="Weeks to forecast"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dispatch Volume Forecast — Expected dispatch trends.

    Access: Officer+ only
    """
    service = ReferralReportService(db)
    result = service.generate_dispatch_forecast_report(format, forecast_weeks)

    filename = f"dispatch_forecast.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/book-demand-forecast")
def get_book_demand_forecast(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    forecast_period: int = Query(90, ge=1, le=365, description="Days to forecast"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Book Demand Forecast — Predicted labor request volume per book.

    Access: Officer+ only
    """
    service = ReferralReportService(db)
    result = service.generate_book_demand_forecast_report(format, forecast_period)

    filename = f"book_demand_forecast.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/member-availability-index")
def get_member_availability_index(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    as_of_date: Optional[date] = Query(None, description="As-of date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Member Availability Index — Real-time member supply metrics.

    Access: Staff+ only
    """
    service = ReferralReportService(db)
    result = service.generate_member_availability_index_report(format, as_of_date)

    filename = f"member_availability_index.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/employer-loyalty-score")
def get_employer_loyalty_score(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    lookback_days: int = Query(365, ge=30, le=1095, description="Historical period for scoring"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Employer Loyalty Score — Repeat usage frequency and reliability.

    Access: Officer+ only
    """
    service = ReferralReportService(db)
    result = service.generate_employer_loyalty_score_report(format, lookback_days)

    filename = f"employer_loyalty_score.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/member-journey/{member_id}")
def get_member_journey(
    member_id: int,
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Member Journey Report — Complete career arc and dispatch history.

    Access: Officer+ only
    """
    service = ReferralReportService(db)
    result = service.generate_member_journey_report(member_id, format)

    if result is None:
        raise HTTPException(status_code=404, detail="Member not found")

    filename = f"member_journey_{member_id}.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/comparative-book-performance")
def get_comparative_book_performance(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Comparative Book Performance — Side-by-side metrics across all books.

    Access: Staff+ only
    """
    service = ReferralReportService(db)
    result = service.generate_comparative_book_performance_report(format, start_date, end_date)

    filename = f"comparative_book_performance.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/custom-export")
def get_custom_export(
    entity_type: str = Query("dispatch", description="Entity type: dispatch, registration, member, employer"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Custom Date Range Export — Flexible Excel export by entity type.

    Access: Staff+ only
    """
    service = ReferralReportService(db)
    result = service.generate_custom_export_report(entity_type, start_date, end_date)

    if result is None:
        raise HTTPException(status_code=400, detail="Invalid entity type or date range")

    filename = f"custom_export_{entity_type}_{start_date or 'all'}.xlsx"

    return StreamingResponse(
        BytesIO(result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/annual-summary")
def get_annual_summary(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    year: Optional[int] = Query(None, description="Year (defaults to current year)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Annual Operations Summary — Year-over-year performance snapshot.

    Access: Officer+ only
    """
    service = ReferralReportService(db)
    result = service.generate_annual_summary_report(format, year)

    filename = f"annual_summary_{year or 'current'}.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/data-quality")
def get_data_quality_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Data Quality Report — Audit completeness and integrity metrics.

    Access: Admin only
    """
    service = ReferralReportService(db)
    result = service.generate_data_quality_report(format)

    filename = f"data_quality.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return StreamingResponse(
        BytesIO(result),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ========================================
# WEEK 42: P3 - PROJECTION, INTELLIGENCE & ADMIN (10 endpoints)
# ========================================


@router.get("/workforce-projection")
def get_workforce_projection_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    projection_days: int = Query(90, ge=30, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Workforce Projection — Queue level projections. Access: Officer+"""
    service = ReferralReportService(db)
    result = service.generate_workforce_projection_report(format, projection_days)
    filename = f"workforce_projection.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(BytesIO(result), media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/dispatch-forecast")
def get_dispatch_forecast_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dispatch Volume Forecast. Access: Officer+"""
    service = ReferralReportService(db)
    result = service.generate_dispatch_forecast_report(format)
    filename = f"dispatch_forecast.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(BytesIO(result), media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/book-demand-forecast")
def get_book_demand_forecast_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    book_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Book Demand Forecast. Access: Officer+"""
    service = ReferralReportService(db)
    result = service.generate_book_demand_forecast_report(format, book_id)
    filename = f"book_demand_forecast.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(BytesIO(result), media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/member-availability-index")
def get_member_availability_index_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Member Availability Index. Access: Staff+"""
    service = ReferralReportService(db)
    result = service.generate_member_availability_index_report(format)
    filename = f"member_availability_index.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(BytesIO(result), media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/employer-loyalty-score")
def get_employer_loyalty_score_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Employer Loyalty Score. Access: Officer+"""
    service = ReferralReportService(db)
    result = service.generate_employer_loyalty_score_report(format)
    filename = f"employer_loyalty_score.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(BytesIO(result), media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/member-journey")
def get_member_journey_report(
    member_id: int = Query(..., description="Member ID"),
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Member Journey Report. Access: Officer+"""
    service = ReferralReportService(db)
    result = service.generate_member_journey_report(format, member_id)
    filename = f"member_journey_{member_id}.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(BytesIO(result), media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/comparative-book-performance")
def get_comparative_book_performance_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Comparative Book Performance. Access: Staff+"""
    service = ReferralReportService(db)
    result = service.generate_comparative_book_performance_report(format)
    filename = f"comparative_book_performance.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(BytesIO(result), media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/custom-export")
def get_custom_export_report(
    entity_type: str = Query(..., pattern="^(members|registrations|dispatches)$"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    book_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Custom Date Range Export. Access: Staff+"""
    service = ReferralReportService(db)
    result = service.generate_custom_export_report("xlsx", entity_type, start_date, end_date, book_id)
    filename = f"custom_export_{entity_type}.xlsx"
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(BytesIO(result), media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/annual-summary")
def get_annual_summary_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Annual Operations Summary. Access: Officer+"""
    service = ReferralReportService(db)
    result = service.generate_annual_summary_report(format, year)
    filename = f"annual_summary_{year or date.today().year}.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(BytesIO(result), media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/data-quality")
def get_data_quality_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Data Quality Report. Access: Admin only"""
    service = ReferralReportService(db)
    result = service.generate_data_quality_report(format)
    filename = f"data_quality.{format}"
    media_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(BytesIO(result), media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})
