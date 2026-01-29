"""
Reports Router - PDF and Excel report generation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.session import get_db
from src.routers.dependencies.auth_cookie import require_auth
from src.services.report_service import ReportService
from src.models import Member, DuesPeriod, DuesPayment, Student, Course, Enrollment
from src.models import SALTingActivity, Grievance
from src.db.enums import MemberStatus, DuesPaymentStatus, StudentStatus, GrievanceStatus

router = APIRouter(prefix="/reports", tags=["reports"])
templates = Jinja2Templates(directory="src/templates")


def get_content_type(format: str) -> str:
    """Get content type for format."""
    if format == "pdf":
        return "application/pdf"
    elif format == "excel":
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/octet-stream"


def get_file_extension(format: str) -> str:
    """Get file extension for format."""
    if format == "pdf":
        return ".pdf"
    elif format == "excel":
        return ".xlsx"
    return ""


# ============================================================
# Reports Landing Page
# ============================================================


@router.get("", response_class=HTMLResponse)
async def reports_landing(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Reports landing page with available reports."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    reports = [
        {
            "category": "Members",
            "items": [
                {"name": "Member Roster", "url": "/reports/members/roster", "formats": ["pdf", "excel"]},
            ],
        },
        {
            "category": "Dues",
            "items": [
                {"name": "Dues Summary", "url": "/reports/dues/summary", "formats": ["pdf", "excel"]},
                {"name": "Overdue Report", "url": "/reports/dues/overdue", "formats": ["pdf", "excel"]},
            ],
        },
        {
            "category": "Training",
            "items": [
                {"name": "Course Enrollment", "url": "/reports/training/enrollment", "formats": ["excel"]},
            ],
        },
        {
            "category": "Operations",
            "items": [
                {"name": "Grievance Summary", "url": "/reports/operations/grievances", "formats": ["pdf"]},
                {"name": "SALTing Activities", "url": "/reports/operations/salting", "formats": ["excel"]},
            ],
        },
    ]

    return templates.TemplateResponse(
        "reports/index.html",
        {
            "request": request,
            "user": current_user,
            "reports": reports,
        },
    )


# ============================================================
# Member Reports
# ============================================================


@router.get("/members/roster")
async def member_roster_report(
    request: Request,
    format: str = Query("pdf", pattern="^(pdf|excel)$"),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Generate member roster report."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Query members
    stmt = select(Member).where(Member.deleted_at == None)

    if status:
        try:
            status_enum = MemberStatus(status)
            stmt = stmt.where(Member.status == status_enum)
        except ValueError:
            pass

    stmt = stmt.order_by(Member.last_name, Member.first_name)
    result = await db.execute(stmt)
    members = result.scalars().all()

    if format == "excel":
        # Excel format
        data = []
        for m in members:
            data.append({
                "member_number": m.member_number or "",
                "last_name": m.last_name,
                "first_name": m.first_name,
                "email": m.email or "",
                "phone": m.phone or "",
                "classification": m.classification.value if m.classification else "",
                "status": m.status.value if m.status else "",
                "hire_date": m.hire_date.strftime("%Y-%m-%d") if m.hire_date else "",
            })

        columns = [
            {"key": "member_number", "header": "Member #"},
            {"key": "last_name", "header": "Last Name"},
            {"key": "first_name", "header": "First Name"},
            {"key": "email", "header": "Email"},
            {"key": "phone", "header": "Phone"},
            {"key": "classification", "header": "Classification"},
            {"key": "status", "header": "Status"},
            {"key": "hire_date", "header": "Hire Date"},
        ]

        excel_bytes = ReportService.generate_excel(
            data, columns, sheet_name="Members", title="Member Roster"
        )

        filename = f"member_roster_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return Response(
            content=excel_bytes,
            media_type=get_content_type("excel"),
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    else:
        # PDF format
        html_content = templates.get_template("reports/member_roster.html").render(
            title="Member Roster",
            subtitle=f"{len(members)} members",
            generated_at=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            generated_by=current_user.get("email"),
            members=members,
            format_phone=ReportService.format_phone,
        )

        pdf_bytes = ReportService.generate_pdf(html_content)

        filename = f"member_roster_{datetime.now().strftime('%Y%m%d')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type=get_content_type("pdf"),
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


# ============================================================
# Dues Reports
# ============================================================


@router.get("/dues/summary")
async def dues_summary_report(
    request: Request,
    format: str = Query("pdf", pattern="^(pdf|excel)$"),
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Generate dues summary report by period."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Default to current year
    if not year:
        year = datetime.now().year

    # Get periods for the year
    stmt = (
        select(DuesPeriod)
        .where(DuesPeriod.period_year == year)
        .order_by(DuesPeriod.period_month)
    )
    result = await db.execute(stmt)
    periods = result.scalars().all()

    # Calculate stats for each period
    period_stats = []
    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']

    for period in periods:
        # Get payments for this period
        payments_stmt = select(DuesPayment).where(DuesPayment.period_id == period.id)
        payments_result = await db.execute(payments_stmt)
        payments = payments_result.scalars().all()

        total_due = sum(p.amount_due for p in payments) if payments else Decimal("0")
        total_paid = sum(p.amount_paid or Decimal("0") for p in payments) if payments else Decimal("0")
        member_count = len(payments)
        paid_count = sum(1 for p in payments if p.status == DuesPaymentStatus.PAID)

        period_stats.append({
            "period_name": f"{month_names[period.period_month]} {period.period_year}",
            "month": period.period_month,
            "is_closed": period.is_closed,
            "total_due": total_due,
            "total_paid": total_paid,
            "collection_rate": (total_paid / total_due * 100) if total_due > 0 else Decimal("0"),
            "member_count": member_count,
            "paid_count": paid_count,
        })

    # Calculate totals
    grand_total_due = sum(p["total_due"] for p in period_stats)
    grand_total_paid = sum(p["total_paid"] for p in period_stats)

    if format == "excel":
        data = []
        for ps in period_stats:
            data.append({
                "period": ps["period_name"],
                "status": "Closed" if ps["is_closed"] else "Open",
                "members": ps["member_count"],
                "paid_count": ps["paid_count"],
                "total_due": float(ps["total_due"]),
                "total_paid": float(ps["total_paid"]),
                "collection_rate": f"{ps['collection_rate']:.1f}%",
            })

        columns = [
            {"key": "period", "header": "Period"},
            {"key": "status", "header": "Status"},
            {"key": "members", "header": "Members"},
            {"key": "paid_count", "header": "Paid"},
            {"key": "total_due", "header": "Total Due"},
            {"key": "total_paid", "header": "Total Paid"},
            {"key": "collection_rate", "header": "Collection %"},
        ]

        excel_bytes = ReportService.generate_excel(
            data, columns, sheet_name="Dues Summary", title=f"Dues Summary - {year}"
        )

        filename = f"dues_summary_{year}.xlsx"
        return Response(
            content=excel_bytes,
            media_type=get_content_type("excel"),
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    else:
        html_content = templates.get_template("reports/dues_summary.html").render(
            title=f"Dues Summary - {year}",
            subtitle=f"{len(periods)} periods",
            generated_at=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            generated_by=current_user.get("email"),
            year=year,
            period_stats=period_stats,
            grand_total_due=grand_total_due,
            grand_total_paid=grand_total_paid,
            grand_collection_rate=(grand_total_paid / grand_total_due * 100) if grand_total_due > 0 else Decimal("0"),
            format_currency=ReportService.format_currency,
        )

        pdf_bytes = ReportService.generate_pdf(html_content)

        filename = f"dues_summary_{year}.pdf"
        return Response(
            content=pdf_bytes,
            media_type=get_content_type("pdf"),
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


@router.get("/dues/overdue")
async def overdue_report(
    request: Request,
    format: str = Query("pdf", pattern="^(pdf|excel)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Generate overdue members report."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Get overdue payments with member info
    stmt = (
        select(DuesPayment)
        .options(selectinload(DuesPayment.member), selectinload(DuesPayment.period))
        .where(DuesPayment.status == DuesPaymentStatus.OVERDUE)
    )
    result = await db.execute(stmt)
    overdue_payments = result.scalars().all()

    # Sort by member name
    overdue_payments = sorted(
        overdue_payments,
        key=lambda p: (p.member.last_name if p.member else "", p.member.first_name if p.member else "")
    )

    if format == "excel":
        data = []
        for payment in overdue_payments:
            member = payment.member
            period = payment.period
            data.append({
                "member_number": member.member_number or "" if member else "",
                "name": f"{member.last_name}, {member.first_name}" if member else "",
                "email": member.email or "" if member else "",
                "phone": member.phone or "" if member else "",
                "period": f"{period.period_month}/{period.period_year}" if period else "",
                "amount_due": float(payment.amount_due),
                "amount_paid": float(payment.amount_paid or 0),
                "balance": float(payment.amount_due - (payment.amount_paid or 0)),
            })

        columns = [
            {"key": "member_number", "header": "Member #"},
            {"key": "name", "header": "Name"},
            {"key": "email", "header": "Email"},
            {"key": "phone", "header": "Phone"},
            {"key": "period", "header": "Period"},
            {"key": "amount_due", "header": "Amount Due"},
            {"key": "amount_paid", "header": "Amount Paid"},
            {"key": "balance", "header": "Balance"},
        ]

        excel_bytes = ReportService.generate_excel(
            data, columns, sheet_name="Overdue", title="Overdue Members Report"
        )

        filename = f"overdue_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return Response(
            content=excel_bytes,
            media_type=get_content_type("excel"),
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    else:
        # Calculate totals
        total_overdue = sum(
            p.amount_due - (p.amount_paid or Decimal("0"))
            for p in overdue_payments
        )

        html_content = templates.get_template("reports/overdue_report.html").render(
            title="Overdue Members Report",
            subtitle=f"{len(overdue_payments)} overdue payments",
            generated_at=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            generated_by=current_user.get("email"),
            overdue_payments=overdue_payments,
            total_overdue=total_overdue,
            format_currency=ReportService.format_currency,
            format_phone=ReportService.format_phone,
        )

        pdf_bytes = ReportService.generate_pdf(html_content)

        filename = f"overdue_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type=get_content_type("pdf"),
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


# ============================================================
# Training Reports
# ============================================================


@router.get("/training/enrollment")
async def training_enrollment_report(
    request: Request,
    format: str = Query("excel", pattern="^(excel)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Generate course enrollment report."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Get courses with enrollment counts
    stmt = select(Course).order_by(Course.course_code)
    result = await db.execute(stmt)
    courses = result.scalars().all()

    data = []
    for course in courses:
        # Count enrollments
        enrollment_stmt = select(func.count(Enrollment.id)).where(Enrollment.course_id == course.id)
        enrollment_result = await db.execute(enrollment_stmt)
        enrollment_count = enrollment_result.scalar() or 0

        data.append({
            "course_code": course.course_code,
            "course_name": course.course_name,
            "description": course.description or "",
            "credits": course.credits or 0,
            "enrollment_count": enrollment_count,
            "status": "Active" if course.is_active else "Inactive",
        })

    columns = [
        {"key": "course_code", "header": "Course Code"},
        {"key": "course_name", "header": "Course Name"},
        {"key": "description", "header": "Description"},
        {"key": "credits", "header": "Credits"},
        {"key": "enrollment_count", "header": "Enrolled"},
        {"key": "status", "header": "Status"},
    ]

    excel_bytes = ReportService.generate_excel(
        data, columns, sheet_name="Enrollments", title="Course Enrollment Report"
    )

    filename = f"enrollment_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return Response(
        content=excel_bytes,
        media_type=get_content_type("excel"),
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ============================================================
# Operations Reports
# ============================================================


@router.get("/operations/grievances")
async def grievance_report(
    request: Request,
    format: str = Query("pdf", pattern="^(pdf)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Generate grievance summary report."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Get all grievances
    stmt = select(Grievance).options(selectinload(Grievance.member)).order_by(Grievance.filed_date.desc())
    result = await db.execute(stmt)
    grievances = result.scalars().all()

    # Count by status
    status_counts = {}
    for g in grievances:
        status = g.status.value if g.status else "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1

    html_content = templates.get_template("reports/grievance_summary.html").render(
        title="Grievance Summary Report",
        subtitle=f"{len(grievances)} total grievances",
        generated_at=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        generated_by=current_user.get("email"),
        grievances=grievances,
        status_counts=status_counts,
        format_date=ReportService.format_date,
    )

    pdf_bytes = ReportService.generate_pdf(html_content)

    filename = f"grievance_report_{datetime.now().strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type=get_content_type("pdf"),
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/operations/salting")
async def salting_report(
    request: Request,
    format: str = Query("excel", pattern="^(excel)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Generate SALTing activities report."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    # Get all SALTing activities
    stmt = select(SALTingActivity).options(
        selectinload(SALTingActivity.member),
        selectinload(SALTingActivity.organization)
    ).order_by(SALTingActivity.activity_date.desc())
    result = await db.execute(stmt)
    activities = result.scalars().all()

    data = []
    for activity in activities:
        data.append({
            "date": activity.activity_date.strftime("%Y-%m-%d") if activity.activity_date else "",
            "member": f"{activity.member.last_name}, {activity.member.first_name}" if activity.member else "",
            "organization": activity.organization.name if activity.organization else "",
            "activity_type": activity.activity_type.value if activity.activity_type else "",
            "outcome": activity.outcome.value if activity.outcome else "",
            "notes": activity.notes or "",
        })

    columns = [
        {"key": "date", "header": "Date"},
        {"key": "member", "header": "Member"},
        {"key": "organization", "header": "Organization"},
        {"key": "activity_type", "header": "Activity Type"},
        {"key": "outcome", "header": "Outcome"},
        {"key": "notes", "header": "Notes"},
    ]

    excel_bytes = ReportService.generate_excel(
        data, columns, sheet_name="SALTing", title="SALTing Activities Report"
    )

    filename = f"salting_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return Response(
        content=excel_bytes,
        media_type=get_content_type("excel"),
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
