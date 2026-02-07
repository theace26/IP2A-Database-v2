# Spoke 1 Onboarding Context: Core Platform

> **Created:** February 7, 2026
> **Created By:** Spoke 2 (Operations) during Phase 7 close-out
> **Purpose:** Provide Spoke 1 with complete project context for Phase 8A (Square Payment Migration)
> **Reviewed By:** Hub (pending)

---

## 1. Project Baseline State

| Metric | Value |
|--------|-------|
| Project | UnionCore (IP2A-Database-v2) |
| Repository | https://github.com/theace26/IP2A-Database-v2 |
| Version | v0.9.16-alpha (as of Week 42) |
| Tests | ~764 total (682 baseline + 82 Phase 7 reports) |
| API Endpoints | ~320+ (260 baseline + 62 Phase 7) |
| ORM Models | 32 (26 core + 6 Phase 7) |
| ADRs | 18 |
| Branch Strategy | `develop` (active work) → `main` (stable/deploy) |
| Deployment | Railway (PostgreSQL + API) |
| Developer | Xerxes (Business Rep, 5-10 hrs/week) |

**IMPORTANT:** Always work on the `develop` branch. Only merge to `main` when ready to update production.

---

## 2. Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| **API** | FastAPI | Async, auto-docs at /docs |
| **ORM** | SQLAlchemy 2.0 | Models = source of truth |
| **Database** | PostgreSQL 16 | JSONB, proper constraints, Railway-hosted |
| **Migrations** | Alembic | Governed, drift-detected |
| **Auth** | JWT + bcrypt | 30min access, 7day refresh, HTTP-only cookies |
| **Files** | MinIO (dev) / S3 (prod) | Presigned URLs |
| **Templates** | Jinja2 | Server-side rendering |
| **Interactivity** | HTMX | HTML-over-the-wire |
| **Micro-interactions** | Alpine.js | Dropdowns, toggles |
| **CSS** | DaisyUI + Tailwind | CDN, no build step |
| **Testing** | pytest + httpx | ~764 total tests |
| **Reports** | WeasyPrint + openpyxl | PDF/Excel generation |
| **Container** | Docker | Full dev environment |

---

## 3. Dues Domain Summary (Your Primary Domain)

### Existing Models

**Location:** `src/models/`

- **`DuesRate`** — Rate definitions per classification/type
  - Fields: `amount`, `classification`, `rate_type`, `effective_date`
  - Used by: Payment calculation service

- **`DuesPeriod`** — Billing period boundaries
  - Fields: `year`, `month`, `status`, `start_date`, `end_date`
  - Used by: Period management, payment reconciliation

- **`DuesPayment`** — Individual payment records
  - Fields: `member_id`, `period_id`, `amount`, `payment_date`, `payment_method`, `status`
  - **CRITICAL:** Check if `stripe_payment_id` field was renamed or removed during Week 35

- **`DuesAdjustment`** — Credit/debit adjustments with approval workflow
  - Fields: `member_id`, `amount`, `reason`, `status`, `approved_by`, `approved_at`
  - Workflow: pending → approved/denied

### Existing Endpoints (~35)

**API Router:** `src/routers/dues.py` (backend) + `src/routers/dues_frontend.py` (frontend)

| Endpoint Group | Count | Purpose |
|----------------|-------|---------|
| `/api/v1/dues/rates` | ~8 | CRUD for rates |
| `/api/v1/dues/periods` | ~10 | Period management, generation, closing |
| `/api/v1/dues/payments` | ~10 | Payment recording, history |
| `/api/v1/dues/adjustments` | ~7 | Adjustment workflow |
| Frontend routes | ~12 | Dues landing, rates list, periods, payments, adjustments |

### Existing Tests

- **Backend:** 21 tests (`src/tests/test_dues.py`)
- **Frontend:** 37 tests (`src/tests/test_dues_frontend.py`)
- **Stripe tests:** 27 tests (DEPRECATED — skip-marked per ADR-018)
  - `src/tests/test_stripe_integration.py` — 13 tests skipped
  - `src/tests/test_stripe_frontend.py` — 14 tests skipped

### Frontend Pages

**Location:** `src/templates/dues/`

- **Landing page** (`index.html`) — Stats cards, quick actions
- **Rates management** (`rates/`) — List, create, edit rates
- **Periods management** (`periods/`) — Year generation, period detail, close period
- **Payment recording** (`payments/`) — Record payment, member payment history
- **Adjustments workflow** (`adjustments/`) — List, detail, approve/deny

---

## 4. Payment Processing History

**CRITICAL TIMELINE:**

1. **Week 11 (v0.8.0-alpha1):** Stripe integration built
   - `PaymentService` created
   - Webhook handler implemented
   - Checkout flow with hosted payment page
   - Tests: 27 tests created
   - Location: `src/services/payment_service.py`, `src/routers/webhooks/stripe_webhook.py`

2. **Week 35 (v0.9.11-alpha):** Stripe REMOVED — ADR-018 decision to migrate to Square
   - All Stripe code archived or removed
   - 27 Stripe tests skip-marked (NOT deleted — marked with `@pytest.mark.skip`)
   - NO active payment processor since Week 35

3. **Current state (v0.9.16-alpha):** NO active payment processor
   - Dues models exist and work
   - Payment recording endpoints exist (manual entry)
   - Processing logic removed
   - **Your task:** Restore online payment capability using Square

### ADR-018 Summary: Square Payment Migration

**Decision:** Replace Stripe with Square for payment processing

**Rationale:**
- **Operational integration** — Union hall already uses Square for in-person payments at the counter
- **Single payment ecosystem** — Running both Square (in-person) and Stripe (online) creates reconciliation burden
- **Cost efficiency** — Square's flat-rate pricing (2.6% + $0.10 for card-present, 2.9% + $0.30 for online) is competitive
- **Feature parity** — Square Web Payments SDK provides same client-side tokenization as Stripe
- **Future expansion** — Terminal/POS integration (Phase 8B) and Invoices (Phase 8C) available in same platform

**Phase A (Weeks 47-49): Online Payments ONLY**
- Square Web Payments SDK (client-side tokenization)
- SquarePaymentService backend
- Payment API router
- Webhook handler
- Tests (mocked — NO sandbox hits)

**Phase B (Future): Terminal/POS Integration**
- NOT IN SCOPE for Weeks 47-49
- Do not build, do not stub

**Phase C (Future): Invoice Generation**
- NOT IN SCOPE for Weeks 47-49
- Do not build, do not stub

### Square SDK Integration Notes

**Client-Side (Square Web Payments SDK):**
- JavaScript library loaded from Square CDN
- Renders card input form
- Tokenizes card data client-side
- Returns single-use nonce to backend
- **Card data NEVER touches UnionCore servers** (PCI compliant)

**Server-Side (Square Payments API):**
- Python SDK: `squareup>=35.0.0`
- Nonce → Payment API → Charge
- Verify payment status
- NO webhook-driven checkout sessions (unlike Stripe)
- Flow: tokenize → charge → verify (synchronous)

**Environment:**
- **Sandbox** for dev/test: `sandbox.web.squarecdn.com`
- **Production** for live: `web.squarecdn.com`

**Key Differences from Stripe:**
- No hosted checkout page — form rendered in-app
- No webhook-driven async flow — synchronous payment processing
- No Payment Intents — direct charge from nonce
- Webhook still used for refunds, disputes, and delayed events

---

## 5. Cross-Cutting File Warnings

These files are shared across all Spokes. **Modifications require noting in session summary for Hub handoff.**

| File | Why It's Shared | Caution |
|------|-----------------|---------|
| `src/main.py` | Router registration, middleware, startup events | Adding routers here affects all modules. Always add at END of router list. |
| `src/tests/conftest.py` | Auth fixtures, DB session, seed data | Fixture changes can break 764+ tests. Test after ANY changes. |
| `src/templates/base.html` | Master layout for all pages | CSS/JS changes affect every page. |
| `src/templates/components/_sidebar.html` | Navigation for all modules | Adding links affects all users. Follow existing patterns. |
| `src/config/settings.py` | Application configuration | New env vars affect deployment. Update `.env.example` simultaneously. |
| `alembic/versions/` | Migration chain | Only one Spoke should create migrations at a time. Coordinate via Hub. |
| `requirements.txt` | Python dependencies | Test after adding packages. Pin versions. |

---

## 6. Coding Standards Quick Reference

| Item | Convention | Example |
|------|-----------|---------|
| **Tables** | snake_case, plural | `dues_payments` |
| **Models** | PascalCase, singular | `DuesPayment` |
| **Services** | PascalCase + Service | `SquarePaymentService` |
| **API routes** | /api/v1/plural-nouns | `/api/v1/dues/payments` |
| **Git commits** | Conventional commits | `feat(dues): add Square tokenization` |
| **Templates** | snake_case | `payment_form.html` |
| **Partials** | underscore prefix | `_payment_row.html` |
| **Enums** | Defined in `src/db/enums/` | Import from there, NOT `src/models/enums` |

### Service Layer Pattern

**All business logic goes through services, not directly in routes.**

```python
# CORRECT
from src.services.square_payment_service import SquarePaymentService

@router.post("/process")
async def process_payment(db: Session = Depends(get_db)):
    service = SquarePaymentService(db)
    result = service.create_payment(...)
    return result
```

### Synchronous Database Sessions (CRITICAL)

**This codebase uses SYNCHRONOUS SQLAlchemy sessions, NOT async.**

```python
# CORRECT - synchronous
from sqlalchemy.orm import Session

def some_function(db: Session = Depends(get_db)):
    result = db.execute(stmt)  # NO await
    items = result.scalars().all()

# WRONG - async (will cause 500 errors)
from sqlalchemy.ext.asyncio import AsyncSession

async def some_function(db: AsyncSession = Depends(get_db)):
    result = await db.execute(stmt)  # FAILS
```

---

## 7. Git Commit Message Format

```
type(scope): description

- Detail 1
- Detail 2
- Cross-cutting changes: [list if any]

Version: vX.Y.Z-alpha
Spoke: Spoke 1 (Core Platform)
```

**Types:** feat, fix, docs, refactor, test, chore

**Example:**
```
feat(payments): Week 47 — Square SDK integration and service layer (v0.9.21-alpha)

- Installed squareup SDK
- Created SquarePaymentService with create_payment, refund, webhook verify
- Added Square configuration to settings.py and .env.example
- Cross-cutting changes: settings.py, requirements.txt

Version: v0.9.21-alpha
Spoke: Spoke 1 (Core Platform)
```

---

## 8. Session Summary Requirements

**Every Claude Code session MUST end with:**

1. ✅ All tests passing (or failures documented)
2. ✅ CLAUDE.md updated with session summary
3. ✅ CHANGELOG.md updated
4. ✅ Any modified `docs/*` files updated
5. ✅ Git commit and push to `develop`
6. ✅ If shared files modified → note for Hub handoff

**Template:**
```markdown
## Session: Week X — [Task Name]
**Date:** [DATE]
**Duration:** [X] hours
**Spoke:** Spoke 1 (Core Platform)
**Starting Version:** vX.Y.Z-alpha
**Ending Version:** vX.Y.Z-alpha

### Work Completed
- [list]

### Tests
- Baseline: [X] passing, [X] skipped
- After changes: [X] passing, [X] skipped
- New tests added: [X]

### Cross-Cutting Changes
- [File]: [What changed]
- Hub handoff needed: [yes/no — describe if yes]

### Files Created/Modified
- Created: [list]
- Modified: [list]
```

---

## 9. Security Notes for Payment Processing

**CRITICAL RULES:**

- ❌ **NEVER store raw card numbers** in the database
- ✅ Square tokenization happens client-side — server only sees tokens
- ✅ PCI compliance: tokens are ephemeral, not reusable (unless stored as Cards on File)
- ✅ Payment amounts stored as **integers (cents)** to avoid floating point issues
  - Example: $50.00 = 5000 cents
  - `amount_money: {"amount": 5000, "currency": "USD"}`
- ✅ All payment operations require **audit trail logging**
- ✅ Payment endpoints require **Staff+ role minimum**
- ✅ Refund endpoints require **Officer+ role**
- ❌ **NEVER hardcode credentials** — read from `settings.py` only
- ✅ Use **idempotency keys** (UUID) to prevent duplicate charges

---

## 10. Audit Requirements

**All payment-related changes MUST be audited:**

- `dues_payments` is already in AUDITED_TABLES
- New Square payment records must log:
  - Amount (in cents)
  - Token (last 4 only)
  - Timestamp
  - User who processed payment
  - Success/failure status
- Refunds require Officer+ approval and separate audit entry
- **7-year NLRA retention** applies to all financial records

### Audit Service Pattern

**Location:** `src/services/audit_service.py`

```python
from src.services.audit_service import audit_service

# Log payment attempt
audit_service.log_action(
    db=db,
    action="PAYMENT_PROCESSED",
    table_name="dues_payments",
    record_id=dues_payment_id,
    user_id=current_user.id,
    old_value=None,
    new_value={"amount": amount_cents, "status": "paid"},
)
```

---

## 11. Testing Patterns

### Test Fixtures (conftest.py)

**Common fixtures:**
- `db` or `db_session` — Database session
- `client` — FastAPI test client
- `auth_headers` or `admin_headers` — JWT auth headers
- `test_user` — User fixture with admin role
- `test_member` — Member fixture

**Always check `conftest.py` for actual fixture names before writing tests.**

### Mocking External APIs

**CRITICAL:** All Square API calls MUST be mocked. Tests should NEVER hit Square's sandbox.

```python
from unittest.mock import MagicMock, patch

@patch("src.services.square_payment_service.SquareClient")
def test_create_payment_success(mock_client_class, db_session):
    mock_result = MagicMock()
    mock_result.is_success.return_value = True
    mock_result.body = {"payment": {"id": "sq_pay_123"}}

    mock_client = MagicMock()
    mock_client.payments.create_payment.return_value = mock_result
    mock_client_class.return_value = mock_client

    # Test implementation
```

---

## 12. Known Issues & Workarounds

### Issue #1: Stripe References May Remain

**Status:** Removed in Week 35, but verify

**Action:** Check for any remaining Stripe imports:
```bash
grep -rn "stripe" src/ --include="*.py" | grep -v "__pycache__"
```

If found, archive to `src/archive/stripe/`

### Issue #2: DuesPayment External ID Field

**Status:** Unknown if `stripe_payment_id` was renamed/removed

**Action:** Before implementing SquarePaymentService, inspect `src/models/dues_payment.py`:
- Check for `stripe_payment_id`, `external_payment_id`, or similar
- If no field exists, create migration: `alembic revision --autogenerate -m "add square_payment_id to dues_payments"`
- Field should be: `square_payment_id = Column(String(255), nullable=True)`

### Issue #3: Auth Dependency Import Path

**Status:** May vary from documented pattern

**Action:** Check existing routers for auth import:
```bash
grep -n "from.*auth.*import.*current_user" src/routers/*.py | head -5
```

Common patterns:
- `from src.routers.dependencies.auth import get_current_user`
- `from src.routers.dependencies.auth_cookie import require_auth`
- `from src.core.auth import get_current_active_user`

---

## 13. Phase 8A Scope Boundary

### ✅ IN SCOPE (Weeks 47-49)

- Install Square Python SDK (`squareup>=35.0.0`)
- Create `SquarePaymentService`
  - `create_payment(nonce, amount_cents, ...)`
  - `get_payment_status(square_payment_id)`
  - `process_refund(square_payment_id, amount_cents, reason)`
  - `verify_webhook(body, signature, url)`
- Create Square payments API router
  - `POST /api/v1/payments/process`
  - `GET /api/v1/payments/{id}`
  - `POST /api/v1/payments/{id}/refund`
  - `POST /api/v1/payments/webhooks/square`
- Frontend payment form with Square Web Payments SDK
- Tests (15-20 tests, all mocked)
- Update ADR-018 with Phase A completion status

### ❌ NOT IN SCOPE

- Terminal/POS integration (Phase 8B)
- Invoice generation (Phase 8C)
- Recurring subscriptions
- Payment plans
- QuickBooks sync
- Refund UI (endpoint only — UI is future)
- Card-on-file storage

**If tempted to build these:** STOP. Document as "Future Phase B/C" and move on.

---

## 14. Version Progression

| Week | Version | Milestone |
|------|---------|-----------|
| 47 | v0.9.21-alpha | Square SDK + service layer |
| 48 | v0.9.22-alpha | Square API + frontend |
| 49 | v0.9.23-alpha | Square tested + Phase 8A complete |

---

## 15. Dependencies & Environment

### Required Python Packages

```txt
# Core (already installed)
fastapi>=0.100.0
sqlalchemy>=2.0.0
alembic>=1.11.0
pydantic>=2.0.0
python-jose[cryptography]
passlib[bcrypt]
python-multipart
httpx

# Reports (already installed)
weasyprint>=60.0
openpyxl>=3.1.0

# Square (YOU WILL INSTALL)
squareup>=35.0.0
```

### Environment Variables (Square)

Add to `.env.example` and `src/config/settings.py`:

```env
# Square Payment Integration (Phase 8A — ADR-018)
SQUARE_ENVIRONMENT=sandbox
SQUARE_ACCESS_TOKEN=
SQUARE_APPLICATION_ID=
SQUARE_LOCATION_ID=
SQUARE_WEBHOOK_SIGNATURE_KEY=
```

### Docker

Dev environment:
```bash
docker-compose up -d  # Starts PostgreSQL, API
```

---

## 16. Quick Start Checklist

Before starting Week 47:

- [ ] Read this entire document
- [ ] Read ADR-018 (`docs/decisions/ADR-018-square-payment-integration.md`)
- [ ] Read Week 47-49 instruction document (`docs/!TEMP/Week47-49_Square_Payment_Migration_ClaudeCode.md`)
- [ ] Checkout `develop` branch
- [ ] Run tests to establish baseline
- [ ] Inspect `src/models/dues_payment.py` for external ID field
- [ ] Check `conftest.py` for auth fixture names
- [ ] Verify Stripe is fully archived

---

## 17. Questions? Issues?

**For Xerxes (the developer):**
- Hub project on claude.ai for strategic questions
- Spoke 1 project for tactical implementation questions
- Git Issues for bugs/blockers

**For Claude Code:**
- If blocked, document in session summary and push to develop
- If unsure about patterns, read existing code first (e.g., check other services for constructor patterns)
- If cross-cutting changes needed, note for Hub handoff

---

*Spoke 1 Onboarding Context Document*
*Version: 1.0*
*Created: February 7, 2026*
*Next Update: After Phase 8A completion (Week 49)*
