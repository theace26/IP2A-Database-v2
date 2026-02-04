# Week 25 Instructions — Phase 7: API Endpoints

> **Document Created:** February 4, 2026
> **Last Updated:** February 4, 2026
> **Version:** 1.0
> **Status:** Active — Ready for implementation (after Week 24 completes)
> **Project Version:** v0.9.5-alpha (Feature-Complete Weeks 1–19, Phase 7 Weeks 20–24)
> **Phase:** 7 — Referral & Dispatch System
> **Estimated Hours:** 10–12 hours across 3 sessions

---

## Purpose

Paste this document into a new Claude chat (or Claude Code session) to provide full context for Week 25 development. This week creates **FastAPI routers** (API endpoints) for all Phase 7 services. Every router follows the established pattern: `APIRouter` with dependency injection for auth and database sessions, Pydantic schemas for request/response validation, and service-layer delegation for all business logic.

Weeks 20–24 built the complete service layer: 7 services covering all 14 business rules. Week 25 exposes these services as HTTP endpoints.

---

## Project Context (Condensed)

**Project:** IP2A-Database-v2 (UnionCore) — IBEW Local 46 operations management platform
**Replaces:** LaborPower (referral/dispatch), Access Database, QuickBooks (sync)
**Users:** ~40 staff + ~4,000 members | **GitHub:** theace26

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, **FastAPI**, SQLAlchemy 2.x |
| Frontend | Jinja2 + HTMX + Alpine.js + **DaisyUI** (Tailwind CSS) |
| Database | PostgreSQL 16 (Railway) |
| Auth | JWT + bcrypt + HTTP-only cookies (ADR-003) |
| Testing | pytest + httpx |

### Current Metrics (Post-Week 24 — Estimated)

| Metric | Value |
|--------|-------|
| Tests | ~590–620 |
| ORM Models | 32 (26 existing + 6 Phase 7) |
| Phase 7 Services | 7 (ReferralBook, BookRegistration, LaborRequest, JobBid, Dispatch, Queue, Enforcement) |
| ADRs | 15 |

---

## Working Copy & Workflow

- **Working copy (OneDrive):** `D:\OneDrive\Documents\Claude.ai\IP2A-Database-v2\`
- **Live project:** `C:\Users\Xerxes\Projects\IP2A-Database-v2\`
- **Workflow:** Claude outputs files → Xerxes manually copies to live project
- **Branch:** `develop` at v0.9.5-alpha

---

## Prerequisites Checklist

Before starting Week 25, verify:

- [ ] Weeks 20–24 complete — all 7 Phase 7 services exist and pass tests
- [ ] QueueService provides queue snapshots, next-eligible, analytics
- [ ] EnforcementService daily run works (dry-run + live)
- [ ] All 14 business rules implemented in service layer
- [ ] Integration tests covering full dispatch lifecycle pass
- [ ] `pytest -v --tb=short` passes (~590–620 tests green)

---

## Existing Router Patterns (Reference)

Phase 7 routers must follow the same patterns used in Weeks 1–19. Here are the key conventions:

### Router Registration (main.py)

```python
# src/main.py — existing pattern
from fastapi import FastAPI
from src.routers import (
    auth, members, staff, training_frontend,
    member_frontend, operations_frontend, dues_frontend,
    # Phase 7 additions:
    referral_books_api, registration_api, dispatch_api,
)

app = FastAPI(title="IP2A-Database-v2", version="0.9.5")

# ... existing routers ...

# Phase 7 routers
app.include_router(referral_books_api.router)
app.include_router(registration_api.router)
app.include_router(dispatch_api.router)
```

### Router Structure Pattern

```python
# Standard router file pattern (from existing codebase)
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.routers.dependencies.auth import get_current_user
from src.models.user import User

router = APIRouter(
    prefix="/api/v1/referral",
    tags=["Referral & Dispatch"],
)

@router.get("/books", response_model=list[ReferralBookRead])
def list_books(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    classification: str = Query(None),
    region: str = Query(None),
):
    """List all active referral books, optionally filtered."""
    books = ReferralBookService.get_all_active(db, classification=classification, region=region)
    return books
```

### Error Handling Pattern

```python
# Services raise domain exceptions → Routers convert to HTTP
@router.post("/registrations", status_code=status.HTTP_201_CREATED)
def register_member(
    data: BookRegistrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a member on a referral book."""
    try:
        registration = BookRegistrationService.register_member(
            db, member_id=data.member_id, book_id=data.book_id, **data.dict()
        )
        return registration
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
```

### Auth Dependencies

```python
# Two auth modes in the project:
from src.routers.dependencies.auth import get_current_user      # Bearer token (API)
from src.routers.dependencies.auth_cookie import get_current_user_cookie  # Cookie (frontend)

# Phase 7 API routers use bearer token auth
# Phase 7 frontend routers (Week 26) use cookie auth
```

### Testing Pattern

```python
# Tests use httpx TestClient (FastAPI convention)
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_list_books(authenticated_client, seed_books):
    """Test listing referral books."""
    response = authenticated_client.get("/api/v1/referral/books")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 11  # 11 seeded books
```

---

## Week 25 Scope — API Endpoints

### Session 25A: Book & Registration API (3–4 hours)

**Purpose:** CRUD and operational endpoints for referral books and member registrations.

**File to create:** `src/routers/referral_books_api.py`
**File to create:** `src/routers/registration_api.py`

#### Referral Books API — Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/referral/books` | List all active books | Staff |
| GET | `/api/v1/referral/books/{id}` | Get book detail with stats | Staff |
| GET | `/api/v1/referral/books/{id}/queue` | Get book queue (FIFO by APN) | Staff |
| GET | `/api/v1/referral/books/{id}/stats` | Book utilization analytics | Staff |
| POST | `/api/v1/referral/books` | Create new book (admin) | Admin |
| PUT | `/api/v1/referral/books/{id}` | Update book settings | Admin |
| PATCH | `/api/v1/referral/books/{id}/activate` | Activate a book | Admin |
| PATCH | `/api/v1/referral/books/{id}/deactivate` | Deactivate a book | Admin |
| GET | `/api/v1/referral/books/summary` | All books summary with counts | Staff |
| GET | `/api/v1/referral/books/by-classification/{classification}` | Filter books by classification | Staff |

#### Registration API — Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/referral/registrations` | Register member on book | Staff |
| GET | `/api/v1/referral/registrations/{id}` | Get registration detail | Staff |
| POST | `/api/v1/referral/registrations/{id}/re-sign` | Re-sign member (30-day cycle) | Staff |
| POST | `/api/v1/referral/registrations/{id}/resign` | Member voluntarily resigns from book | Staff |
| POST | `/api/v1/referral/registrations/{id}/roll-off` | Roll member off book | Staff |
| POST | `/api/v1/referral/registrations/{id}/exempt` | Grant exempt status | Staff |
| DELETE | `/api/v1/referral/registrations/{id}/exempt` | Revoke exempt status | Staff |
| GET | `/api/v1/referral/registrations/member/{member_id}` | All registrations for a member | Staff |
| GET | `/api/v1/referral/registrations/member/{member_id}/status` | Member queue status (all books) | Staff |
| GET | `/api/v1/referral/registrations/expiring` | Registrations expiring soon | Staff |

#### Expected Code — referral_books_api.py

```python
# src/routers/referral_books_api.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from src.db.session import get_db
from src.routers.dependencies.auth import get_current_user
from src.models.user import User
from src.schemas.referral_book import (
    ReferralBookCreate, ReferralBookUpdate, ReferralBookRead,
    ReferralBookStats, ReferralBookSummary,
)
from src.services.referral_book_service import ReferralBookService
from src.services.queue_service import QueueService

router = APIRouter(
    prefix="/api/v1/referral/books",
    tags=["Referral Books"],
)

@router.get("", response_model=list[ReferralBookRead])
def list_books(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    classification: Optional[str] = Query(None, description="Filter by classification"),
    region: Optional[str] = Query(None, description="Filter by region"),
    active_only: bool = Query(True, description="Show only active books"),
):
    """List referral books with optional filters.

    Supports filtering by classification (wire, technician, etc.)
    and region (seattle, bremerton, pt_angeles).
    """
    if classification and region:
        return ReferralBookService.get_by_classification_and_region(
            db, classification=classification, region=region
        )
    elif classification:
        return ReferralBookService.get_by_classification(db, classification=classification)
    elif region:
        return ReferralBookService.get_by_region(db, region=region)
    elif active_only:
        return ReferralBookService.get_all_active(db)
    else:
        return ReferralBookService.get_all(db)

@router.get("/summary", response_model=list[ReferralBookSummary])
def get_all_books_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Summary of all books with registration counts."""
    return ReferralBookService.get_all_books_summary(db)

@router.get("/{book_id}", response_model=ReferralBookRead)
def get_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get referral book detail."""
    book = ReferralBookService.get_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.get("/{book_id}/queue")
def get_book_queue(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_exempt: bool = Query(False),
):
    """Get the out-of-work queue for a book, ordered by APN (FIFO)."""
    book = ReferralBookService.get_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return QueueService.get_queue_snapshot(db, book_id, include_exempt=include_exempt)

@router.get("/{book_id}/stats", response_model=ReferralBookStats)
def get_book_stats(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get utilization statistics for a book."""
    book = ReferralBookService.get_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return ReferralBookService.get_book_stats(db, book_id)

@router.post("", status_code=status.HTTP_201_CREATED, response_model=ReferralBookRead)
def create_book(
    data: ReferralBookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new referral book (admin only)."""
    # TODO: Add admin role check
    try:
        return ReferralBookService.create_book(db, **data.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ... remaining endpoints follow same pattern
```

#### Expected Code — registration_api.py

```python
# src/routers/registration_api.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.routers.dependencies.auth import get_current_user
from src.models.user import User
from src.schemas.book_registration import (
    BookRegistrationCreate, BookRegistrationRead,
    BookRegistrationWithMember, ExemptRequest, QueuePosition,
)
from src.services.book_registration_service import BookRegistrationService
from src.services.queue_service import QueueService

router = APIRouter(
    prefix="/api/v1/referral/registrations",
    tags=["Referral Registrations"],
)

@router.post("", status_code=status.HTTP_201_CREATED, response_model=BookRegistrationRead)
def register_member(
    data: BookRegistrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a member on a referral book.

    Validates: one registration per classification per member (Rule 5).
    Assigns next APN in sequence.
    """
    try:
        return BookRegistrationService.register_member(
            db, member_id=data.member_id, book_id=data.book_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{registration_id}/re-sign", response_model=BookRegistrationRead)
def re_sign_member(
    registration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-sign member for another 30-day cycle (Rule 7)."""
    try:
        return BookRegistrationService.re_sign_member(db, registration_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{registration_id}/exempt", response_model=BookRegistrationRead)
def grant_exempt_status(
    registration_id: int,
    data: ExemptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Grant exempt status to a registration (Rule 14).

    Exempt reasons: military, medical, union_business, salting,
    jury_duty, training, other.
    """
    try:
        return BookRegistrationService.grant_exempt_status(
            db, registration_id, reason=data.exempt_reason,
            start_date=data.exempt_start_date, end_date=data.exempt_end_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/member/{member_id}/status")
def get_member_queue_status(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get member's status on all books they're registered on.

    Returns position, APN, days_on_book, check marks, re-sign due date
    for each active registration.
    """
    return QueueService.get_member_queue_status(db, member_id)

# ... remaining endpoints follow same pattern
```

#### Test Scenarios for Session 25A

| Test | Endpoint | Asserts |
|------|----------|---------|
| List all active books | GET /books | 200, returns 11 books |
| List books filtered by classification | GET /books?classification=wire | 200, returns 3 Wire books |
| Get book detail | GET /books/{id} | 200, correct book data |
| Get book queue | GET /books/{id}/queue | 200, ordered by APN |
| Get nonexistent book | GET /books/99999 | 404 |
| Create book (admin) | POST /books | 201, book created |
| Create duplicate book | POST /books | 400 |
| Register member | POST /registrations | 201, APN assigned |
| Duplicate registration | POST /registrations | 400, "already registered" |
| Re-sign member | POST /registrations/{id}/re-sign | 200, re-sign date updated |
| Re-sign expired registration | POST /registrations/{id}/re-sign | 400 |
| Grant exempt status | POST /registrations/{id}/exempt | 200, exempt applied |
| Get member queue status | GET /registrations/member/{id}/status | 200, all books listed |
| Get expiring registrations | GET /registrations/expiring | 200, approaching deadline |

**Test target for 25A:** +15–18 tests

---

### Session 25B: LaborRequest & Bid API (3–4 hours)

**Purpose:** Endpoints for employer labor requests and the online bidding workflow.

**File to create:** `src/routers/labor_request_api.py`
**File to create:** `src/routers/job_bid_api.py`

#### LaborRequest API — Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/referral/requests` | Create labor request | Staff |
| GET | `/api/v1/referral/requests` | List requests (filtered) | Staff |
| GET | `/api/v1/referral/requests/{id}` | Get request detail | Staff |
| PUT | `/api/v1/referral/requests/{id}` | Update open request | Staff |
| POST | `/api/v1/referral/requests/{id}/cancel` | Cancel request | Staff |
| GET | `/api/v1/referral/requests/morning` | Morning referral queue | Staff |
| GET | `/api/v1/referral/requests/open` | All unfilled requests | Staff |
| GET | `/api/v1/referral/requests/employer/{employer_id}` | Employer request history | Staff |
| GET | `/api/v1/referral/requests/{id}/bids` | Bids on a request | Staff |

#### Job Bid API — Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/referral/bids` | Place bid on request | Staff/Member |
| GET | `/api/v1/referral/bids/{id}` | Get bid detail | Staff |
| POST | `/api/v1/referral/bids/{id}/withdraw` | Withdraw pending bid | Staff/Member |
| POST | `/api/v1/referral/bids/{id}/accept` | Accept bid (staff) | Staff |
| POST | `/api/v1/referral/bids/{id}/reject` | Reject accepted bid | Staff/Member |
| POST | `/api/v1/referral/requests/{id}/process-bids` | Process all bids for request | Staff |
| GET | `/api/v1/referral/bids/member/{member_id}` | Member bid history | Staff |
| GET | `/api/v1/referral/bids/member/{member_id}/suspension` | Check suspension status | Staff |

#### Expected Code — labor_request_api.py

```python
# src/routers/labor_request_api.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from src.db.session import get_db
from src.routers.dependencies.auth import get_current_user
from src.models.user import User
from src.schemas.labor_request import (
    LaborRequestCreate, LaborRequestUpdate, LaborRequestRead,
)
from src.services.labor_request_service import LaborRequestService

router = APIRouter(
    prefix="/api/v1/referral/requests",
    tags=["Labor Requests"],
)

@router.post("", status_code=status.HTTP_201_CREATED, response_model=LaborRequestRead)
def create_request(
    data: LaborRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new labor request from an employer.

    Validates cutoff time (Rule 3): requests after 3 PM go to next day.
    Pre-calculates generates_checkmark flag (Rule 11).
    """
    try:
        request = LaborRequestService.create_request(
            db,
            employer_id=data.employer_id,
            book_id=data.book_id,
            workers_requested=data.workers_requested,
            **data.dict(exclude={"employer_id", "book_id", "workers_requested"}),
        )
        return request
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/morning")
def get_morning_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
):
    """Get all requests ready for morning referral, ordered by classification time.

    Rule 2: Wire 8:30 AM → S&C/Marine/Stock/LFM/Residential 9:00 AM → Tradeshow 9:30 AM
    """
    return LaborRequestService.get_requests_for_morning(db, target_date=target_date)

@router.get("/open")
def get_open_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    book_id: Optional[int] = Query(None),
    classification: Optional[str] = Query(None),
):
    """List all unfilled labor requests."""
    return LaborRequestService.get_open_requests(
        db, book_id=book_id, classification=classification
    )

@router.post("/{request_id}/cancel")
def cancel_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel an open labor request."""
    try:
        return LaborRequestService.cancel_request(db, request_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

#### Expected Code — job_bid_api.py

```python
# src/routers/job_bid_api.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.routers.dependencies.auth import get_current_user
from src.models.user import User
from src.schemas.job_bid import JobBidCreate, JobBidRead
from src.services.job_bid_service import JobBidService

router = APIRouter(
    prefix="/api/v1/referral/bids",
    tags=["Job Bids"],
)

@router.post("", status_code=status.HTTP_201_CREATED, response_model=JobBidRead)
def place_bid(
    data: JobBidCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Place a bid on a labor request.

    Rule 8: Only valid during bidding window (5:30 PM – 7:00 AM).
    Validates: active registration, not suspended, no duplicate bid.
    """
    try:
        return JobBidService.place_bid(
            db,
            member_id=data.member_id,
            labor_request_id=data.labor_request_id,
            registration_id=data.registration_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{bid_id}/reject")
def reject_bid(
    bid_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject an accepted bid. Counts as quit (Rule 8/12).

    WARNING: 2nd rejection in 12 months = 1-year bidding suspension.
    """
    try:
        return JobBidService.reject_bid(db, bid_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/member/{member_id}/suspension")
def check_suspension(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if member has active bidding suspension.

    Returns: is_suspended, suspended_until, rejections_in_window,
    next_rejection_causes_suspension.
    """
    return JobBidService.check_suspension_status(db, member_id)
```

#### Test Scenarios for Session 25B

| Test | Endpoint | Asserts |
|------|----------|---------|
| Create labor request | POST /requests | 201, request created |
| Create request after 3 PM | POST /requests | 200 but flagged for next day |
| Get morning requests | GET /requests/morning | 200, ordered by classification time |
| Get open requests | GET /requests/open | 200, only unfilled |
| Cancel request | POST /requests/{id}/cancel | 200, status CANCELLED |
| Cancel already filled request | POST /requests/{id}/cancel | 400 |
| Get employer history | GET /requests/employer/{id} | 200, list of requests |
| Place bid during window | POST /bids | 201, bid PENDING |
| Place bid outside window | POST /bids | 400, "outside bidding window" |
| Place bid while suspended | POST /bids | 400, "bidding suspended" |
| Reject bid — first time | POST /bids/{id}/reject | 200, warning |
| Process bids for request | POST /requests/{id}/process-bids | 200, FIFO result |
| Check suspension — clean | GET /bids/member/{id}/suspension | 200, not suspended |
| Member bid history | GET /bids/member/{id} | 200, ordered by date |

**Test target for 25B:** +14–17 tests

---

### Session 25C: Dispatch & Admin API (3–4 hours)

**Purpose:** Dispatch workflow endpoints and admin operations (enforcement triggers, queue management).

**File to create:** `src/routers/dispatch_api.py`
**Modify:** `src/main.py` (register all Phase 7 routers)

#### Dispatch API — Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/referral/dispatch` | Dispatch member from queue | Staff |
| POST | `/api/v1/referral/dispatch/by-name` | Foreperson-by-name dispatch | Staff |
| GET | `/api/v1/referral/dispatch/{id}` | Get dispatch detail | Staff |
| POST | `/api/v1/referral/dispatch/{id}/check-in` | Record member check-in | Staff |
| POST | `/api/v1/referral/dispatch/{id}/terminate` | Terminate dispatch | Staff |
| GET | `/api/v1/referral/dispatch/active` | All active dispatches | Staff |
| GET | `/api/v1/referral/dispatch/member/{member_id}` | Member dispatch history | Staff |
| GET | `/api/v1/referral/dispatch/book/{book_id}/stats` | Book dispatch stats | Staff |

#### Admin/Queue API — Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/referral/queue/{book_id}` | Queue snapshot for book | Staff |
| GET | `/api/v1/referral/queue/{book_id}/depth` | Queue depth analytics | Staff |
| GET | `/api/v1/referral/queue/classification-summary` | Cross-book classification summary | Staff |
| POST | `/api/v1/referral/admin/enforcement/run` | Trigger daily enforcement | Admin |
| GET | `/api/v1/referral/admin/enforcement/preview` | Dry-run enforcement preview | Admin |
| GET | `/api/v1/referral/admin/re-sign-reminders` | Upcoming re-sign deadlines | Staff |

#### Expected Code — dispatch_api.py

```python
# src/routers/dispatch_api.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from src.db.session import get_db
from src.routers.dependencies.auth import get_current_user
from src.models.user import User
from src.schemas.dispatch import (
    DispatchCreate, DispatchRead, DispatchTerminate, DispatchCheckIn,
)
from src.services.dispatch_service import DispatchService
from src.services.queue_service import QueueService
from src.services.enforcement_service import EnforcementService
from src.db.enums.phase7_enums import TermReason

router = APIRouter(
    prefix="/api/v1/referral",
    tags=["Dispatch"],
)

# --- Dispatch Operations ---

@router.post("/dispatch", status_code=status.HTTP_201_CREATED, response_model=DispatchRead)
def create_dispatch(
    data: DispatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dispatch next eligible member from queue to a labor request.

    Selects member by FIFO (APN order), Book 1 before Book 2.
    Creates dispatch record, marks registration as DISPATCHED.
    """
    try:
        dispatch = DispatchService.dispatch_from_queue(db, data.labor_request_id)
        if not dispatch:
            raise HTTPException(
                status_code=404,
                detail="No eligible members available for dispatch"
            )
        return dispatch
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/dispatch/by-name", status_code=status.HTTP_201_CREATED, response_model=DispatchRead)
def dispatch_by_name(
    data: DispatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Foreperson-by-name dispatch (Rule 13).

    Validates no active blackout period and anti-collusion rules.
    """
    try:
        return DispatchService.dispatch_by_name(
            db,
            labor_request_id=data.labor_request_id,
            member_id=data.member_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/dispatch/{dispatch_id}/terminate")
def terminate_dispatch(
    dispatch_id: int,
    data: DispatchTerminate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Terminate a dispatch.

    Routes by reason:
    - QUIT/DISCHARGED: Roll off ALL books, 2-week blackout (Rule 12)
    - RIF: Standard termination, no penalty
    - SHORT_CALL_END: Restore queue position (Rule 9)
    """
    try:
        return DispatchService.terminate_dispatch(
            db, dispatch_id, term_reason=data.term_reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/dispatch/active")
def get_active_dispatches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    book_id: Optional[int] = Query(None),
):
    """List all currently active dispatches."""
    return DispatchService.get_active_dispatches(db, book_id=book_id)

# --- Queue Operations ---

@router.get("/queue/{book_id}")
def get_queue_snapshot(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_exempt: bool = Query(False),
):
    """Full queue snapshot for a book, ordered by APN."""
    return QueueService.get_queue_snapshot(db, book_id, include_exempt=include_exempt)

@router.get("/queue/{book_id}/depth")
def get_queue_depth(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Queue depth analytics: total, active, exempt, by tier."""
    return QueueService.get_queue_depth(db, book_id)

@router.get("/queue/classification-summary")
def get_classification_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cross-book summary grouped by classification."""
    return QueueService.get_classification_summary(db)

# --- Admin Operations ---

@router.post("/admin/enforcement/run")
def run_enforcement(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    dry_run: bool = Query(False, description="Preview without making changes"),
):
    """Trigger daily enforcement run.

    Processes: expired re-signs, expired exemptions, expired blackouts,
    expired suspensions, unfilled requests.
    """
    # TODO: Add admin role check
    return EnforcementService.daily_enforcement_run(db, dry_run=dry_run)

@router.get("/admin/enforcement/preview")
def preview_enforcement(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview what enforcement would do without making changes."""
    return EnforcementService.get_enforcement_report(db)

@router.get("/admin/re-sign-reminders")
def get_re_sign_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(7, description="Days until re-sign deadline"),
):
    """List registrations approaching re-sign deadline."""
    return BookRegistrationService.get_registrations_expiring_soon(db, days=days)
```

#### main.py Modification

```python
# Add to src/main.py — Phase 7 router registration
from src.routers import (
    referral_books_api,
    registration_api,
    labor_request_api,
    job_bid_api,
    dispatch_api,
)

# Phase 7: Referral & Dispatch
app.include_router(referral_books_api.router)
app.include_router(registration_api.router)
app.include_router(labor_request_api.router)
app.include_router(job_bid_api.router)
app.include_router(dispatch_api.router)
```

#### Test Scenarios for Session 25C

| Test | Endpoint | Asserts |
|------|----------|---------|
| Dispatch from queue | POST /dispatch | 201, member dispatched |
| Dispatch from empty queue | POST /dispatch | 404, no eligible members |
| Dispatch by name — valid | POST /dispatch/by-name | 201 |
| Dispatch by name — blackout | POST /dispatch/by-name | 400 |
| Terminate — quit | POST /dispatch/{id}/terminate | 200, rolled off all books |
| Terminate — short call | POST /dispatch/{id}/terminate | 200, position restored |
| Get active dispatches | GET /dispatch/active | 200, only active |
| Get member dispatch history | GET /dispatch/member/{id} | 200, ordered by date |
| Get queue snapshot | GET /queue/{book_id} | 200, APN ordered |
| Get queue depth | GET /queue/{book_id}/depth | 200, correct counts |
| Classification summary | GET /queue/classification-summary | 200 |
| Run enforcement (dry run) | POST /admin/enforcement/run?dry_run=true | 200, no changes |
| Run enforcement (live) | POST /admin/enforcement/run | 200, changes committed |
| Preview enforcement | GET /admin/enforcement/preview | 200 |
| Re-sign reminders | GET /admin/re-sign-reminders | 200, approaching deadlines |
| All Phase 7 routers registered in main.py | Verify imports | No import errors |

**Test target for 25C:** +16–19 tests

---

## Architecture Reminders

- **FastAPI — NOT Flask.** APIRouter, Depends, HTTPException, status codes. Use uvicorn for server.
- **Services raise domain exceptions → Routers convert to HTTP.** Services raise `ValueError` (→ 400), `LookupError` (→ 404). Routers catch and wrap in `HTTPException`.
- **Auth dependency injection.** Use `Depends(get_current_user)` for bearer token auth. Frontend routes (Week 26) use `Depends(get_current_user_cookie)`.
- **Pydantic schemas for validation.** All request bodies use schemas from `src/schemas/`. Response models enforce output shape.
- **APN is DECIMAL(10,2).** Queue endpoints return `registration_number` as string or Decimal — never truncate.
- **Dual audit.** Services write to RegistrationActivity + audit_logs automatically. Routers don't need to handle audit.

---

## Session Checklist

### Before Each Session
- [ ] `git checkout develop && git pull origin develop`
- [ ] `pytest -v --tb=short` — verify all tests pass
- [ ] Review this document for the current session's scope

### After Each Session
- [ ] All new tests pass (`pytest -v`)
- [ ] Code formatted (`ruff check . --fix && ruff format .`)
- [ ] `git add . && git commit -m "feat(phase7): [session description]"`
- [ ] `git push origin develop`

---

## Week 25 Completion Criteria

- [ ] `src/routers/referral_books_api.py` — 10 endpoints for book CRUD and queries
- [ ] `src/routers/registration_api.py` — 10 endpoints for registration operations
- [ ] `src/routers/labor_request_api.py` — 9 endpoints for request lifecycle
- [ ] `src/routers/job_bid_api.py` — 8 endpoints for bidding workflow
- [ ] `src/routers/dispatch_api.py` — 14 endpoints for dispatch, queue, admin
- [ ] All Phase 7 routers registered in `src/main.py`
- [ ] API endpoints documented via FastAPI auto-docs (`/docs`)
- [ ] Error handling follows pattern: services raise ValueError/LookupError → routers convert to HTTPException
- [ ] All tests pass
- [ ] ~640–670 total tests (was ~590–620, target +45–55)
- [ ] API endpoints count jumps from ~150 to ~200+

---

## What Comes After

| Week | Focus | Status |
|------|-------|--------|
| 20–22 | Models, Enums, Schemas, Registration Services | ✅ Complete |
| 23 | Dispatch Services (LaborRequest, JobBid, Dispatch) | ✅ Complete |
| 24 | Queue Management (QueueService, enforcement, analytics) | ✅ Complete |
| **25** | **API Endpoints (Routers for all Phase 7 services)** | **← YOU ARE HERE** |
| 26 | Frontend — Books & Registration UI | 🔜 Next |
| 27 | Frontend — Dispatch Workflow UI | 🔜 Pending |
| 28 | Frontend — Reports Navigation & Dashboard | 🔜 Pending |
| 29–32+ | Report Sprints (78 reports across P0–P3) | 🔜 Pending |

---

## Related Documents

| Document | Location |
|----------|----------|
| Week 23 Instructions | `docs/instructions/WEEK_23_INSTRUCTIONS.md` |
| Week 24 Instructions | `docs/instructions/WEEK_24_INSTRUCTIONS.md` |
| Phase 7 Continuity Doc | `docs/phase7/PHASE7_CONTINUITY_DOC.md` |
| ADR-015 (Referral Architecture) | `docs/decisions/ADR-015-referral-dispatch-architecture.md` |
| ADR-003 (Authentication) | `docs/decisions/ADR-003-authentication-strategy.md` |
| Backend Roadmap v3.1 | `docs/IP2A_BACKEND_ROADMAP.md` |

---

## End-of-Session Documentation (MANDATORY)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

---

## Known Pitfalls (Carry Forward)

- ❌ Flask / flask run / Blueprints → ✅ **FastAPI / uvicorn / APIRouter**
- ❌ Grafana / Loki → ✅ **Sentry** (ADR-007)
- ❌ Missing DaisyUI references → ✅ Always mention DaisyUI with frontend stack
- ❌ `is_locked` → ✅ `locked_until` (datetime, not boolean)
- ❌ 7 contract codes → ✅ **8** (RESIDENTIAL is the 8th)
- ❌ 80–120 hrs Phase 7 → ✅ **100–150 hrs**
- ❌ Week 15 "missing" → ✅ Intentionally skipped (14→16)
- ❌ APN as INTEGER → ✅ **DECIMAL(10,2)** — preserves FIFO ordering
- ❌ Services raising HTTP exceptions → ✅ Services raise **domain exceptions**. Routers handle HTTP.
- ❌ 14 ADRs → ✅ **15 ADRs** (ADR-015 added February 4, 2026)
- ❌ `response.json` → ✅ Use `response.json()` (FastAPI TestClient via httpx)

---

*Week 25 Instructions — Phase 7: API Endpoints*
*Created: February 4, 2026*
*Project Version: v0.9.5-alpha*
