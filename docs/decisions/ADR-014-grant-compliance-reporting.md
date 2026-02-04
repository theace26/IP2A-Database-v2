# ADR-014: Grant Compliance Reporting System

> **Document Created:** 2026-02-02
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Implemented — Grant tracking and compliance reporting live since Week 14

## Status
Implemented

## Date
2026-02-02

## Context

The IP2A (Inside to Pre-Apprenticeship) program receives funding from multiple grant sources including:
- Department of Labor (DOL) grants
- State workforce development funds
- Private foundation grants
- Industry association sponsorships

Each grant has compliance requirements including:
- Enrollment tracking (who is funded by which grant)
- Outcome tracking (completion, certification, job placement)
- Financial tracking (expenses against grant budgets)
- Regular reporting (monthly, quarterly, annual)

Without proper tracking and reporting infrastructure:
- Staff manually compile reports from multiple data sources
- Risk of compliance violations from incomplete data
- Difficulty demonstrating grant effectiveness
- Potential for lost or delayed funding

## Decision

We will implement a comprehensive grant tracking and compliance reporting system with:

### 1. Enhanced Grant Model

Add tracking fields to the Grant model:
- `status` — Grant lifecycle (pending, active, completed, closed, suspended)
- `target_enrollment` — Target number of students
- `target_completion` — Target program completions
- `target_placement` — Target job/apprenticeship placements

### 2. GrantEnrollment Model

Create association model to track which students are funded by which grants:
- Links Student to Grant with many-to-many relationship
- Tracks enrollment date and status progression
- Records outcomes (completion, credential, placement)
- Captures placement details (employer, wage, job title)

### 3. Grant Metrics Service

Implement `GrantMetricsService` for calculating:
- Enrollment statistics (total, active, completed, attrition)
- Financial metrics (budget, spent, remaining, utilization rate)
- Outcome breakdowns (by outcome type)
- Progress toward targets (enrollment, completion, placement)
- Dashboard-level aggregations

### 4. Grant Report Service

Implement `GrantReportService` for generating:
- **Summary Reports** — Executive overview for internal use
- **Detailed Reports** — Student-level data with all metrics
- **Funder Reports** — Formatted for funder submission requirements
- **Excel Export** — Multi-sheet workbook with summary, enrollments, expenses

### 5. Frontend Dashboard

Create grant management UI with:
- Grant list with summary cards
- Individual grant dashboards with progress visualizations
- Enrollment management interface
- Expense tracking views
- Report generation and download

## Implementation Status

| Component | Status | Week | Notes |
|-----------|--------|------|-------|
| Grant model enhancements (status, targets) | ✅ | 14 | GrantStatus enum |
| GrantEnrollment model | ✅ | 14 | Student-Grant association with outcomes |
| GrantEnrollmentStatus enum | ✅ | 14 | enrolled → active → completed/withdrawn/dropped |
| GrantOutcome enum | ✅ | 14 | 7 outcome types |
| GrantMetricsService | ✅ | 14 | Retention, utilization, progress calculations |
| GrantReportService | ✅ | 14 | Summary, detailed, funder, Excel formats |
| Grant API endpoints | ✅ | 14 | CRUD + metrics + reports |
| Grant frontend dashboard | ✅ | 14 | Progress visualizations, stats cards |
| Enrollment management UI | ✅ | 14 | Add/update enrollment, record outcomes |
| Excel export (openpyxl) | ✅ | 14 | Multi-sheet workbook generation |
| ~20 grant compliance tests | ✅ | 14 | Metrics, reports, enrollment lifecycle |
| Grant analytics (Chart.js) | ✅ | 19 | Enrollment trends, outcome breakdowns |
| Automated report scheduling | 🔜 | — | Future: email delivery on schedule |

### Enum Values (Implemented)

```python
class GrantStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CLOSED = "closed"
    SUSPENDED = "suspended"

class GrantEnrollmentStatus(str, Enum):
    ENROLLED = "enrolled"
    ACTIVE = "active"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"
    DROPPED = "dropped"

class GrantOutcome(str, Enum):
    COMPLETED_PROGRAM = "completed_program"
    OBTAINED_CREDENTIAL = "obtained_credential"
    ENTERED_APPRENTICESHIP = "entered_apprenticeship"
    OBTAINED_EMPLOYMENT = "obtained_employment"
    CONTINUED_EDUCATION = "continued_education"
    WITHDRAWN = "withdrawn"
    OTHER = "other"
```

### Key Metrics Calculated

| Metric | Formula |
|--------|---------|
| Retention Rate | (Total − Attrition) / Total × 100 |
| Utilization Rate | Spent / Budget × 100 |
| Enrollment Progress | Enrolled / Target Enrollment × 100 |
| Completion Progress | Completed / Target Completion × 100 |
| Placement Progress | Placements / Target Placement × 100 |

### Report Types

| Report | Format | Purpose |
|--------|--------|---------|
| Summary | JSON/HTML | Internal quick overview |
| Detailed | JSON/HTML | Full data with student details |
| Funder | JSON/HTML | Formatted for external submission |
| Excel | XLSX | Multi-sheet downloadable workbook |

## Consequences

### Positive
- Automated compliance data collection eliminates manual compilation
- Real-time progress tracking against grant targets
- Standardized report generation reduces errors
- Single source of truth for grant outcomes
- Enables proactive identification of at-risk grants
- Analytics dashboard provides visual progress tracking (Week 19)

### Negative
- Additional data entry required for enrollment outcomes
- Staff training needed on grant enrollment workflow
- Historical data migration may be needed for existing grants
- More complex student records (linked to multiple tracking systems)

### Neutral
- Expense model (already exists) links to grants via `grant_id` FK
- Report templates may need customization per funder
- Future enhancement: automated report scheduling and email delivery

## Phase 7 Note

The Referral & Dispatch system (Phase 7) may interact with grant compliance tracking — for instance, tracking whether grant-funded students who enter apprenticeship are also captured in the referral/dispatch system. Cross-referencing grant outcomes with LaborPower placement data could strengthen compliance reporting.

## Related Decisions

- ADR-002: Frontend Framework (Jinja2 + HTMX patterns for dashboard)
- ADR-005: CSS Framework (DaisyUI progress components)
- ADR-010: Operations Frontend Patterns (established UI patterns reused here)
- ADR-011: Dues Frontend Patterns (modal and filter patterns reused)
- ADR-013: Stripe Payment Integration (payment processing patterns)

## References

- Week 14 Instruction Document: Grant Module Expansion
- Original IP2A requirements from ChatGPT transfer analysis
- Grant metrics service: `src/services/grant_metrics_service.py`
- Grant report service: `src/services/grant_report_service.py`
- Grant enrollment model: `src/models/grant_enrollment.py`
- Grant enums: `src/db/enums/grant_enums.py`
- Frontend: `src/templates/grants/`
- Tests: `src/tests/test_grant*.py`

---

## 🔄 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (2026-02-02 — original decision record)
