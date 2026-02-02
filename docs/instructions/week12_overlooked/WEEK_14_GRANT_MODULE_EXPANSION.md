# Week 14: Grant Module Expansion & Compliance Reporting

**Version:** 1.0.0  
**Created:** February 1, 2026  
**Branch:** `develop`  
**Estimated Effort:** 8-10 hours (3-4 sessions)  
**Dependencies:** Week 13 (IP2A Entity Completion) should be reviewed first

---

## Overview

The original IP2A vision emphasized **grant tracking and compliance** as a core feature. While the `Grant` model exists, this instruction ensures full grant lifecycle management including:

- Student enrollment tracking per grant
- Progress/outcome tracking per student per grant
- Compliance report generation
- Funder-specific report formats
- Budget vs. actual expense tracking

### Why This Matters

> "Grant compliance reporting is mandatory for continued funding. External funders require specific data formats and outcome metrics."
> — IP2A Mission & Constraints (ChatGPT Transfer)

---

## Pre-Flight Checklist

- [ ] On `develop` branch
- [ ] Week 13 entity audit reviewed (Location, InstructorHours, ToolCheckout, GrantExpense)
- [ ] All tests passing (`pytest -v`)
- [ ] Docker services running
- [ ] Reviewed existing `Grant` model in `src/models/`
- [ ] Reviewed existing grant-related services

---

## Current State Assessment

### Existing Grant Infrastructure

Before implementing, verify current state:

```bash
# Find all grant-related files
find src/ -name "*grant*" -type f

# Check Grant model
cat src/models/grant.py

# Check existing schemas
cat src/schemas/grant.py

# Check existing services
cat src/services/grant_service.py

# Check existing routes
grep -r "grant" src/routers/
```

### Expected Findings

| Component | Expected | Action if Missing |
|-----------|----------|-------------------|
| `Grant` model | ✅ Exists | — |
| `GrantEnrollment` model | ❓ Verify | Create in Phase 2 |
| `GrantExpense` model | ❓ From Week 13 | Verify complete |
| Grant reporting service | ❓ Likely missing | Create in Phase 4 |
| Funder report templates | ❓ Likely missing | Create in Phase 5 |

---

## Phase 1: Grant Model Enhancement

### 1.1 Review Required Fields

The Grant model should support:

```python
# Verify these fields exist in src/models/grant.py

class Grant(Base):
    __tablename__ = "grants"
    
    id: Mapped[int]
    
    # Basic Info
    name: Mapped[str]  # "DOL Pre-Apprenticeship Grant FY2024"
    funder_name: Mapped[str]  # "Department of Labor"
    grant_number: Mapped[str | None]  # Funder's reference number
    
    # Financials
    total_amount: Mapped[Decimal]  # Total grant award
    
    # Dates
    start_date: Mapped[date]
    end_date: Mapped[date]
    
    # Status
    status: Mapped[GrantStatus]  # PENDING, ACTIVE, COMPLETED, CLOSED
    
    # Targets/Goals
    target_enrollment: Mapped[int | None]  # Target number of students
    target_completion: Mapped[int | None]  # Target completions
    target_placement: Mapped[int | None]  # Target job placements
    
    # Reporting
    reporting_frequency: Mapped[str | None]  # "monthly", "quarterly", "annually"
    next_report_due: Mapped[date | None]
    
    # Metadata
    notes: Mapped[str | None]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

### 1.2 Add Missing Fields via Migration

If fields are missing, create migration:

```bash
alembic revision --autogenerate -m "enhance_grant_model_targets_reporting"
```

---

## Phase 2: Grant Enrollment Tracking

### 2.1 GrantEnrollment Model

Create association between Grants and Students with outcome tracking:

```python
# src/models/grant_enrollment.py
"""Track student enrollment and outcomes per grant."""
from datetime import datetime, date
from typing import TYPE_CHECKING
from sqlalchemy import String, Date, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.enums import GrantEnrollmentStatus, GrantOutcome

if TYPE_CHECKING:
    from src.models.grant import Grant
    from src.models.student import Student


class GrantEnrollment(Base):
    """Links students to grants with outcome tracking."""
    
    __tablename__ = "grant_enrollments"
    __table_args__ = (
        UniqueConstraint('grant_id', 'student_id', name='uq_grant_student'),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True)
    grant_id: Mapped[int] = mapped_column(
        ForeignKey("grants.id"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"), nullable=False
    )
    
    # Enrollment tracking
    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[GrantEnrollmentStatus] = mapped_column(
        default=GrantEnrollmentStatus.ENROLLED
    )
    
    # Outcome tracking (for compliance reporting)
    completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    outcome: Mapped[GrantOutcome | None] = mapped_column(nullable=True)
    outcome_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Placement tracking (if job placement is a metric)
    placement_employer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    placement_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    placement_wage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Additional data
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    grant: Mapped["Grant"] = relationship(back_populates="enrollments")
    student: Mapped["Student"] = relationship(back_populates="grant_enrollments")
```

### 2.2 Add Enums

```python
# Add to src/db/enums/__init__.py

class GrantStatus(str, Enum):
    """Status of a grant."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CLOSED = "closed"


class GrantEnrollmentStatus(str, Enum):
    """Status of student enrollment in a grant."""
    ENROLLED = "enrolled"
    ACTIVE = "active"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"
    DROPPED = "dropped"


class GrantOutcome(str, Enum):
    """Outcome for grant compliance reporting."""
    COMPLETED_PROGRAM = "completed_program"
    OBTAINED_CREDENTIAL = "obtained_credential"
    ENTERED_APPRENTICESHIP = "entered_apprenticeship"
    OBTAINED_EMPLOYMENT = "obtained_employment"
    CONTINUED_EDUCATION = "continued_education"
    WITHDRAWN = "withdrawn"
    OTHER = "other"
```

### 2.3 Update Student Model

```python
# Add to src/models/student.py
grant_enrollments: Mapped[list["GrantEnrollment"]] = relationship(
    back_populates="student"
)
```

### 2.4 Update Grant Model

```python
# Add to src/models/grant.py
enrollments: Mapped[list["GrantEnrollment"]] = relationship(
    back_populates="grant"
)
expenses: Mapped[list["GrantExpense"]] = relationship(
    back_populates="grant"
)
```

---

## Phase 3: Grant Service Enhancement

### 3.1 Grant Metrics Service

Create `src/services/grant_metrics_service.py`:

```python
"""Grant metrics and reporting service."""
from datetime import date
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.grant import Grant
from src.models.grant_enrollment import GrantEnrollment
from src.models.grant_expense import GrantExpense
from src.db.enums import GrantEnrollmentStatus, GrantOutcome


class GrantMetricsService:
    """Service for calculating grant metrics and compliance data."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_grant_summary(self, grant_id: int) -> dict:
        """Get comprehensive summary for a grant."""
        grant = await self.db.get(Grant, grant_id)
        if not grant:
            return None
        
        # Enrollment metrics
        enrollment_stats = await self._get_enrollment_stats(grant_id)
        
        # Financial metrics
        financial_stats = await self._get_financial_stats(grant_id)
        
        # Outcome metrics
        outcome_stats = await self._get_outcome_stats(grant_id)
        
        return {
            "grant_id": grant_id,
            "grant_name": grant.name,
            "funder": grant.funder_name,
            "period": {
                "start": grant.start_date,
                "end": grant.end_date,
            },
            "enrollment": enrollment_stats,
            "financials": financial_stats,
            "outcomes": outcome_stats,
            "targets": {
                "enrollment": grant.target_enrollment,
                "completion": grant.target_completion,
                "placement": grant.target_placement,
            },
            "progress": self._calculate_progress(
                enrollment_stats, outcome_stats, grant
            ),
        }
    
    async def _get_enrollment_stats(self, grant_id: int) -> dict:
        """Calculate enrollment statistics."""
        query = select(
            func.count(GrantEnrollment.id).label("total"),
            func.count(GrantEnrollment.id).filter(
                GrantEnrollment.status == GrantEnrollmentStatus.ACTIVE
            ).label("active"),
            func.count(GrantEnrollment.id).filter(
                GrantEnrollment.status == GrantEnrollmentStatus.COMPLETED
            ).label("completed"),
            func.count(GrantEnrollment.id).filter(
                GrantEnrollment.status.in_([
                    GrantEnrollmentStatus.WITHDRAWN,
                    GrantEnrollmentStatus.DROPPED
                ])
            ).label("attrition"),
        ).where(GrantEnrollment.grant_id == grant_id)
        
        result = await self.db.execute(query)
        row = result.one()
        
        return {
            "total_enrolled": row.total,
            "currently_active": row.active,
            "completed": row.completed,
            "attrition": row.attrition,
            "retention_rate": (
                round((row.total - row.attrition) / row.total * 100, 1)
                if row.total > 0 else 0
            ),
        }
    
    async def _get_financial_stats(self, grant_id: int) -> dict:
        """Calculate financial statistics."""
        grant = await self.db.get(Grant, grant_id)
        
        # Sum expenses
        expense_query = select(
            func.coalesce(func.sum(GrantExpense.amount), 0)
        ).where(
            GrantExpense.grant_id == grant_id,
            GrantExpense.status == "approved"  # Only approved expenses
        )
        
        result = await self.db.execute(expense_query)
        total_spent = result.scalar() or Decimal("0")
        
        return {
            "total_budget": float(grant.total_amount),
            "total_spent": float(total_spent),
            "remaining": float(grant.total_amount - total_spent),
            "utilization_rate": round(
                float(total_spent / grant.total_amount * 100), 1
            ) if grant.total_amount > 0 else 0,
        }
    
    async def _get_outcome_stats(self, grant_id: int) -> dict:
        """Calculate outcome statistics."""
        query = select(
            GrantEnrollment.outcome,
            func.count(GrantEnrollment.id)
        ).where(
            GrantEnrollment.grant_id == grant_id,
            GrantEnrollment.outcome.isnot(None)
        ).group_by(GrantEnrollment.outcome)
        
        result = await self.db.execute(query)
        outcomes = {row[0].value: row[1] for row in result.all()}
        
        return {
            "by_outcome": outcomes,
            "total_with_outcomes": sum(outcomes.values()),
            "placement_count": outcomes.get("obtained_employment", 0) + 
                             outcomes.get("entered_apprenticeship", 0),
        }
    
    def _calculate_progress(
        self, 
        enrollment: dict, 
        outcomes: dict, 
        grant: Grant
    ) -> dict:
        """Calculate progress toward targets."""
        progress = {}
        
        if grant.target_enrollment:
            progress["enrollment"] = round(
                enrollment["total_enrolled"] / grant.target_enrollment * 100, 1
            )
        
        if grant.target_completion:
            progress["completion"] = round(
                enrollment["completed"] / grant.target_completion * 100, 1
            )
        
        if grant.target_placement:
            progress["placement"] = round(
                outcomes["placement_count"] / grant.target_placement * 100, 1
            )
        
        return progress
```

---

## Phase 4: Compliance Report Generation

### 4.1 Report Service

Create `src/services/grant_report_service.py`:

```python
"""Grant compliance report generation service."""
from datetime import date, datetime
from typing import Literal
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.grant_metrics_service import GrantMetricsService


class GrantReportService:
    """Generate compliance reports for grants."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.metrics = GrantMetricsService(db)
    
    async def generate_report(
        self,
        grant_id: int,
        report_type: Literal["summary", "detailed", "funder"],
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> dict:
        """Generate a compliance report."""
        summary = await self.metrics.get_grant_summary(grant_id)
        
        if report_type == "summary":
            return self._format_summary_report(summary)
        elif report_type == "detailed":
            return await self._format_detailed_report(grant_id, summary)
        elif report_type == "funder":
            return await self._format_funder_report(
                grant_id, summary, period_start, period_end
            )
    
    def _format_summary_report(self, summary: dict) -> dict:
        """Format executive summary report."""
        return {
            "report_type": "summary",
            "generated_at": datetime.utcnow().isoformat(),
            "grant": {
                "name": summary["grant_name"],
                "funder": summary["funder"],
                "period": summary["period"],
            },
            "highlights": {
                "total_enrolled": summary["enrollment"]["total_enrolled"],
                "currently_active": summary["enrollment"]["currently_active"],
                "completed": summary["enrollment"]["completed"],
                "retention_rate": f"{summary['enrollment']['retention_rate']}%",
                "budget_utilization": f"{summary['financials']['utilization_rate']}%",
            },
            "progress_toward_targets": summary["progress"],
        }
    
    async def _format_detailed_report(
        self, 
        grant_id: int, 
        summary: dict
    ) -> dict:
        """Format detailed report with student-level data."""
        # Get all enrollments for this grant
        enrollments = await self._get_enrollment_details(grant_id)
        expenses = await self._get_expense_details(grant_id)
        
        return {
            "report_type": "detailed",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": summary,
            "enrollments": enrollments,
            "expenses": expenses,
        }
    
    async def _format_funder_report(
        self,
        grant_id: int,
        summary: dict,
        period_start: date | None,
        period_end: date | None,
    ) -> dict:
        """Format report for funder submission."""
        # This would be customized per funder's requirements
        return {
            "report_type": "funder",
            "report_period": {
                "start": period_start.isoformat() if period_start else None,
                "end": period_end.isoformat() if period_end else None,
            },
            "generated_at": datetime.utcnow().isoformat(),
            "grant_number": summary.get("grant_number"),
            "grantee": "IBEW Local 46",
            "metrics": {
                "participants_served": summary["enrollment"]["total_enrolled"],
                "participants_completed": summary["enrollment"]["completed"],
                "job_placements": summary["outcomes"]["placement_count"],
                "funds_expended": summary["financials"]["total_spent"],
            },
            # Add funder-specific fields as needed
        }
    
    async def _get_enrollment_details(self, grant_id: int) -> list[dict]:
        """Get detailed enrollment records."""
        # Implementation would query GrantEnrollment with Student joins
        pass
    
    async def _get_expense_details(self, grant_id: int) -> list[dict]:
        """Get detailed expense records."""
        # Implementation would query GrantExpense
        pass
```

---

## Phase 5: Frontend - Grant Dashboard

### 5.1 Routes

Create `src/routers/ui/grants.py`:

```python
"""Grant management UI routes."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_async_session
from src.routers.dependencies.auth_cookie import get_current_user_from_cookie
from src.services.grant_service import GrantService
from src.services.grant_metrics_service import GrantMetricsService
from src.templates import templates

router = APIRouter(prefix="/grants", tags=["grants-ui"])


@router.get("", response_class=HTMLResponse)
async def grant_list(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user_from_cookie),
):
    """List all grants with summary metrics."""
    service = GrantService(db)
    grants = await service.get_all_grants()
    
    return templates.TemplateResponse(
        "grants/list.html",
        {"request": request, "grants": grants, "user": current_user}
    )


@router.get("/{grant_id}", response_class=HTMLResponse)
async def grant_detail(
    request: Request,
    grant_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user_from_cookie),
):
    """Grant detail page with metrics dashboard."""
    metrics = GrantMetricsService(db)
    summary = await metrics.get_grant_summary(grant_id)
    
    return templates.TemplateResponse(
        "grants/detail.html",
        {"request": request, "summary": summary, "user": current_user}
    )


@router.get("/{grant_id}/enrollments", response_class=HTMLResponse)
async def grant_enrollments(
    request: Request,
    grant_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user_from_cookie),
):
    """Manage student enrollments for a grant."""
    # Implementation
    pass


@router.get("/{grant_id}/expenses", response_class=HTMLResponse)
async def grant_expenses(
    request: Request,
    grant_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user_from_cookie),
):
    """Manage expenses for a grant."""
    # Implementation
    pass


@router.get("/{grant_id}/report", response_class=HTMLResponse)
async def grant_report_page(
    request: Request,
    grant_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user_from_cookie),
):
    """Report generation page."""
    # Implementation
    pass
```

### 5.2 Template Structure

Create these templates:

```
src/templates/grants/
├── list.html           # Grant list with summary cards
├── detail.html         # Grant dashboard with metrics
├── enrollments.html    # Student enrollment management
├── expenses.html       # Expense tracking
├── report.html         # Report generation options
└── partials/
    ├── _metrics_card.html
    ├── _enrollment_table.html
    ├── _expense_table.html
    └── _progress_chart.html
```

---

## Phase 6: Report Export (PDF/Excel)

### 6.1 PDF Report Generation

Leverage existing WeasyPrint setup:

```python
# Add to src/services/grant_report_service.py

from weasyprint import HTML
from io import BytesIO

async def generate_pdf_report(
    self,
    grant_id: int,
    report_type: str,
) -> BytesIO:
    """Generate PDF version of report."""
    report_data = await self.generate_report(grant_id, report_type)
    
    # Render HTML template
    html_content = self._render_report_template(report_data)
    
    # Convert to PDF
    pdf_buffer = BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    
    return pdf_buffer
```

### 6.2 Excel Export

```python
from openpyxl import Workbook

async def generate_excel_report(
    self,
    grant_id: int,
) -> BytesIO:
    """Generate Excel workbook with grant data."""
    summary = await self.metrics.get_grant_summary(grant_id)
    enrollments = await self._get_enrollment_details(grant_id)
    expenses = await self._get_expense_details(grant_id)
    
    wb = Workbook()
    
    # Summary sheet
    ws_summary = wb.active
    ws_summary.title = "Summary"
    # Populate summary data...
    
    # Enrollments sheet
    ws_enroll = wb.create_sheet("Enrollments")
    # Populate enrollment data...
    
    # Expenses sheet
    ws_expense = wb.create_sheet("Expenses")
    # Populate expense data...
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return buffer
```

---

## Acceptance Criteria

### Required - Backend
- [ ] Grant model has target/reporting fields
- [ ] GrantEnrollment model created with outcome tracking
- [ ] GrantExpense model linked (from Week 13)
- [ ] GrantMetricsService calculates all required metrics
- [ ] GrantReportService generates summary/detailed/funder reports
- [ ] All new code has test coverage

### Required - Frontend
- [ ] Grant list page with summary metrics
- [ ] Grant detail page with dashboard
- [ ] Enrollment management (add/update students)
- [ ] Expense tracking page
- [ ] Report generation page

### Required - Export
- [ ] PDF report generation working
- [ ] Excel export working

### Optional
- [ ] Funder-specific report templates (DOL, State, etc.)
- [ ] Automated report scheduling
- [ ] Email report delivery

---

## Testing Requirements

### Unit Tests

```bash
# Create these test files
src/tests/test_grant_enrollment.py
src/tests/test_grant_metrics_service.py
src/tests/test_grant_report_service.py
src/tests/test_grants_ui.py
```

### Test Scenarios

1. **Enrollment Tracking**
   - Enroll student in grant
   - Update enrollment status
   - Record outcome
   - Prevent duplicate enrollments

2. **Metrics Calculation**
   - Verify enrollment counts
   - Verify financial calculations
   - Verify outcome breakdowns
   - Verify progress calculations

3. **Report Generation**
   - Summary report format
   - Detailed report includes all data
   - PDF generation succeeds
   - Excel export has correct sheets

---

## 📝 MANDATORY: End-of-Session Documentation

> **REQUIRED:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. **Do not forget about ADRs—update as necessary.**

### Quick Checklist

- [ ] `/CHANGELOG.md` — Version bump, grant features added
- [ ] `/CLAUDE.md` — Update model count, add grant module section
- [ ] `/docs/IP2A_MILESTONE_CHECKLIST.md` — Mark grant completion
- [ ] `/docs/decisions/ADR-014-grant-compliance-reporting.md` — **Create new ADR**
- [ ] `/docs/reports/session-logs/YYYY-MM-DD-grant-expansion.md` — **Create session log**

### ADR Triggers for This Week

**Definitely create ADR for:**
- Grant outcome taxonomy choices
- Report format decisions
- Funder template approach

---

*Last Updated: February 1, 2026*
