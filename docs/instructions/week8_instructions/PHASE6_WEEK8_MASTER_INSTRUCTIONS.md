# Phase 6 Week 8: Reports & Export — Master Instructions

**Version:** 0.7.6 → 0.7.7
**Estimated Time:** 6-8 hours (3 sessions)
**Prerequisites:** Phase 6 Week 7 complete, ~284 tests passing

---

## Overview

Week 8 implements report generation capabilities:
- PDF generation for certificates and formal reports
- Excel export for data analysis
- Report templates for members, dues, training
- Download infrastructure

This provides leadership with exportable data and printable documents.

---

## Session Breakdown

| Session | Focus | Duration | New Tests |
|---------|-------|----------|-----------|
| A | Report Infrastructure | 2-3 hrs | 6 |
| B | Member & Dues Reports | 2-3 hrs | 8 |
| C | Training & Operations Reports | 2-3 hrs | 6 |

**Total:** ~20 new tests, bringing frontend tests to ~139

---

## Dependencies

Add to `requirements.txt`:
```
weasyprint==60.1      # PDF generation
openpyxl==3.1.2       # Excel generation
```

**Note:** WeasyPrint requires system dependencies:
```bash
# Ubuntu/Debian (in Dockerfile)
apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0
```

---

## Architecture

### ReportService Pattern
```python
class ReportService:
    """Base class for report generation."""

    @staticmethod
    def generate_pdf(template: str, context: dict) -> bytes:
        """Generate PDF from HTML template."""
        pass

    @staticmethod
    def generate_excel(data: list[dict], columns: list[str]) -> bytes:
        """Generate Excel from data."""
        pass
```

### Report Types

| Report | Format | Description |
|--------|--------|-------------|
| Member Roster | PDF/Excel | All members with contact info |
| Dues Summary | PDF/Excel | Period collection summary |
| Overdue Report | PDF/Excel | Members with overdue dues |
| Training Completion | PDF | Individual certificates |
| Course Enrollment | Excel | Students per course |
| Grievance Summary | PDF | Open/closed grievances |
| SALTing Report | Excel | Activities with outcomes |

---

## File Structure

```
src/
├── services/
│   └── report_service.py            # NEW: Report generation
├── routers/
│   └── reports.py                   # NEW: Report routes
├── templates/
│   └── reports/
│       ├── base_pdf.html            # PDF base template
│       ├── member_roster.html       # Member roster PDF
│       ├── dues_summary.html        # Dues summary PDF
│       ├── training_certificate.html # Certificate template
│       └── grievance_summary.html   # Grievance PDF
└── tests/
    └── test_reports.py              # NEW: ~20 tests
```

---

## Routes to Implement

| Route | Method | Format | Description |
|-------|--------|--------|-------------|
| `/reports` | GET | HTML | Reports landing page |
| `/reports/members/roster` | GET | PDF/Excel | Member roster |
| `/reports/dues/summary` | GET | PDF/Excel | Dues period summary |
| `/reports/dues/overdue` | GET | PDF/Excel | Overdue members |
| `/reports/training/certificate/{student_id}` | GET | PDF | Completion certificate |
| `/reports/training/enrollment` | GET | Excel | Course enrollments |
| `/reports/operations/grievances` | GET | PDF | Grievance summary |
| `/reports/operations/salting` | GET | Excel | SALTing activities |

Query parameter `?format=pdf` or `?format=excel` determines output.

---

## Session Documents

1. `1-SESSION-A-REPORT-INFRASTRUCTURE.md` — Base service, PDF/Excel generation
2. `2-SESSION-B-MEMBER-DUES-REPORTS.md` — Member roster, dues reports
3. `3-SESSION-C-TRAINING-OPERATIONS-REPORTS.md` — Certificates, grievance reports

---

## Success Criteria

After Week 8:
- [ ] Reports landing page with available reports
- [ ] Member roster (PDF/Excel)
- [ ] Dues summary (PDF/Excel)
- [ ] Overdue members report
- [ ] Training completion certificates
- [ ] Course enrollment export
- [ ] Grievance summary
- [ ] ~304 total tests (~139 frontend)
- [ ] ADR-012: Report Generation Patterns
- [ ] v0.7.7 tagged

---

*Execute sessions in order. Each session builds on the previous.*
