# Phase 2 Quick Reference — Union Operations

> **Document Created:** January 28, 2026
> **Last Updated:** February 3, 2026
> **Version:** 1.1
> **Status:** Active — Implemented (Phase 2, v0.3.0)
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)
> **Related ADRs:** [ADR-005](../decisions/ADR-005-phase2-union-operations.md)

Quick reference for Phase 2 Union Operations models, endpoints, and usage.

> **Context:** Phase 2 models were introduced at v0.3.0 and remain stable through v0.9.4-alpha.
> The project now uses Flask Blueprints (not FastAPI APIRouter). All endpoints below are served
> via Flask and rendered with Jinja2 + HTMX + Alpine.js + DaisyUI where applicable.

---

## Models

### SALTing Activity
Track organizing campaigns at non-union employers.

**Fields:**
- `id` — Primary key
- `member_id` — Organizer (FK to members)
- `organization_id` — Target employer (FK to organizations)
- `activity_type` — Type of activity (enum)
- `activity_date` — When activity occurred
- `outcome` — Result (enum, nullable)
- `location` — Where activity took place
- `workers_contacted` — Number of workers contacted
- `cards_signed` — Number of authorization cards signed
- `description` — Activity description
- `notes` — Additional notes

**Activity Types:**
- `outreach` — Initial contact
- `site_visit` — Facility visit
- `leafleting` — Literature distribution
- `one_on_one` — Personal meetings
- `meeting` — Group meetings
- `petition_drive` — Petition collection
- `card_signing` — Authorization cards
- `information_session` — Educational sessions
- `other` — Other activities

**Outcomes:**
- `positive` — Favorable response
- `neutral` — Neutral response
- `negative` — Unfavorable response
- `no_contact` — No contact made

**Endpoints:**
```
POST   /salting-activities/
GET    /salting-activities/
GET    /salting-activities/{id}
PUT    /salting-activities/{id}
DELETE /salting-activities/{id}
```

---

### Benevolence Application
Financial assistance requests from members.

**Fields:**
- `id` — Primary key
- `member_id` — Applicant (FK to members)
- `application_date` — Submission date
- `reason` — Assistance reason (enum)
- `description` — Detailed explanation
- `amount_requested` — Amount requested (Decimal)
- `status` — Application status (enum)
- `approved_amount` — Amount approved (Decimal, nullable)
- `payment_date` — Payment date (nullable)
- `payment_method` — Payment method (nullable)
- `notes` — Additional notes

**Reasons:**
- `medical` — Medical expenses ($500–$5,000)
- `death_in_family` — Funeral expenses ($1,000–$3,000)
- `disaster` — Natural disaster ($1,000–$7,500)
- `hardship` — Financial hardship ($200–$2,000)
- `other` — Other needs ($100–$1,000)

**Statuses:**
- `draft` — Being prepared
- `submitted` — Awaiting review
- `under_review` — Currently being reviewed
- `approved` — Approved for payment
- `paid` — Payment issued
- `denied` — Application denied

**Endpoints:**
```
POST   /benevolence-applications/
GET    /benevolence-applications/
GET    /benevolence-applications/{id}
PUT    /benevolence-applications/{id}
DELETE /benevolence-applications/{id}
```

---

### Benevolence Review
Review steps in approval workflow.

**Fields:**
- `id` — Primary key
- `application_id` — Application being reviewed (FK)
- `reviewer_name` — Reviewer name (Text)
- `review_level` — Level of review (enum)
- `decision` — Review decision (enum)
- `review_date` — Date of review
- `comments` — Reviewer comments

**Review Levels:**
- `vp` — Vice President
- `admin` — Administrator
- `manager` — Manager
- `president` — President

**Decisions:**
- `approved` — Approved at this level
- `denied` — Denied at this level
- `needs_info` — More information needed
- `deferred` — Escalated to next level

**Endpoints:**
```
POST   /benevolence-reviews/
GET    /benevolence-reviews/
GET    /benevolence-reviews/{id}
GET    /benevolence-reviews/application/{application_id}
PUT    /benevolence-reviews/{id}
DELETE /benevolence-reviews/{id}
```

---

### Grievance
Formal complaints against employers.

**Fields:**
- `id` — Primary key
- `grievance_number` — Unique identifier (e.g., GR-2026-0001)
- `member_id` — Grievant (FK to members)
- `employer_id` — Employer (FK to organizations)
- `filed_date` — Filing date
- `incident_date` — When incident occurred
- `contract_article` — Contract provision violated
- `violation_description` — What happened
- `remedy_sought` — Requested remedy
- `current_step` — Current grievance step (enum)
- `status` — Grievance status (enum)
- `assigned_rep` — Assigned representative
- `resolution` — Resolution description (nullable)
- `resolution_date` — Resolution date (nullable)
- `settlement_amount` — Settlement amount (Decimal, nullable)
- `notes` — Additional notes

**Steps:**
- `step_1` — Initial meeting
- `step_2` — Second level
- `step_3` — Third level
- `arbitration` — Arbitration hearing

**Statuses:**
- `open` — Just filed
- `investigation` — Under investigation
- `hearing` — In hearing process
- `settled` — Settled
- `withdrawn` — Withdrawn
- `arbitration` — In arbitration
- `closed` — Closed

**Common Violation Types:**
- Overtime distribution
- Safety violations
- Wrongful termination
- Wage disputes
- Seniority violations
- Break time violations
- Discrimination
- Subcontracting
- Misclassification
- Benefits denial

**Endpoints:**
```
POST   /grievances/
GET    /grievances/
GET    /grievances/{id}
GET    /grievances/number/{grievance_number}
POST   /grievances/{id}/steps
GET    /grievances/{id}/steps
PUT    /grievances/{id}
DELETE /grievances/{id}
```

---

### Grievance Step Record
Record of meetings at each grievance step.

**Fields:**
- `id` — Primary key
- `grievance_id` — Grievance (FK)
- `step_number` — Step number (1–4)
- `meeting_date` — Meeting date
- `union_attendees` — Union representatives
- `employer_attendees` — Employer representatives
- `outcome` — Step outcome (enum)
- `notes` — Meeting notes

**Outcomes:**
- `denied` — Denied at this step
- `settled` — Settled at this step
- `advanced` — Advanced to next step

**Typical Attendees by Step:**

**Step 1:**
- Union: Shop Steward
- Employer: Foreman, Superintendent

**Step 2:**
- Union: Business Representative, Shop Steward
- Employer: Project Manager, HR Representative

**Step 3:**
- Union: Business Manager, Business Representative
- Employer: HR Director, Legal Counsel

**Step 4 (Arbitration):**
- Union: Business Manager, Legal Counsel, Business Representative
- Employer: Legal Counsel, HR Director, Company Representative

---

## Seed Data

### Generate Phase 2 Test Data

**Using ip2adb CLI (preferred):**
```bash
./ip2adb seed
```

**Standalone (legacy):**
```bash
python -m src.seed.phase2_seed
```

**With Full Database:**
```bash
python -m src.seed.run_seed
```

**What Gets Created:**
- 30 SALTing activities at 13 employers
- 25 benevolence applications
- 47 benevolence reviews (multi-level)
- 20 grievances with unique numbers
- 31 grievance step records

---

## Database Queries

### Common Queries

**Active SALTing campaigns:**
```python
activities = db.query(SALTingActivity)\
    .filter(SALTingActivity.outcome == None)\
    .all()
```

**Pending benevolence applications:**
```python
pending = db.query(BenevolenceApplication)\
    .filter(BenevolenceApplication.status.in_([
        BenevolenceStatus.SUBMITTED,
        BenevolenceStatus.UNDER_REVIEW
    ]))\
    .all()
```

**Open grievances:**
```python
open_grievances = db.query(Grievance)\
    .filter(Grievance.status.in_([
        GrievanceStatus.OPEN,
        GrievanceStatus.INVESTIGATION,
        GrievanceStatus.HEARING
    ]))\
    .all()
```

**Grievances by number:**
```python
grievance = db.query(Grievance)\
    .filter(Grievance.grievance_number == "GR-2026-0001")\
    .first()
```

---

## Enums Import

```python
from src.db.enums import (
    SALTingActivityType,
    SALTingOutcome,
    BenevolenceReason,
    BenevolenceStatus,
    BenevolenceReviewLevel,
    BenevolenceReviewDecision,
    GrievanceStatus,
    GrievanceStep,
    GrievanceStepOutcome,
)
```

---

## Models Import

```python
from src.models import (
    SALTingActivity,
    BenevolenceApplication,
    BenevolenceReview,
    Grievance,
    GrievanceStepRecord,
)
```

---

## Migrations

**Apply Phase 2 migrations:**
```bash
alembic upgrade head
```

**Phase 2 migration IDs:**
- `bc1f99c730dc` — Add Phase 2 union operations models
- `6f77d764d2c3` — Add file_category to file_attachments

---

## Testing

**Run Phase 2 tests:**
```bash
pytest src/tests/test_salting_activities.py -v
pytest src/tests/test_benevolence_applications.py -v
pytest src/tests/test_benevolence_reviews.py -v
pytest src/tests/test_grievances.py -v
```

**All tests (~470 total across all phases):**
```bash
pytest -v
```

---

## Cross-References

| Document | Location |
|----------|----------|
| Project README | `/README.md` |
| Audit API Reference | `/docs/reference/audit-api.md` |
| Dues Tracking API | `/docs/reference/dues-api.md` |
| Phase 7 Planning | `/docs/planning/PHASE_7_MASTER_PLAN.md` |
| ADR-005: Phase 2 Union Operations | `/docs/decisions/ADR-005-phase2-union-operations.md` |
| Seed Code | `/src/seed/phase2_seed.py` |

---

## 📄 End-of-Session Documentation (MANDATORY)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture
> progress made this session. Scan `/docs/*` and make or create any relevant
> updates/documents to keep a historical record as the project progresses.
> Do not forget about ADRs — update as necessary.

---

*Document Version: 1.1*
*Last Updated: February 3, 2026*
