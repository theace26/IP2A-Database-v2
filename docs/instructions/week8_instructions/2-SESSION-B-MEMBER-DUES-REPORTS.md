# Session B: Member & Dues Reports

**Duration:** 2-3 hours
**Goal:** Member roster and dues reports (PDF/Excel)

---

## Prerequisites

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest src/tests/test_reports.py -v  # Verify Session A tests pass
```

---

## Task 1: Add Member Report Routes

Add to `src/routers/reports.py`:

```python
# Add imports
from src.db.models import Member, DuesPeriod, DuesPayment
from src.db.enums import MemberStatus, MemberClassification, DuesPaymentStatus

@router.get("/members/roster")
async def member_roster_report(
    request: Request,
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Generate member roster report."""
    templates = get_templates(request)

    # Query members
    query = db.query(Member).filter(Member.deleted_at == None)

    if status:
        try:
            status_enum = MemberStatus(status)
            query = query.filter(Member.status == status_enum)
        except ValueError:
            pass

    members = query.order_by(Member.last_name, Member.first_name).all()

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
            generated_by=current_user.email,
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
```

---

## Task 2: Create Member Roster PDF Template

Create `src/templates/reports/member_roster.html`:

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
            <p class="meta">{{ subtitle }}</p>
        </div>
        <div class="meta" style="text-align: right;">
            <p>Generated: {{ generated_at }}</p>
            <p>By: {{ generated_by }}</p>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Member #</th>
                <th>Name</th>
                <th>Contact</th>
                <th>Classification</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for member in members %}
            <tr>
                <td>{{ member.member_number or '—' }}</td>
                <td>
                    <strong>{{ member.last_name }}, {{ member.first_name }}</strong>
                </td>
                <td>
                    {% if member.email %}{{ member.email }}<br>{% endif %}
                    {{ format_phone(member.phone) }}
                </td>
                <td>
                    {% if member.classification %}
                    <span class="badge badge-info">{{ member.classification.value.replace('_', ' ').title() }}</span>
                    {% else %}
                    —
                    {% endif %}
                </td>
                <td>
                    {% if member.status %}
                    <span class="badge {% if member.status.value == 'active' %}badge-success{% elif member.status.value == 'inactive' %}badge-warning{% else %}badge-error{% endif %}">
                        {{ member.status.value.title() }}
                    </span>
                    {% else %}
                    —
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="footer">
        <p>IBEW Local 46 — Member Roster Report</p>
        <p>This report contains confidential member information. Handle accordingly.</p>
    </div>
</body>
</html>
```

---

## Task 3: Add Dues Report Routes

Add to `src/routers/reports.py`:

```python
from sqlalchemy import func, and_
from decimal import Decimal

@router.get("/dues/summary")
async def dues_summary_report(
    request: Request,
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Generate dues summary report by period."""
    templates = get_templates(request)

    # Default to current year
    if not year:
        year = datetime.now().year

    # Get periods for the year
    periods = (
        db.query(DuesPeriod)
        .filter(DuesPeriod.period_year == year)
        .order_by(DuesPeriod.period_month)
        .all()
    )

    # Calculate stats for each period
    period_stats = []
    for period in periods:
        payments = (
            db.query(DuesPayment)
            .filter(DuesPayment.period_id == period.id)
            .all()
        )

        total_due = sum(p.amount_due for p in payments)
        total_paid = sum(p.amount_paid or Decimal("0") for p in payments)
        member_count = len(payments)
        paid_count = sum(1 for p in payments if p.status == DuesPaymentStatus.PAID)

        period_stats.append({
            "period_name": f"{['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][period.period_month]} {period.period_year}",
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
            generated_by=current_user.email,
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
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Generate overdue members report."""
    templates = get_templates(request)

    # Get overdue payments with member info
    overdue_payments = (
        db.query(DuesPayment)
        .join(Member)
        .filter(DuesPayment.status == DuesPaymentStatus.OVERDUE)
        .order_by(Member.last_name, Member.first_name)
        .all()
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
            generated_by=current_user.email,
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
```

---

## Task 4: Create Dues Summary PDF Template

Create `src/templates/reports/dues_summary.html`:

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
            <p class="meta">{{ subtitle }}</p>
        </div>
        <div class="meta" style="text-align: right;">
            <p>Generated: {{ generated_at }}</p>
            <p>By: {{ generated_by }}</p>
        </div>
    </div>

    <!-- Summary Stats -->
    <div style="display: flex; gap: 20px; margin-bottom: 20px;">
        <div class="stat-box" style="flex: 1;">
            <div class="stat-label">Total Due</div>
            <div class="stat-value">{{ format_currency(grand_total_due) }}</div>
        </div>
        <div class="stat-box" style="flex: 1;">
            <div class="stat-label">Total Collected</div>
            <div class="stat-value">{{ format_currency(grand_total_paid) }}</div>
        </div>
        <div class="stat-box" style="flex: 1;">
            <div class="stat-label">Collection Rate</div>
            <div class="stat-value">{{ "%.1f"|format(grand_collection_rate) }}%</div>
        </div>
    </div>

    <h2>Monthly Breakdown</h2>
    <table>
        <thead>
            <tr>
                <th>Period</th>
                <th>Status</th>
                <th>Members</th>
                <th>Paid</th>
                <th>Total Due</th>
                <th>Total Paid</th>
                <th>Collection %</th>
            </tr>
        </thead>
        <tbody>
            {% for ps in period_stats %}
            <tr>
                <td>{{ ps.period_name }}</td>
                <td>
                    <span class="badge {% if ps.is_closed %}badge-success{% else %}badge-warning{% endif %}">
                        {% if ps.is_closed %}Closed{% else %}Open{% endif %}
                    </span>
                </td>
                <td>{{ ps.member_count }}</td>
                <td>{{ ps.paid_count }}</td>
                <td>{{ format_currency(ps.total_due) }}</td>
                <td>{{ format_currency(ps.total_paid) }}</td>
                <td>{{ "%.1f"|format(ps.collection_rate) }}%</td>
            </tr>
            {% endfor %}
        </tbody>
        <tfoot>
            <tr style="font-weight: bold; background-color: #edf2f7;">
                <td colspan="4">Totals</td>
                <td>{{ format_currency(grand_total_due) }}</td>
                <td>{{ format_currency(grand_total_paid) }}</td>
                <td>{{ "%.1f"|format(grand_collection_rate) }}%</td>
            </tr>
        </tfoot>
    </table>

    <div class="footer">
        <p>IBEW Local 46 — Dues Summary Report</p>
        <p>This report contains confidential financial information.</p>
    </div>
</body>
</html>
```

---

## Task 5: Create Overdue Report PDF Template

Create `src/templates/reports/overdue_report.html`:

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
            <p class="meta">{{ subtitle }}</p>
        </div>
        <div class="meta" style="text-align: right;">
            <p>Generated: {{ generated_at }}</p>
            <p>By: {{ generated_by }}</p>
        </div>
    </div>

    <!-- Summary -->
    <div class="stat-box" style="max-width: 300px;">
        <div class="stat-label">Total Overdue Balance</div>
        <div class="stat-value" style="color: #c53030;">{{ format_currency(total_overdue) }}</div>
    </div>

    {% if overdue_payments %}
    <table>
        <thead>
            <tr>
                <th>Member</th>
                <th>Contact</th>
                <th>Period</th>
                <th>Due</th>
                <th>Paid</th>
                <th>Balance</th>
            </tr>
        </thead>
        <tbody>
            {% for payment in overdue_payments %}
            <tr>
                <td>
                    {% if payment.member %}
                    <strong>{{ payment.member.last_name }}, {{ payment.member.first_name }}</strong>
                    <br><span style="font-size: 9pt; color: #666;">{{ payment.member.member_number or '' }}</span>
                    {% else %}
                    Member #{{ payment.member_id }}
                    {% endif %}
                </td>
                <td>
                    {% if payment.member %}
                    {% if payment.member.email %}{{ payment.member.email }}<br>{% endif %}
                    {{ format_phone(payment.member.phone) }}
                    {% else %}
                    —
                    {% endif %}
                </td>
                <td>
                    {% if payment.period %}
                    {{ payment.period.period_month }}/{{ payment.period.period_year }}
                    {% else %}
                    —
                    {% endif %}
                </td>
                <td>{{ format_currency(payment.amount_due) }}</td>
                <td>{{ format_currency(payment.amount_paid) }}</td>
                <td style="color: #c53030; font-weight: bold;">
                    {{ format_currency(payment.amount_due - (payment.amount_paid or 0)) }}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <div style="text-align: center; padding: 40px; color: #666;">
        <p>No overdue payments found. Great job!</p>
    </div>
    {% endif %}

    <div class="footer">
        <p>IBEW Local 46 — Overdue Report</p>
        <p>Members on this list should be contacted regarding payment.</p>
    </div>
</body>
</html>
```

---

## Task 6: Add Tests

Add to `src/tests/test_reports.py`:

```python
class TestMemberReports:
    """Tests for member reports."""

    def test_member_roster_pdf_requires_auth(self, client: TestClient):
        """Member roster PDF requires authentication."""
        response = client.get("/reports/members/roster?format=pdf")
        assert response.status_code in [302, 401, 403]

    def test_member_roster_pdf(self, authenticated_client: TestClient):
        """Member roster PDF generates successfully."""
        response = authenticated_client.get("/reports/members/roster?format=pdf")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_member_roster_excel(self, authenticated_client: TestClient):
        """Member roster Excel generates successfully."""
        response = authenticated_client.get("/reports/members/roster?format=excel")
        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]


class TestDuesReports:
    """Tests for dues reports."""

    def test_dues_summary_pdf(self, authenticated_client: TestClient):
        """Dues summary PDF generates successfully."""
        response = authenticated_client.get("/reports/dues/summary?format=pdf")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_dues_summary_excel(self, authenticated_client: TestClient):
        """Dues summary Excel generates successfully."""
        response = authenticated_client.get("/reports/dues/summary?format=excel")
        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]

    def test_dues_summary_with_year(self, authenticated_client: TestClient):
        """Dues summary accepts year parameter."""
        response = authenticated_client.get("/reports/dues/summary?format=pdf&year=2025")
        assert response.status_code == 200

    def test_overdue_report_pdf(self, authenticated_client: TestClient):
        """Overdue report PDF generates successfully."""
        response = authenticated_client.get("/reports/dues/overdue?format=pdf")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_overdue_report_excel(self, authenticated_client: TestClient):
        """Overdue report Excel generates successfully."""
        response = authenticated_client.get("/reports/dues/overdue?format=excel")
        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]
```

---

## Verification

```bash
# Run tests
pytest src/tests/test_reports.py -v

# Test manually
# 1. Navigate to /reports
# 2. Click PDF for Member Roster - should download PDF
# 3. Click Excel for Member Roster - should download XLSX
# 4. Click PDF for Dues Summary - should download PDF
# 5. Click Excel for Dues Summary - should download XLSX
# 6. Click Overdue Report - verify both formats

# Commit
git add -A
git commit -m "feat(reports): add member and dues reports

- Add member roster report (PDF/Excel)
- Add dues summary report by year
- Add overdue members report
- Add PDF templates for all reports
- Add member/dues report tests"
```

---

## Session B Complete

**Created:**
- `src/templates/reports/member_roster.html`
- `src/templates/reports/dues_summary.html`
- `src/templates/reports/overdue_report.html`

**Modified:**
- `src/routers/reports.py` (member/dues routes)
- `src/tests/test_reports.py` (member/dues tests)

**Next:** Session C - Training & Operations Reports
