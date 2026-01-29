# Session A: Report Infrastructure

**Duration:** 2-3 hours
**Goal:** Base report service with PDF and Excel generation

---

## Prerequisites

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Verify ~284 passing
```

---

## Task 1: Add Dependencies

Update `requirements.txt`:
```
weasyprint==60.1
openpyxl==3.1.2
```

Update `Dockerfile` (if needed for WeasyPrint):
```dockerfile
# Add before pip install
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
```

Install locally:
```bash
pip install weasyprint==60.1 openpyxl==3.1.2 --break-system-packages
```

---

## Task 2: Create ReportService

Create `src/services/report_service.py`:

```python
"""Report generation service."""

import io
from datetime import datetime
from typing import Optional, Any

from weasyprint import HTML, CSS
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter


class ReportService:
    """Service for generating PDF and Excel reports."""

    # Default CSS for PDF reports
    DEFAULT_CSS = """
        @page {
            size: letter;
            margin: 1in;
            @top-center {
                content: "IP2A Database Report";
                font-size: 10pt;
                color: #666;
            }
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10pt;
                color: #666;
            }
        }

        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.4;
            color: #333;
        }

        h1 {
            color: #1a365d;
            font-size: 24pt;
            margin-bottom: 0.5em;
            border-bottom: 2px solid #1a365d;
            padding-bottom: 0.25em;
        }

        h2 {
            color: #2c5282;
            font-size: 16pt;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }

        h3 {
            color: #2d3748;
            font-size: 13pt;
            margin-top: 0.75em;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
            font-size: 10pt;
        }

        th {
            background-color: #edf2f7;
            border: 1px solid #cbd5e0;
            padding: 8px 12px;
            text-align: left;
            font-weight: 600;
        }

        td {
            border: 1px solid #e2e8f0;
            padding: 8px 12px;
        }

        tr:nth-child(even) {
            background-color: #f7fafc;
        }

        .header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 1.5em;
        }

        .meta {
            font-size: 10pt;
            color: #718096;
        }

        .stat-box {
            background-color: #ebf8ff;
            border: 1px solid #90cdf4;
            border-radius: 4px;
            padding: 12px;
            margin: 0.5em 0;
        }

        .stat-label {
            font-size: 10pt;
            color: #4a5568;
        }

        .stat-value {
            font-size: 18pt;
            font-weight: 600;
            color: #2b6cb0;
        }

        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 9pt;
            font-weight: 500;
        }

        .badge-success { background-color: #c6f6d5; color: #22543d; }
        .badge-warning { background-color: #fefcbf; color: #744210; }
        .badge-error { background-color: #fed7d7; color: #822727; }
        .badge-info { background-color: #bee3f8; color: #2a4365; }

        .certificate {
            text-align: center;
            padding: 2em;
            border: 3px double #1a365d;
            margin: 1em;
        }

        .certificate h1 {
            border: none;
            font-size: 28pt;
        }

        .certificate .name {
            font-size: 24pt;
            color: #2d3748;
            margin: 1em 0;
        }

        .footer {
            margin-top: 2em;
            padding-top: 1em;
            border-top: 1px solid #e2e8f0;
            font-size: 9pt;
            color: #718096;
        }
    """

    @staticmethod
    def generate_pdf(
        html_content: str,
        css: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> bytes:
        """
        Generate PDF from HTML content.

        Args:
            html_content: HTML string to convert
            css: Optional custom CSS (uses default if not provided)
            base_url: Base URL for resolving relative paths

        Returns:
            PDF as bytes
        """
        if css is None:
            css = ReportService.DEFAULT_CSS

        html = HTML(string=html_content, base_url=base_url)
        stylesheet = CSS(string=css)

        pdf_buffer = io.BytesIO()
        html.write_pdf(pdf_buffer, stylesheets=[stylesheet])
        pdf_buffer.seek(0)

        return pdf_buffer.getvalue()

    @staticmethod
    def generate_excel(
        data: list[dict[str, Any]],
        columns: list[dict[str, str]],
        sheet_name: str = "Report",
        title: Optional[str] = None,
    ) -> bytes:
        """
        Generate Excel file from data.

        Args:
            data: List of dictionaries with row data
            columns: List of column definitions [{"key": "field", "header": "Display Name"}]
            sheet_name: Name of the worksheet
            title: Optional title row

        Returns:
            Excel file as bytes
        """
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name

        # Styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        row_num = 1

        # Title row (optional)
        if title:
            ws.cell(row=row_num, column=1, value=title)
            ws.cell(row=row_num, column=1).font = Font(bold=True, size=14)
            ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=len(columns))
            row_num += 2

        # Header row
        for col_num, col_def in enumerate(columns, 1):
            cell = ws.cell(row=row_num, column=col_num, value=col_def["header"])
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

        row_num += 1

        # Data rows
        for row_data in data:
            for col_num, col_def in enumerate(columns, 1):
                value = row_data.get(col_def["key"], "")
                cell = ws.cell(row=row_num, column=col_num, value=value)
                cell.border = thin_border
            row_num += 1

        # Auto-adjust column widths
        for col_num, col_def in enumerate(columns, 1):
            max_length = len(col_def["header"])
            for row in range(1, row_num):
                cell_value = ws.cell(row=row, column=col_num).value
                if cell_value:
                    max_length = max(max_length, len(str(cell_value)))
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[get_column_letter(col_num)].width = adjusted_width

        # Add metadata footer
        ws.cell(row=row_num + 1, column=1, value=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        ws.cell(row=row_num + 1, column=1).font = Font(italic=True, color="666666")

        # Save to bytes
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)

        return excel_buffer.getvalue()

    @staticmethod
    def format_currency(amount) -> str:
        """Format amount as currency string."""
        if amount is None:
            return "$0.00"
        return f"${float(amount):,.2f}"

    @staticmethod
    def format_date(dt, format_str: str = "%B %d, %Y") -> str:
        """Format datetime as string."""
        if dt is None:
            return "—"
        return dt.strftime(format_str)

    @staticmethod
    def format_phone(phone: Optional[str]) -> str:
        """Format phone number."""
        if not phone:
            return "—"
        # Simple formatting for 10-digit numbers
        digits = "".join(filter(str.isdigit, phone))
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return phone
```

---

## Task 3: Create Reports Router

Create `src/routers/reports.py`:

```python
"""Routes for report generation."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.dependencies.auth_cookie import get_current_user_from_cookie
from src.db.models import User
from src.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


def get_templates(request: Request):
    """Get templates from app state."""
    return request.app.state.templates


@router.get("", response_class=HTMLResponse)
async def reports_landing(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Reports landing page with available reports."""
    templates = get_templates(request)

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
```

---

## Task 4: Create Reports Landing Template

Create `src/templates/reports/index.html`:

```html
{% extends "base.html" %}

{% block title %}Reports - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li>Reports</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div>
        <h1 class="text-2xl font-bold">Reports</h1>
        <p class="text-base-content/70">Generate and download reports in PDF or Excel format</p>
    </div>

    <!-- Report Categories -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        {% for category in reports %}
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title">
                    {% if category.category == "Members" %}
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    {% elif category.category == "Dues" %}
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {% elif category.category == "Training" %}
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                    {% else %}
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    {% endif %}
                    {{ category.category }}
                </h2>

                <div class="divide-y">
                    {% for item in category.items %}
                    <div class="py-3 flex justify-between items-center">
                        <span>{{ item.name }}</span>
                        <div class="flex gap-2">
                            {% if "pdf" in item.formats %}
                            <a href="{{ item.url }}?format=pdf" class="btn btn-sm btn-outline btn-error">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                </svg>
                                PDF
                            </a>
                            {% endif %}
                            {% if "excel" in item.formats %}
                            <a href="{{ item.url }}?format=excel" class="btn btn-sm btn-outline btn-success">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                Excel
                            </a>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- Info Box -->
    <div class="alert alert-info">
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div>
            <h3 class="font-bold">Report Tips</h3>
            <ul class="text-sm mt-1">
                <li>• PDF reports are formatted for printing</li>
                <li>• Excel reports can be filtered and analyzed</li>
                <li>• Reports reflect data as of generation time</li>
            </ul>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Task 5: Create PDF Base Template

Create `src/templates/reports/base_pdf.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }} - IP2A Report</title>
</head>
<body>
    <div class="header">
        <div>
            <h1>{{ title }}</h1>
            {% if subtitle %}
            <p class="meta">{{ subtitle }}</p>
            {% endif %}
        </div>
        <div class="meta" style="text-align: right;">
            <p>Generated: {{ generated_at }}</p>
            {% if generated_by %}
            <p>By: {{ generated_by }}</p>
            {% endif %}
        </div>
    </div>

    {% block content %}{% endblock %}

    <div class="footer">
        <p>IBEW Local 46 — IP2A Database Report</p>
        <p>This report contains confidential information. Handle accordingly.</p>
    </div>
</body>
</html>
```

---

## Task 6: Register Router

Update `src/main.py`:

```python
# Add import
from src.routers.reports import router as reports_router

# Add router registration
app.include_router(reports_router)
```

---

## Task 7: Update Sidebar

Add to `src/templates/components/sidebar.html`:

```html
<!-- Reports -->
<li>
    <a href="/reports" class="{% if request.url.path.startswith('/reports') %}active{% endif %}">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        Reports
    </a>
</li>
```

---

## Task 8: Add Initial Tests

Create `src/tests/test_reports.py`:

```python
"""Tests for report generation."""

import pytest
from fastapi.testclient import TestClient

from src.services.report_service import ReportService


class TestReportService:
    """Tests for ReportService."""

    def test_format_currency(self):
        """Format currency correctly."""
        assert ReportService.format_currency(75.00) == "$75.00"
        assert ReportService.format_currency(1234.56) == "$1,234.56"
        assert ReportService.format_currency(None) == "$0.00"

    def test_format_phone(self):
        """Format phone number correctly."""
        assert ReportService.format_phone("2065551234") == "(206) 555-1234"
        assert ReportService.format_phone(None) == "—"

    def test_generate_excel(self):
        """Generate Excel file from data."""
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25},
        ]
        columns = [
            {"key": "name", "header": "Name"},
            {"key": "age", "header": "Age"},
        ]

        result = ReportService.generate_excel(data, columns, title="Test Report")

        assert isinstance(result, bytes)
        assert len(result) > 0


class TestReportsLanding:
    """Tests for reports landing page."""

    def test_reports_landing_requires_auth(self, client: TestClient):
        """Reports landing requires authentication."""
        response = client.get("/reports")
        assert response.status_code in [302, 401, 403]

    def test_reports_landing_authenticated(self, authenticated_client: TestClient):
        """Reports landing loads for authenticated users."""
        response = authenticated_client.get("/reports")
        assert response.status_code == 200
        assert b"Reports" in response.content

    def test_reports_landing_shows_categories(self, authenticated_client: TestClient):
        """Reports landing shows report categories."""
        response = authenticated_client.get("/reports")
        assert response.status_code == 200
        assert b"Members" in response.content
        assert b"Dues" in response.content
        assert b"Training" in response.content
```

---

## Verification

```bash
# Install dependencies
pip install weasyprint==60.1 openpyxl==3.1.2 --break-system-packages

# Run tests
pytest src/tests/test_reports.py -v

# Test manually
# 1. Navigate to /reports - should see landing page
# 2. Verify report categories are displayed
# 3. Verify PDF/Excel buttons are present

# Commit
git add -A
git commit -m "feat(reports): add report infrastructure

- Add ReportService with PDF/Excel generation
- Add weasyprint and openpyxl dependencies
- Add reports router with landing page
- Add reports landing template
- Add PDF base template
- Update sidebar navigation
- Add initial report tests"
```

---

## Session A Complete

**Created:**
- `src/services/report_service.py`
- `src/routers/reports.py`
- `src/templates/reports/index.html`
- `src/templates/reports/base_pdf.html`
- `src/tests/test_reports.py`

**Modified:**
- `requirements.txt`
- `src/main.py`
- `src/templates/components/sidebar.html`

**Next:** Session B - Member & Dues Reports
