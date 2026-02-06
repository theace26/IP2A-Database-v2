# Claude Code Instruction: Week 33A — Out-of-Work List Reports (P0 Critical)

**Source:** Spoke 2 → Claude Code
**Date:** February 5, 2026
**Priority:** 🔴 HIGH
**Estimated Time:** 5 hours
**Branch:** develop
**Risk Level:** MEDIUM — new service layer (ReferralReportService), WeasyPrint PDF generation
**Prerequisite:** Week 32 complete (7e DONE, reports navigation dashboard exists)

---

## Context

This is the first batch of report generation for Sub-Phase 7f. Out-of-Work Lists are the **single most important daily tool** for dispatch staff. Every morning, dispatchers print these lists to process referrals. If these reports are wrong, members get dispatched out of order — a grievable offense under the Referral Procedures.

These 4 reports form the foundation that all subsequent report batches build on. The `ReferralReportService` created here will be extended in Weeks 33B, 34, and 35+.

**Reports in this batch:**

| # | Report Name | Output Formats | Usage |
|---|-------------|---------------|-------|
| 1 | Out-of-Work List (by Book) | PDF + Excel | Morning dispatch — one per book |
| 2 | Out-of-Work List (All Books) | PDF + Excel | Overview across entire dispatch system |
| 3 | Out-of-Work Summary | PDF | Quick counts per book per tier — dashboard report |
| 4 | Active Registrations by Member | PDF | Lookup: all books a specific member is registered on |

---

## Pre-Flight Checklist

- [ ] `git checkout develop && git pull origin develop`
- [ ] `docker-compose up -d`
- [ ] `pytest -v --tb=short` — verify baseline (should be ~529+ after Week 32)
- [ ] Read `CLAUDE.md` for current state
- [ ] Confirm Week 32 is committed and reports navigation dashboard exists at `/dispatch/reports`
- [ ] Verify WeasyPrint is installed: `pip show weasyprint` — if not, `pip install weasyprint --break-system-packages`
- [ ] Verify openpyxl is installed: `pip show openpyxl` — if not, `pip install openpyxl --break-system-packages`
- [ ] Check both are in `requirements.txt` — add if missing

---

## Task 1: Create ReferralReportService (~1.5 hrs)

### What This Is

The central service for all referral/dispatch report generation. This task creates the service with 4 report methods and shared infrastructure (PDF rendering, Excel generation, union branding).

### Files to Create

| File | Purpose |
|------|---------|
| `src/services/referral_report_service.py` | Report generation service — business logic + data assembly |

### Implementation Details

**Study the existing pattern first:**
```bash
cat src/services/report_service.py
```

The existing `ReportService` (Week 8) generates member roster, dues summary, and other reports. Follow its patterns for PDF and Excel generation. Do NOT subclass it — create a parallel service. The existing service handles training/dues domain; this one handles referral/dispatch domain.

**Service structure:**

```python
# src/services/referral_report_service.py

from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session
from io import BytesIO

class ReferralReportService:
    """Generates referral and dispatch reports (PDF + Excel).
    
    All reports follow these principles:
    - Data assembly happens in service methods (not templates)
    - PDF rendering uses WeasyPrint with Jinja2 HTML templates
    - Excel rendering uses openpyxl with consistent formatting
    - All report generation is audit-logged
    - Union branding (Local 46 header, generation timestamp, user) on all PDFs
    """

    def __init__(self, db: Session):
        self.db = db

    # --- Report 1: Out-of-Work List (by Book) ---
    def get_out_of_work_by_book(
        self, book_id: int, tier: Optional[int] = None
    ) -> dict:
        """Assemble data for a single book's out-of-work list.
        
        Returns: {
            'book': ReferralBook object,
            'registrations': [sorted by APN ascending],
            'total_count': int,
            'tier_counts': {1: n, 2: n, 3: n, 4: n},
            'generated_at': datetime,
        }
        
        Sort order: APN ascending (DECIMAL sort — this is dispatch priority order).
        If tier is specified, filter to that tier only.
        """

    def render_out_of_work_by_book_pdf(
        self, book_id: int, tier: Optional[int] = None
    ) -> BytesIO:
        """Render PDF for single book out-of-work list."""

    def render_out_of_work_by_book_excel(
        self, book_id: int, tier: Optional[int] = None
    ) -> BytesIO:
        """Render Excel for single book out-of-work list."""

    # --- Report 2: Out-of-Work List (All Books) ---
    def get_out_of_work_all_books(self) -> dict:
        """Assemble data for combined out-of-work list across all books.
        
        Returns: {
            'books': [{
                'book': ReferralBook,
                'registrations': [sorted by APN],
                'count': int,
            }],
            'total_across_all': int,
            'generated_at': datetime,
        }
        
        Books sorted by morning processing order (Rule #2):
        Wire 8:30 → S&C/Marine/Stock/LFM/Residential 9:00 → Tradeshow 9:30
        """

    def render_out_of_work_all_books_pdf(self) -> BytesIO:
        """Render PDF for all-books out-of-work list."""

    def render_out_of_work_all_books_excel(self) -> BytesIO:
        """Render Excel for all-books out-of-work list."""

    # --- Report 3: Out-of-Work Summary ---
    def get_out_of_work_summary(self) -> dict:
        """Assemble summary counts per book per tier.
        
        Returns: {
            'summary': [{
                'book_name': str,
                'book_id': int,
                'tier_1': int,
                'tier_2': int,
                'tier_3': int,
                'tier_4': int,
                'total': int,
            }],
            'grand_total': int,
            'generated_at': datetime,
        }
        """

    def render_out_of_work_summary_pdf(self) -> BytesIO:
        """Render PDF summary — compact, fits on one page."""

    # --- Report 4: Active Registrations by Member ---
    def get_member_registrations(self, member_id: int) -> dict:
        """Assemble all active registrations for a specific member.
        
        Returns: {
            'member': Member object,
            'registrations': [{
                'book': ReferralBook,
                'tier': int,
                'apn': Decimal,
                'registered_date': date,
                'last_re_sign': date,
                're_sign_due': date,
                'check_marks': int,
                'status': str,
            }],
            'total_books': int,
            'generated_at': datetime,
        }
        """

    def render_member_registrations_pdf(self, member_id: int) -> BytesIO:
        """Render PDF for single member's registration overview."""

    # --- Shared Infrastructure ---
    def _render_pdf(self, template_name: str, context: dict) -> BytesIO:
        """Render HTML template to PDF via WeasyPrint.
        
        All PDFs include:
        - IBEW Local 46 header
        - Report title and generation timestamp
        - Generated by: [username]
        - Page numbers in footer
        """

    def _render_excel(
        self, headers: list[str], rows: list[list], sheet_name: str, title: str
    ) -> BytesIO:
        """Render data to Excel via openpyxl.
        
        All Excel files include:
        - Title row (merged, bold)
        - Generation timestamp
        - Auto-column-width
        - Freeze panes (header row frozen)
        - Table formatting with alternating row colors
        """
```

**Critical APN handling:**
```python
# When sorting registrations, sort by APN as Decimal — NOT as string or int
# APN 45880.23 comes before 45880.91 comes before 45881.00
# SQLAlchemy: .order_by(BookRegistration.applicant_priority_number.asc())
```

**Morning processing order constant** (used in all-books report):
```python
MORNING_PROCESSING_ORDER = [
    # 8:30 AM — Inside Wireperson
    'WIRE SEATTLE', 'WIRE BREMERTON', 'WIRE PT ANGELES',
    # 9:00 AM — Other classifications
    'SOUND & COMM', 'MARINE', 'STOCKMAN', 'LT FXT MAINT', 'RESIDENTIAL',
    # 9:30 AM — Supplemental
    'TRADESHOW',
    # Unscheduled
    'TECHNICIAN', 'UTILITY WORKER', 'TERO APPR WIRE',
]
```

---

## Task 2: Create PDF Report Templates (~1.5 hrs)

### Files to Create

| File | Purpose |
|------|---------|
| `src/templates/reports/referral/_base_report.html` | Base layout for all referral PDF reports (union branding) |
| `src/templates/reports/referral/out_of_work_by_book.html` | Single book out-of-work list |
| `src/templates/reports/referral/out_of_work_all_books.html` | Combined all-books list |
| `src/templates/reports/referral/out_of_work_summary.html` | Summary counts table |
| `src/templates/reports/referral/member_registrations.html` | Single member registration overview |

### Implementation Details

**Base report template (`_base_report.html`):**

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        /* WeasyPrint CSS — print-optimized */
        @page {
            size: letter;
            margin: 0.75in;
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }
        }
        body { font-family: Arial, Helvetica, sans-serif; font-size: 10pt; }
        .header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #003366; padding-bottom: 10px; }
        .header h1 { font-size: 14pt; color: #003366; margin: 0; }
        .header .subtitle { font-size: 10pt; color: #666; }
        .header .local { font-size: 12pt; font-weight: bold; color: #003366; }
        .meta { font-size: 8pt; color: #999; margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th { background: #003366; color: white; padding: 6px 8px; text-align: left; font-size: 9pt; }
        td { padding: 4px 8px; border-bottom: 1px solid #ddd; font-size: 9pt; }
        tr:nth-child(even) { background: #f5f5f5; }
        .tier-badge { display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 8pt; font-weight: bold; }
        .tier-1 { background: #d1fae5; color: #065f46; }
        .tier-2 { background: #dbeafe; color: #1e40af; }
        .tier-3 { background: #fef3c7; color: #92400e; }
        .tier-4 { background: #fce7f3; color: #9d174d; }
        .summary-box { background: #f0f4f8; padding: 12px; border-radius: 4px; margin-bottom: 15px; }
        .count-label { font-weight: bold; color: #003366; }
    </style>
</head>
<body>
    <div class="header">
        <div class="local">IBEW Local 46</div>
        <h1>{% block title %}Report{% endblock %}</h1>
        <div class="subtitle">{% block subtitle %}{% endblock %}</div>
    </div>
    <div class="meta">
        Generated: {{ generated_at.strftime('%B %d, %Y at %I:%M %p') }}
        {% if generated_by %} | By: {{ generated_by }}{% endif %}
    </div>
    {% block content %}{% endblock %}
</body>
</html>
```

**Out-of-Work by Book template columns:**
| Column | Source |
|--------|--------|
| # (row number) | Sequential |
| APN | `registration.applicant_priority_number` — format as `XXXXX.XX` |
| Member Name | `registration.member.last_name, first_name` |
| Card # | `registration.member.card_number` (if available) |
| Tier | `registration.book_priority_number` — with tier badge |
| Registered | `registration.registered_date` — format `MM/DD/YYYY` |
| Last Re-Sign | `registration.last_re_sign_date` — format `MM/DD/YYYY` |
| Re-Sign Due | calculated: last_re_sign + 30 days |
| Check Marks | count for this member on this book |
| Status | `registration.status` — badge |

**Out-of-Work Summary template:** Simple grid — one row per book, columns for Tier 1/2/3/4/Total. Grand total row at bottom. This should fit on a single page.

**Member Registrations template:** Member header (name, card number, classification), then table of all active registrations across books with APN, tier, dates, check marks.

---

## Task 3: Create API Endpoints (~1 hr)

### Files to Modify

| File | Change |
|------|--------|
| `src/routers/dispatch_api.py` (or create `src/routers/referral_reports_api.py`) | Add report generation endpoints |

### Implementation Details

**Decision point:** Add report endpoints to the existing `dispatch_api.py` router, OR create a dedicated `referral_reports_api.py` router. Hub recommendation: create a separate router — the reports will grow to 78 endpoints and shouldn't clutter the dispatch CRUD router.

**If creating a new router (`src/routers/referral_reports_api.py`):**
- Register it in `src/main.py` with prefix `/api/v1/reports/referral` and tag `referral-reports`
- **⚠️ This modifies `src/main.py` — note in session summary for Hub handoff**

**Endpoints:**

```python
@router.get("/out-of-work/book/{book_id}")
# Query params: format (pdf|xlsx), tier (optional, 1-4)
# Returns: StreamingResponse with appropriate content-type
# Audit log: report generation

@router.get("/out-of-work/all-books")
# Query params: format (pdf|xlsx)
# Returns: StreamingResponse
# Audit log: report generation

@router.get("/out-of-work/summary")
# Query params: format (pdf) — summary is PDF-only (one page)
# Returns: StreamingResponse
# Audit log: report generation

@router.get("/member/{member_id}/registrations")
# Query params: format (pdf)
# Returns: StreamingResponse
# Audit log: report generation
```

**Response pattern:**
```python
from fastapi.responses import StreamingResponse

@router.get("/out-of-work/book/{book_id}")
def get_out_of_work_by_book(
    book_id: int,
    format: str = Query("pdf", regex="^(pdf|xlsx)$"),
    tier: Optional[int] = Query(None, ge=1, le=4),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReferralReportService(db)
    
    if format == "pdf":
        buffer = service.render_out_of_work_by_book_pdf(book_id, tier)
        media_type = "application/pdf"
        filename = f"out_of_work_book_{book_id}.pdf"
    else:
        buffer = service.render_out_of_work_by_book_excel(book_id, tier)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"out_of_work_book_{book_id}.xlsx"
    
    # Audit log the report generation
    audit_service.log_action(
        db=db, action="REPORT_GENERATED",
        table_name="referral_reports",
        details={"report": "out_of_work_by_book", "book_id": book_id, "format": format},
        user_id=current_user.id,
    )
    
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
```

---

## Task 4: Wire Reports to Navigation Dashboard (~30 min)

### Files to Modify

| File | Change |
|------|--------|
| `src/services/dispatch_frontend_service.py` | Update `get_report_categories()` to mark these 4 reports as `available: True` with URLs |
| `src/templates/dispatch/reports_landing.html` | Available reports should render as download links (not "Coming Soon") |

### Implementation Details

Update the 4 reports in the "Out-of-Work Lists" and "Registration Reports" categories (Report 4 goes under Registration):

```python
# In get_report_categories(), update these entries:
{'name': 'Out-of-Work List (by Book)', 'available': True, 
 'url': '/api/v1/reports/referral/out-of-work/book/{book_id}?format=pdf',
 'needs_book_selector': True},  # UI must show book dropdown
```

For reports that need a book selector, the landing page should show a dropdown of active books before the download link. Use HTMX to load book options.

---

## Task 5: Tests (~30 min)

### Files to Create or Modify

| File | Change |
|------|--------|
| `src/tests/test_referral_reports.py` | **NEW** — tests for ReferralReportService + API endpoints |

### Tests Required (8 minimum)

```python
# test_referral_reports.py

class TestReferralReportService:
    def test_out_of_work_by_book_data_assembly(self, db, sample_book_with_registrations):
        """Service returns correct registration data sorted by APN ascending"""

    def test_out_of_work_by_book_respects_tier_filter(self, db, sample_book_with_registrations):
        """When tier=1, only tier 1 registrations returned"""

    def test_out_of_work_all_books_processing_order(self, db, sample_multiple_books):
        """Books are returned in morning processing order (Wire first, Tradeshow last)"""

    def test_out_of_work_summary_counts(self, db, sample_multiple_books):
        """Summary returns correct count per book per tier"""

    def test_member_registrations_returns_all_books(self, db, sample_member_on_multiple_books):
        """Returns all active registrations for a member across books"""

class TestReferralReportAPI:
    def test_out_of_work_pdf_endpoint(self, auth_client, sample_book_with_registrations):
        """GET /api/v1/reports/referral/out-of-work/book/{id}?format=pdf returns 200 with PDF"""

    def test_out_of_work_excel_endpoint(self, auth_client, sample_book_with_registrations):
        """GET /api/v1/reports/referral/out-of-work/book/{id}?format=xlsx returns 200 with Excel"""

    def test_report_endpoint_requires_auth(self, client):
        """Unauthenticated report request returns 401/302"""
```

**Test fixtures needed:**
- `sample_book_with_registrations` — A ReferralBook with 5+ BookRegistrations at varying APNs and tiers
- `sample_multiple_books` — 3+ books with registrations (for all-books and summary reports)
- `sample_member_on_multiple_books` — One member registered on 3 books (for member registrations report)

Add these fixtures to `conftest.py` or to the test file itself. If adding to `conftest.py`, note in session summary for Hub handoff.

---

## Anti-Patterns (DO NOT)

- Do NOT sort APNs as strings or integers — always sort as Decimal
- Do NOT hardcode book names in report queries — always query from `referral_books` table
- Do NOT put business logic in PDF templates — all data assembly happens in the service layer
- Do NOT generate reports without audit logging — every generation must be tracked
- Do NOT modify existing Phase 7 models
- Do NOT use `commit()` in test fixtures — use `flush()`
- Do NOT install WeasyPrint system dependencies in Docker without updating Dockerfile (note for Hub)
- Do NOT create new Alembic migrations — these are service + template changes only

---

## WeasyPrint Dependency Note

WeasyPrint requires system libraries (`libpango`, `libcairo`, etc.). Check the Dockerfile:

```bash
grep -i "weasyprint\|pango\|cairo" Dockerfile
```

If not present, the Docker build will need updating. This is a **Hub/Spoke 3 concern** — note in session summary. For local development, these are typically already installed. If WeasyPrint fails, fall back to HTML-to-PDF via `xhtml2pdf` as a simpler alternative (less CSS support but zero system deps).

---

## Success Criteria

- [ ] `ReferralReportService` created with 4 report data methods + PDF/Excel renderers
- [ ] 4 PDF templates created with union branding and proper formatting
- [ ] 4 API endpoints returning PDF/Excel downloads
- [ ] Reports navigation dashboard updated to show 4 available reports
- [ ] APN sorting verified as Decimal (not string/int)
- [ ] Morning processing order used in all-books report
- [ ] All report generations audit-logged
- [ ] Minimum 8 new tests passing
- [ ] No regression in existing tests

---

## End-of-Session (MANDATORY)

- [ ] `pytest -v` — verify green (or document new failures)
- [ ] `ruff check . --fix && ruff format .`
- [ ] `git add -A && git commit -m "feat(phase7): Week 33A — out-of-work list reports (P0)"`
- [ ] `git push origin develop`
- [ ] Update `CLAUDE.md` — test counts, mark reports batch 1 complete
- [ ] Update `CHANGELOG.md`
- [ ] Create session log: `docs/reports/session-logs/2026-XX-XX-week33a-owlist-reports.md`
- [ ] If `src/main.py` modified (new router), note in session summary for Hub handoff
- [ ] If `conftest.py` modified (new fixtures), note in session summary for Hub handoff
- [ ] If Dockerfile needs WeasyPrint deps, note in session summary for Hub/Spoke 3

---

## Files Changed/Created Summary (Expected)

**Created:**
- `/src/services/referral_report_service.py`
- `/src/routers/referral_reports_api.py` (or endpoints added to existing router)
- `/src/templates/reports/referral/_base_report.html`
- `/src/templates/reports/referral/out_of_work_by_book.html`
- `/src/templates/reports/referral/out_of_work_all_books.html`
- `/src/templates/reports/referral/out_of_work_summary.html`
- `/src/templates/reports/referral/member_registrations.html`
- `/src/tests/test_referral_reports.py`

**Modified:**
- `/src/main.py` — new router registration (⚠️ shared file)
- `/src/services/dispatch_frontend_service.py` — report availability flags
- `/src/templates/dispatch/reports_landing.html` — available report links
- `/requirements.txt` — verify WeasyPrint and openpyxl listed

---

## Session Reminders

> **Member ≠ Student.** Phase 7 reports use `members` table, NOT `students`.

> **APN = DECIMAL(10,2).** All sorting by APN must use Decimal comparison. Display format: `XXXXX.XX` (5 digits, 2 decimal places).

> **Morning Processing Order matters.** Wire books first (8:30 AM), then S&C/Marine/Stock/LFM/Residential (9:00 AM), then Tradeshow (9:30 AM).

> **Audit everything.** Report generation is an auditable action — dispatchers need to know who ran what report and when.

---

*Week 33A Instruction — Spoke 2: Operations*
*UnionCore (IP2A-Database-v2) — February 5, 2026*
