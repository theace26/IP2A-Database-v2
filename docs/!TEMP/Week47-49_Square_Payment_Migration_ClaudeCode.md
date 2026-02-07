# Claude Code Instructions: Weeks 47–49 — Phase 8A Square Online Payments

**Created:** February 6, 2026
**Source:** Hub Project — UnionCore Strategic Planning
**Spoke Owner:** Spoke 1 (Core Platform: Members, Dues, Employers, Member Portal)
**Branch:** `develop`
**Baseline:** v0.9.16-alpha | ~764 tests | ~320+ endpoints | 85 reports | 32 models | 18 ADRs
**Target Version:** v0.9.23-alpha (upon Week 49 completion)
**Hub Guidance Ref:** `Hub_Guidance_Weeks_43-49.md`
**ADR Reference:** ADR-018 (Stripe → Square Migration)
**Estimated Time:** 8–12 hours across 3 sprint weeks

---

## Context for Claude Code

You are executing Phase 8A of the UnionCore project — replacing Stripe with Square Web Payments SDK for online dues payment processing.

**What happened before you:**
- Stripe was integrated at Week 11 (ADR-013)
- Stripe was removed at Week 35 (ADR-018) — code archived, 27 Stripe tests deleted, skip markers added
- There is currently NO active payment processor
- Dues models exist and work: `DuesRate`, `DuesPeriod`, `DuesPayment`, `DuesAdjustment`
- Existing dues endpoints: ~35 API + frontend routes
- Existing dues tests: 21 backend + 37 frontend

**What you are building:**
- Phase 8A = Online payments ONLY (Square Web Payments SDK)
- Phase 8B (Terminal/POS) and 8C (Invoices) are NOT in scope. Do not build them. Do not stub them.

**Scope boundary — hard stop:**
- ✅ IN SCOPE: SquarePaymentService, payment API router, frontend payment form, webhook handler, tests
- ❌ NOT IN SCOPE: Terminal/POS, invoice generation, QuickBooks sync, recurring subscriptions, refund UI
- ⚠️ CROSS-CUTTING: `src/main.py` (router registration), `conftest.py` (fixtures), base templates (Square SDK script tag). Note ALL cross-cutting changes in session summary for Hub handoff.

**Sprint Weeks ≠ Calendar Weeks.** At 5–10 hrs/week, each sprint takes 1–2 calendar weeks.

---

## Pre-Flight (Run Before EVERY Week)

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
pytest -v --tb=short 2>&1 | tail -10
```

Capture the test count. Verify green baseline before starting any work.

---

## Week 47: Square SDK Integration & Service Layer (3–4 hours)

### Objective
Install the Square Python SDK, create configuration, build the SquarePaymentService, and archive any remaining Stripe references.

### Step 1: Install Dependencies

```bash
pip install squareup --break-system-packages
```

Verify `requirements.txt`:
```bash
grep -i stripe requirements.txt    # Should return nothing (removed Week 35)
grep -i square requirements.txt    # Should return nothing (not yet added)
```

Add to `requirements.txt`:
```
squareup>=35.0.0
```

> **If `stripe` is still in requirements.txt**, remove it. ADR-018 says it was removed at Week 35 but verify.

### Step 2: Configuration

**Add to `.env.example`:**
```env
# Square Payment Integration (Phase 8A — ADR-018)
SQUARE_ENVIRONMENT=sandbox
SQUARE_ACCESS_TOKEN=
SQUARE_APPLICATION_ID=
SQUARE_LOCATION_ID=
SQUARE_WEBHOOK_SIGNATURE_KEY=
```

**Add to `src/config/settings.py`** (or equivalent settings file — check existing pattern):
```python
# Square Payment Integration (Phase 8A — ADR-018)
SQUARE_ENVIRONMENT: str = "sandbox"
SQUARE_ACCESS_TOKEN: str = ""
SQUARE_APPLICATION_ID: str = ""
SQUARE_LOCATION_ID: str = ""
SQUARE_WEBHOOK_SIGNATURE_KEY: str = ""
```

> **NEVER hardcode credentials.** Read from settings only. Check ADR-018 for any additional config requirements.

### Step 3: Archive Remaining Stripe Code (If Any)

Week 35 should have archived Stripe code, but verify:

```bash
# Check for any remaining Stripe imports or references
grep -rn "stripe" src/ --include="*.py" | grep -v "__pycache__" | grep -v ".pyc"
grep -rn "stripe" src/templates/ --include="*.html"
```

If any active Stripe references remain:
- Move files to `src/archive/stripe/` (create directory if needed)
- Remove Stripe imports from `src/main.py`
- Remove Stripe router registration from `src/main.py`
- Remove Stripe references from templates

If Stripe is already fully gone, skip this step and note "Stripe already clean" in session summary.

### Step 4: Create SquarePaymentService

**Create:** `src/services/square_payment_service.py`

Follow existing service layer conventions. Look at any existing service (e.g., `src/services/dues_payment_service.py`) for the constructor pattern.

```python
"""
Square Payment Service — Phase 8A (ADR-018)
Handles online payment processing via Square Web Payments SDK.
Card data NEVER touches UnionCore servers — tokenized client-side.

Spoke Owner: Spoke 1 (Core Platform)
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from square.client import Client as SquareClient

from src.config.settings import settings

logger = logging.getLogger(__name__)


class SquarePaymentService:
    """Process dues payments through Square Web Payments SDK."""

    def __init__(self, db: Session):
        self.db = db
        self.client = SquareClient(
            access_token=settings.SQUARE_ACCESS_TOKEN,
            environment=settings.SQUARE_ENVIRONMENT,
        )

    def create_payment(
        self,
        nonce: str,
        amount_cents: int,
        member_id: int,
        dues_payment_id: int,
        description: str,
        idempotency_key: str,
    ) -> dict:
        """
        Process a payment using a client-side nonce from Square Web Payments SDK.

        Args:
            nonce: Single-use token from Square JS SDK (client-side tokenization)
            amount_cents: Payment amount in cents (e.g., 5000 = $50.00)
            member_id: UnionCore member ID
            dues_payment_id: UnionCore DuesPayment record ID
            description: Human-readable description (e.g., "January 2026 Dues")
            idempotency_key: Unique key to prevent duplicate charges (UUID)

        Returns:
            dict with keys: success (bool), payment_id (str|None), error (str|None)
        """
        try:
            result = self.client.payments.create_payment(
                body={
                    "source_id": nonce,
                    "idempotency_key": idempotency_key,
                    "amount_money": {
                        "amount": amount_cents,
                        "currency": "USD",
                    },
                    "location_id": settings.SQUARE_LOCATION_ID,
                    "note": description,
                    "reference_id": str(dues_payment_id),
                }
            )

            if result.is_success():
                payment = result.body.get("payment", {})
                square_payment_id = payment.get("id")

                # AUDIT TRAIL — MANDATORY for all payment attempts
                self._log_payment_audit(
                    member_id=member_id,
                    dues_payment_id=dues_payment_id,
                    square_payment_id=square_payment_id,
                    amount_cents=amount_cents,
                    status="COMPLETED",
                    detail=description,
                )

                # Update DuesPayment record with Square payment ID
                self._update_dues_payment(
                    dues_payment_id=dues_payment_id,
                    square_payment_id=square_payment_id,
                    status="paid",
                )

                logger.info(
                    "Payment processed: member=%s amount=%s square_id=%s",
                    member_id, amount_cents, square_payment_id,
                )
                return {
                    "success": True,
                    "payment_id": square_payment_id,
                    "error": None,
                }

            elif result.is_error():
                errors = result.errors
                error_msg = "; ".join(
                    [f"{e.get('category')}: {e.get('detail')}" for e in errors]
                )

                # AUDIT TRAIL — log failures too
                self._log_payment_audit(
                    member_id=member_id,
                    dues_payment_id=dues_payment_id,
                    square_payment_id=None,
                    amount_cents=amount_cents,
                    status="FAILED",
                    detail=error_msg,
                )

                logger.warning(
                    "Payment failed: member=%s amount=%s error=%s",
                    member_id, amount_cents, error_msg,
                )
                return {
                    "success": False,
                    "payment_id": None,
                    "error": error_msg,
                }

        except Exception as exc:
            error_msg = str(exc)
            self._log_payment_audit(
                member_id=member_id,
                dues_payment_id=dues_payment_id,
                square_payment_id=None,
                amount_cents=amount_cents,
                status="ERROR",
                detail=error_msg,
            )
            logger.exception("Payment exception: member=%s", member_id)
            return {
                "success": False,
                "payment_id": None,
                "error": error_msg,
            }

    def get_payment_status(self, square_payment_id: str) -> dict:
        """Check payment status from Square API."""
        try:
            result = self.client.payments.get_payment(payment_id=square_payment_id)
            if result.is_success():
                payment = result.body.get("payment", {})
                return {
                    "success": True,
                    "status": payment.get("status"),
                    "amount_cents": payment.get("amount_money", {}).get("amount"),
                    "created_at": payment.get("created_at"),
                }
            return {
                "success": False,
                "error": str(result.errors),
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def process_refund(
        self,
        square_payment_id: str,
        amount_cents: int,
        reason: str,
        requested_by_user_id: int,
        idempotency_key: str,
    ) -> dict:
        """
        Process a refund. Officer+ role required (enforced at router level).

        AUDIT TRAIL IS MANDATORY FOR ALL REFUNDS — success or failure.
        """
        try:
            result = self.client.refunds.refund_payment(
                body={
                    "idempotency_key": idempotency_key,
                    "payment_id": square_payment_id,
                    "amount_money": {
                        "amount": amount_cents,
                        "currency": "USD",
                    },
                    "reason": reason,
                }
            )

            if result.is_success():
                refund = result.body.get("refund", {})
                refund_id = refund.get("id")

                self._log_payment_audit(
                    member_id=None,  # Resolve from payment record
                    dues_payment_id=None,
                    square_payment_id=square_payment_id,
                    amount_cents=amount_cents,
                    status="REFUNDED",
                    detail=f"Refund by user {requested_by_user_id}: {reason}",
                )

                logger.info(
                    "Refund processed: square_payment=%s refund=%s amount=%s",
                    square_payment_id, refund_id, amount_cents,
                )
                return {"success": True, "refund_id": refund_id, "error": None}

            error_msg = str(result.errors)
            self._log_payment_audit(
                member_id=None,
                dues_payment_id=None,
                square_payment_id=square_payment_id,
                amount_cents=amount_cents,
                status="REFUND_FAILED",
                detail=error_msg,
            )
            return {"success": False, "refund_id": None, "error": error_msg}

        except Exception as exc:
            logger.exception("Refund exception: payment=%s", square_payment_id)
            return {"success": False, "refund_id": None, "error": str(exc)}

    def verify_webhook(self, body: str, signature: str, url: str) -> bool:
        """
        Verify Square webhook signature.
        Returns True if signature is valid, False otherwise.
        """
        from square.utilities.webhooks_helper import is_valid_webhook_event_signature

        try:
            return is_valid_webhook_event_signature(
                request_body=body,
                signature_key=settings.SQUARE_WEBHOOK_SIGNATURE_KEY,
                signature_header=signature,
                notification_url=url,
            )
        except Exception:
            logger.exception("Webhook verification error")
            return False

    def _log_payment_audit(
        self,
        member_id: Optional[int],
        dues_payment_id: Optional[int],
        square_payment_id: Optional[str],
        amount_cents: int,
        status: str,
        detail: str,
    ):
        """
        Log payment event to audit trail.

        CRITICAL: This uses the existing audit_service pattern.
        Check src/services/audit_service.py for the correct method signature.
        Adapt this stub to match the actual audit logging pattern in the codebase.
        """
        # TODO: Wire to actual audit_service.log_action() or equivalent
        # Pattern should match existing audit calls in dues_payment_service.py
        # Required fields: action, entity_type, entity_id, user_id, old_value, new_value
        logger.info(
            "AUDIT: payment %s | member=%s | dues_payment=%s | square=%s | amount=%s | %s",
            status, member_id, dues_payment_id, square_payment_id, amount_cents, detail,
        )

    def _update_dues_payment(
        self,
        dues_payment_id: int,
        square_payment_id: str,
        status: str,
    ):
        """
        Update DuesPayment record with Square payment reference.

        CRITICAL: Check the DuesPayment model for correct field names.
        The old Stripe integration used `stripe_payment_id` — this may have been
        renamed to a generic `external_payment_id` or removed entirely during Week 35.
        Inspect the model before coding.
        """
        # TODO: Look at src/models/ for DuesPayment model
        # Check if there's a stripe_payment_id, external_payment_id, or similar field
        # If no field exists, create an Alembic migration to add:
        #   square_payment_id = Column(String(255), nullable=True)
        pass
```

> **CRITICAL IMPLEMENTATION NOTE:** The `_log_payment_audit` and `_update_dues_payment` methods are stubs. Before implementing:
> 1. Read `src/services/audit_service.py` to understand the existing audit pattern
> 2. Read the `DuesPayment` model to find the correct field for external payment IDs
> 3. If `stripe_payment_id` was renamed generically during Week 35, use that field
> 4. If no field exists, create a migration: `alembic revision --autogenerate -m "add square_payment_id to dues_payments"`

### Step 5: Verify No Breakage

```bash
pytest -v --tb=short 2>&1 | tail -10
```

Nothing should break — you've only added new files and config, not modified existing code.

### Week 47 Acceptance Criteria

- [ ] `squareup` package installed and importable (`python -c "from square.client import Client"`)
- [ ] Square configuration added to `.env.example` and `settings.py`
- [ ] SquarePaymentService created at `src/services/square_payment_service.py`
- [ ] No remaining active Stripe references in `src/` (archived or removed)
- [ ] All existing tests still pass (no regressions)
- [ ] CLAUDE.md updated (add Phase 8A status, note Square integration begun)
- [ ] CHANGELOG.md updated with Week 47 entry

### Week 47 Git Commit

```bash
git add -A
git commit -m "feat(payments): Week 47 — Square SDK integration and service layer (v0.9.21-alpha)

- Installed squareup SDK
- Created SquarePaymentService with create_payment, get_payment_status, process_refund, verify_webhook
- Added Square configuration to settings.py and .env.example
- Verified Stripe code fully archived (ADR-018)
- All existing tests pass — no regressions
- Spoke Owner: Spoke 1 (Core Platform)"

git push origin develop
```

---

## Week 48: API Router & Frontend Integration (3–4 hours)

### Objective
Create the payment API router, register it in `main.py`, build the frontend payment form with Square Web Payments SDK, and implement the webhook handler.

### Step 1: Create Payment API Router

**Create:** `src/routers/square_payments.py`

```python
"""
Square Payment API Router — Phase 8A (ADR-018)
Handles payment processing, status checks, refunds, and webhooks.

Spoke Owner: Spoke 1 (Core Platform)
"""
import json
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.db.session import get_db
from src.services.square_payment_service import SquarePaymentService

# Import your existing auth dependency — check src/routers/ for the pattern
# Common patterns:
#   from src.auth.dependencies import get_current_user, require_role
#   from src.core.auth import get_current_active_user
# VERIFY THE ACTUAL IMPORT PATH before coding.

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


class PaymentRequest(BaseModel):
    """Payment request from frontend (nonce from Square SDK)."""
    nonce: str
    amount_cents: int
    member_id: int
    dues_payment_id: int
    description: str


class RefundRequest(BaseModel):
    """Refund request (Officer+ only)."""
    amount_cents: int
    reason: str


@router.post("/process")
async def process_payment(
    request: PaymentRequest,
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user),  # VERIFY auth dependency name
):
    """Process a payment using a nonce from the Square Web Payments SDK."""
    service = SquarePaymentService(db)
    idempotency_key = str(uuid.uuid4())

    result = service.create_payment(
        nonce=request.nonce,
        amount_cents=request.amount_cents,
        member_id=request.member_id,
        dues_payment_id=request.dues_payment_id,
        description=request.description,
        idempotency_key=idempotency_key,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "status": "success",
        "payment_id": result["payment_id"],
    }


@router.get("/{square_payment_id}")
async def get_payment_status(
    square_payment_id: str,
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user),
):
    """Get payment status from Square."""
    service = SquarePaymentService(db)
    result = service.get_payment_status(square_payment_id)

    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Payment not found"))

    return result


@router.post("/{square_payment_id}/refund")
async def process_refund(
    square_payment_id: str,
    request: RefundRequest,
    db: Session = Depends(get_db),
    # current_user = Depends(require_role("officer")),  # VERIFY: Officer+ only
):
    """Process a refund. Requires Officer role or higher."""
    service = SquarePaymentService(db)
    idempotency_key = str(uuid.uuid4())

    result = service.process_refund(
        square_payment_id=square_payment_id,
        amount_cents=request.amount_cents,
        reason=request.reason,
        requested_by_user_id=0,  # Replace with current_user.id
        idempotency_key=idempotency_key,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "status": "refunded",
        "refund_id": result["refund_id"],
    }


@router.post("/webhooks/square")
async def square_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receive and process Square webhook events.
    NO AUTH — Square calls this endpoint directly.
    Signature verification replaces authentication.
    """
    body = await request.body()
    body_str = body.decode("utf-8")
    signature = request.headers.get("x-square-hmacsha256-signature", "")
    notification_url = str(request.url)

    service = SquarePaymentService(db)

    if not service.verify_webhook(body_str, signature, notification_url):
        logger.warning("Invalid webhook signature received")
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = json.loads(body_str)
    event_type = event.get("type", "")

    # Handle relevant events
    if event_type == "payment.completed":
        payment_data = event.get("data", {}).get("object", {}).get("payment", {})
        logger.info("Webhook: payment completed — %s", payment_data.get("id"))
        # Update DuesPayment status if needed

    elif event_type == "payment.failed":
        payment_data = event.get("data", {}).get("object", {}).get("payment", {})
        logger.warning("Webhook: payment failed — %s", payment_data.get("id"))

    elif event_type == "refund.created":
        refund_data = event.get("data", {}).get("object", {}).get("refund", {})
        logger.info("Webhook: refund created — %s", refund_data.get("id"))

    else:
        logger.info("Webhook: unhandled event type — %s", event_type)

    # Always return 200 to acknowledge receipt (Square retries on non-200)
    return {"status": "received"}
```

### Step 2: Register Router in main.py

**⚠️ CROSS-CUTTING CHANGE — Note in session summary for Hub.**

Open `src/main.py` and add the router registration. Follow the existing pattern:

```python
from src.routers.square_payments import router as square_payments_router

# Add to the router registration block (at the END — don't reorder existing registrations)
app.include_router(square_payments_router)
```

### Step 3: Frontend Payment Form

**Check existing dues payment template:**
```bash
find src/templates -name "*payment*" -o -name "*dues*" | head -20
ls src/templates/dues/
```

**Update or create the payment template.** The exact file depends on what exists. Look for the existing "Pay Now" button that was wired to Stripe.

The critical integration pattern for the Square Web Payments SDK:

```html
{# Square Web Payments SDK — loaded from Square CDN #}
{# IMPORTANT: Use sandbox URL for dev, production URL for prod #}
{% if config.SQUARE_ENVIRONMENT == "sandbox" %}
<script src="https://sandbox.web.squarecdn.com/v1/square.js"></script>
{% else %}
<script src="https://web.squarecdn.com/v1/square.js"></script>
{% endif %}

<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <h2 class="card-title">Pay Dues</h2>

    <div class="form-control">
      <label class="label">Amount</label>
      <div class="text-2xl font-bold">${{ amount_display }}</div>
    </div>

    {# Square renders its card input here #}
    <div id="card-container" class="mt-4"></div>

    <div id="payment-status" class="hidden mt-2">
      <div class="alert" id="payment-alert"></div>
    </div>

    <div class="card-actions justify-end mt-4">
      <button id="card-button"
              class="btn btn-primary"
              type="button">
        Pay ${{ amount_display }}
      </button>
    </div>
  </div>
</div>

<script>
  // Initialize Square Web Payments SDK
  async function initializeSquare() {
    if (!window.Square) {
      console.error('Square SDK not loaded');
      return;
    }

    const payments = window.Square.payments(
      '{{ config.SQUARE_APPLICATION_ID }}',
      '{{ config.SQUARE_LOCATION_ID }}'
    );

    const card = await payments.card();
    await card.attach('#card-container');

    const button = document.getElementById('card-button');
    button.addEventListener('click', async () => {
      button.disabled = true;
      button.textContent = 'Processing...';

      try {
        const result = await card.tokenize();
        if (result.status === 'OK') {
          // Send nonce to backend
          const response = await fetch('/api/v1/payments/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              nonce: result.token,
              amount_cents: {{ amount_cents }},
              member_id: {{ member_id }},
              dues_payment_id: {{ dues_payment_id }},
              description: '{{ description }}'
            })
          });

          const data = await response.json();
          if (response.ok) {
            showStatus('success', 'Payment successful!');
            // Redirect to success page after 2 seconds
            setTimeout(() => {
              window.location.href = '/dues/payments/{{ dues_payment_id }}';
            }, 2000);
          } else {
            showStatus('error', data.detail || 'Payment failed');
            button.disabled = false;
            button.textContent = 'Pay ${{ amount_display }}';
          }
        } else {
          showStatus('error', 'Card validation failed. Please check your card details.');
          button.disabled = false;
          button.textContent = 'Pay ${{ amount_display }}';
        }
      } catch (err) {
        showStatus('error', 'An error occurred. Please try again.');
        button.disabled = false;
        button.textContent = 'Pay ${{ amount_display }}';
      }
    });
  }

  function showStatus(type, message) {
    const statusDiv = document.getElementById('payment-status');
    const alertDiv = document.getElementById('payment-alert');
    statusDiv.classList.remove('hidden');
    alertDiv.className = type === 'success' ? 'alert alert-success' : 'alert alert-error';
    alertDiv.textContent = message;
  }

  // Initialize when DOM ready
  document.addEventListener('DOMContentLoaded', initializeSquare);
</script>
```

> **CRITICAL:** Card data NEVER touches the UnionCore server. The Square SDK tokenizes client-side. The server only receives a single-use nonce. This is how PCI compliance works — we never see, store, or transmit card numbers.

### Step 4: Add Square SDK Script to Base Template (If Needed)

**⚠️ CROSS-CUTTING CHANGE — Note in session summary for Hub.**

Check if the Square SDK script needs to go in `base.html` or only in the payment template. If only used on the payment page, keep it in the payment template (as shown above). If multiple pages need it, add a `{% block extra_scripts %}` pattern.

### Step 5: Verify No Breakage

```bash
pytest -v --tb=short 2>&1 | tail -10
```

### Week 48 Acceptance Criteria

- [ ] Payment API router created at `src/routers/square_payments.py`
- [ ] Router registered in `src/main.py` (cross-cutting change noted)
- [ ] 4 API endpoints functional: `POST /process`, `GET /{id}`, `POST /{id}/refund`, `POST /webhooks/square`
- [ ] Frontend payment form renders with Square SDK card input
- [ ] Card tokenization flow works (manual test in browser with sandbox credentials)
- [ ] Webhook endpoint receives and verifies signatures
- [ ] All existing tests still pass
- [ ] CLAUDE.md updated
- [ ] CHANGELOG.md updated with Week 48 entry

### Week 48 Git Commit

```bash
git add -A
git commit -m "feat(payments): Week 48 — Square API router and frontend integration (v0.9.22-alpha)

- Created square_payments router (4 endpoints: process, status, refund, webhook)
- Registered router in main.py
- Built frontend payment form with Square Web Payments SDK
- Client-side tokenization (PCI compliant — card data never touches server)
- Webhook handler with signature verification
- All existing tests pass — no regressions
- Cross-cutting: main.py modified (router registration)
- Spoke Owner: Spoke 1 (Core Platform)"

git push origin develop
```

---

## Week 49: Testing & Phase 8A Close-Out (2–4 hours)

### Objective
Write comprehensive tests for the Square payment integration, clean up any remaining Stripe skip markers, update ADR-018, and close out Phase 8A.

### Step 1: Create Test File

**Create:** `src/tests/test_square_payments.py`

```python
"""
Tests for Square Payment Integration — Phase 8A (ADR-018)

CRITICAL: All Square API calls MUST be mocked. Tests should NEVER hit
Square's sandbox API. We test our code, not Square's API.

Spoke Owner: Spoke 1 (Core Platform)
"""
import json
import uuid
import pytest
from unittest.mock import MagicMock, patch

# Adjust imports to match actual project structure
# from src.services.square_payment_service import SquarePaymentService


# ============================================================
# SERVICE TESTS
# ============================================================

class TestSquarePaymentService:
    """Tests for SquarePaymentService methods."""

    @patch("src.services.square_payment_service.SquareClient")
    def test_create_payment_success(self, mock_client_class, db_session):
        """Successful payment returns payment_id."""
        # Mock Square API response
        mock_result = MagicMock()
        mock_result.is_success.return_value = True
        mock_result.body = {
            "payment": {
                "id": "sq_payment_123",
                "status": "COMPLETED",
            }
        }
        mock_client = MagicMock()
        mock_client.payments.create_payment.return_value = mock_result
        mock_client_class.return_value = mock_client

        from src.services.square_payment_service import SquarePaymentService
        service = SquarePaymentService(db_session)
        service.client = mock_client

        result = service.create_payment(
            nonce="cnon:card-nonce-ok",
            amount_cents=5000,
            member_id=1,
            dues_payment_id=1,
            description="January 2026 Dues",
            idempotency_key=str(uuid.uuid4()),
        )

        assert result["success"] is True
        assert result["payment_id"] == "sq_payment_123"
        assert result["error"] is None

    @patch("src.services.square_payment_service.SquareClient")
    def test_create_payment_failure(self, mock_client_class, db_session):
        """Failed payment returns error message."""
        mock_result = MagicMock()
        mock_result.is_success.return_value = False
        mock_result.is_error.return_value = True
        mock_result.errors = [
            {"category": "PAYMENT_METHOD_ERROR", "detail": "Card declined"}
        ]
        mock_client = MagicMock()
        mock_client.payments.create_payment.return_value = mock_result
        mock_client_class.return_value = mock_client

        from src.services.square_payment_service import SquarePaymentService
        service = SquarePaymentService(db_session)
        service.client = mock_client

        result = service.create_payment(
            nonce="cnon:card-nonce-declined",
            amount_cents=5000,
            member_id=1,
            dues_payment_id=1,
            description="Test",
            idempotency_key=str(uuid.uuid4()),
        )

        assert result["success"] is False
        assert "Card declined" in result["error"]

    @patch("src.services.square_payment_service.SquareClient")
    def test_create_payment_exception(self, mock_client_class, db_session):
        """Exception during payment returns error gracefully."""
        mock_client = MagicMock()
        mock_client.payments.create_payment.side_effect = Exception("Network error")
        mock_client_class.return_value = mock_client

        from src.services.square_payment_service import SquarePaymentService
        service = SquarePaymentService(db_session)
        service.client = mock_client

        result = service.create_payment(
            nonce="test", amount_cents=5000, member_id=1,
            dues_payment_id=1, description="Test",
            idempotency_key=str(uuid.uuid4()),
        )

        assert result["success"] is False
        assert "Network error" in result["error"]

    @patch("src.services.square_payment_service.SquareClient")
    def test_get_payment_status_success(self, mock_client_class, db_session):
        """Can retrieve payment status from Square."""
        mock_result = MagicMock()
        mock_result.is_success.return_value = True
        mock_result.body = {
            "payment": {
                "id": "sq_payment_123",
                "status": "COMPLETED",
                "amount_money": {"amount": 5000, "currency": "USD"},
                "created_at": "2026-02-06T12:00:00Z",
            }
        }
        mock_client = MagicMock()
        mock_client.payments.get_payment.return_value = mock_result
        mock_client_class.return_value = mock_client

        from src.services.square_payment_service import SquarePaymentService
        service = SquarePaymentService(db_session)
        service.client = mock_client

        result = service.get_payment_status("sq_payment_123")

        assert result["success"] is True
        assert result["status"] == "COMPLETED"
        assert result["amount_cents"] == 5000

    @patch("src.services.square_payment_service.SquareClient")
    def test_process_refund_success(self, mock_client_class, db_session):
        """Successful refund returns refund_id."""
        mock_result = MagicMock()
        mock_result.is_success.return_value = True
        mock_result.body = {"refund": {"id": "sq_refund_456"}}
        mock_client = MagicMock()
        mock_client.refunds.refund_payment.return_value = mock_result
        mock_client_class.return_value = mock_client

        from src.services.square_payment_service import SquarePaymentService
        service = SquarePaymentService(db_session)
        service.client = mock_client

        result = service.process_refund(
            square_payment_id="sq_payment_123",
            amount_cents=5000,
            reason="Overpayment",
            requested_by_user_id=1,
            idempotency_key=str(uuid.uuid4()),
        )

        assert result["success"] is True
        assert result["refund_id"] == "sq_refund_456"

    @patch("src.services.square_payment_service.SquareClient")
    def test_process_refund_failure(self, mock_client_class, db_session):
        """Failed refund returns error."""
        mock_result = MagicMock()
        mock_result.is_success.return_value = False
        mock_result.errors = [{"detail": "Already refunded"}]
        mock_client = MagicMock()
        mock_client.refunds.refund_payment.return_value = mock_result
        mock_client_class.return_value = mock_client

        from src.services.square_payment_service import SquarePaymentService
        service = SquarePaymentService(db_session)
        service.client = mock_client

        result = service.process_refund(
            square_payment_id="sq_payment_123",
            amount_cents=5000,
            reason="Test",
            requested_by_user_id=1,
            idempotency_key=str(uuid.uuid4()),
        )

        assert result["success"] is False


# ============================================================
# API ROUTER TESTS
# ============================================================

class TestSquarePaymentRouter:
    """Tests for payment API endpoints."""

    def test_process_payment_endpoint(self, client, auth_headers, mocker):
        """POST /api/v1/payments/process returns payment_id on success."""
        mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        ).return_value.create_payment.return_value = {
            "success": True, "payment_id": "sq_pay_123", "error": None
        }

        response = client.post(
            "/api/v1/payments/process",
            json={
                "nonce": "cnon:card-nonce-ok",
                "amount_cents": 5000,
                "member_id": 1,
                "dues_payment_id": 1,
                "description": "Test payment",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["payment_id"] == "sq_pay_123"

    def test_process_payment_failure_returns_400(self, client, auth_headers, mocker):
        """POST /api/v1/payments/process returns 400 on failure."""
        mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        ).return_value.create_payment.return_value = {
            "success": False, "payment_id": None, "error": "Card declined"
        }

        response = client.post(
            "/api/v1/payments/process",
            json={
                "nonce": "bad-nonce",
                "amount_cents": 5000,
                "member_id": 1,
                "dues_payment_id": 1,
                "description": "Test",
            },
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_payment_status_endpoint(self, client, auth_headers, mocker):
        """GET /api/v1/payments/{id} returns payment status."""
        mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        ).return_value.get_payment_status.return_value = {
            "success": True, "status": "COMPLETED", "amount_cents": 5000
        }

        response = client.get(
            "/api/v1/payments/sq_pay_123",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "COMPLETED"

    def test_refund_requires_officer_role(self, client, mocker):
        """POST /refund should require Officer+ role."""
        # This test verifies RBAC enforcement.
        # ADAPT based on actual auth pattern:
        # - If using @require_role decorator, test with staff-level token (should get 403)
        # - If using dependency injection, mock accordingly
        # The exact implementation depends on the auth pattern in the codebase.
        pass  # TODO: Implement once auth pattern confirmed


# ============================================================
# WEBHOOK TESTS
# ============================================================

class TestSquareWebhook:
    """Tests for Square webhook handler."""

    def test_webhook_valid_signature(self, client, mocker):
        """Webhook with valid signature returns 200."""
        mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        ).return_value.verify_webhook.return_value = True

        event = {
            "type": "payment.completed",
            "data": {"object": {"payment": {"id": "sq_pay_123"}}},
        }

        response = client.post(
            "/api/v1/payments/webhooks/square",
            content=json.dumps(event),
            headers={
                "Content-Type": "application/json",
                "x-square-hmacsha256-signature": "valid-sig",
            },
        )

        assert response.status_code == 200

    def test_webhook_invalid_signature(self, client, mocker):
        """Webhook with invalid signature returns 401."""
        mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        ).return_value.verify_webhook.return_value = False

        response = client.post(
            "/api/v1/payments/webhooks/square",
            content=json.dumps({"type": "test"}),
            headers={
                "Content-Type": "application/json",
                "x-square-hmacsha256-signature": "bad-sig",
            },
        )

        assert response.status_code == 401

    def test_webhook_payment_completed(self, client, mocker):
        """Webhook handles payment.completed event."""
        mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        ).return_value.verify_webhook.return_value = True

        event = {
            "type": "payment.completed",
            "data": {
                "object": {
                    "payment": {
                        "id": "sq_pay_789",
                        "status": "COMPLETED",
                        "amount_money": {"amount": 5000},
                    }
                }
            },
        }

        response = client.post(
            "/api/v1/payments/webhooks/square",
            content=json.dumps(event),
            headers={
                "Content-Type": "application/json",
                "x-square-hmacsha256-signature": "valid",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "received"


# ============================================================
# FRONTEND TESTS
# ============================================================

class TestSquarePaymentFrontend:
    """Tests for payment form rendering."""

    def test_payment_page_loads(self, client, auth_headers):
        """Payment page returns 200."""
        # ADAPT: Find the actual URL for the dues payment form
        # Likely: /dues/pay or /dues/payments/new or similar
        # Check src/routers/ for the frontend route
        pass  # TODO: Implement once route confirmed

    def test_payment_page_contains_square_sdk(self, client, auth_headers):
        """Payment page includes Square Web Payments SDK script."""
        # ADAPT: Check that the response HTML contains the Square SDK script tag
        pass  # TODO: Implement once route confirmed
```

> **NOTE ON TEST FIXTURES:** The test file uses `db_session`, `client`, `auth_headers`, and `mocker`. Check `conftest.py` for the actual fixture names. Common alternatives: `db`, `test_client`, `admin_headers`, `staff_headers`. Adapt as needed.

### Step 2: Remove Stripe Skip Markers

```bash
grep -rn "skip.*[Ss]tripe" src/tests/ | head -20
```

For each skip marker found:
- If the test was Stripe-specific and has no Square equivalent → DELETE the test
- If the test was a payment flow test that should now use Square → CONVERT to Square equivalent
- Document what was removed/converted in the session summary

### Step 3: Update ADR-018

Open `docs/decisions/ADR-018-*.md` and update:

```markdown
## Phase A Status: ✅ COMPLETE (Week 49)

### Implementation Summary
- SquarePaymentService: create_payment, get_payment_status, process_refund, verify_webhook
- API Router: 4 endpoints (process, status, refund, webhook)
- Frontend: Square Web Payments SDK with client-side tokenization
- Tests: ~15 tests (service, API, webhook, frontend)
- All Square API calls mocked in tests (no sandbox dependency)

### Files Created/Modified
- `src/services/square_payment_service.py` (NEW)
- `src/routers/square_payments.py` (NEW)
- `src/tests/test_square_payments.py` (NEW)
- `src/templates/dues/payment.html` (MODIFIED)
- `src/main.py` (MODIFIED — router registration)
- `src/config/settings.py` (MODIFIED — Square config)

### Phase B (Terminal/POS): PLANNED — Not yet scoped
### Phase C (Invoices): PLANNED — Not yet scoped
```

### Step 4: Full Test Suite Run

```bash
pytest -v --tb=short 2>&1 | tee test_results_week49.log
```

Expected: Previous tests + 15–20 new Square tests. Zero regressions.

### Step 5: Documentation Updates

- **CLAUDE.md:** Update payment section (Stripe → Square), Phase 8A status = COMPLETE, test count, version
- **CHANGELOG.md:** Week 49 entry
- **docs/IP2A_BACKEND_ROADMAP.md:** Phase 8 section — mark Phase A complete
- **docs/IP2A_MILESTONE_CHECKLIST.md:** Phase 8 section — check off Phase A tasks

### Week 49 Acceptance Criteria

- [ ] 15–20 Square payment tests passing
- [ ] All Square API calls mocked (verify: `grep -rn "sandbox" src/tests/test_square_payments.py` returns 0)
- [ ] Stripe skip markers removed or tests converted
- [ ] ADR-018 updated with Phase A completion
- [ ] Full test suite passes (all existing + new tests)
- [ ] CLAUDE.md accurate (version, test count, Phase 8A status)
- [ ] CHANGELOG.md updated
- [ ] Roadmap and Checklist updated
- [ ] `test_results_week49.log` saved

### Week 49 Git Commit

```bash
git add -A
git commit -m "feat(payments): Week 49 — Square testing and Phase 8A close-out (v0.9.23-alpha)

- Created test_square_payments.py (15+ tests: service, API, webhook, frontend)
- All Square API calls mocked — no sandbox dependency
- Removed/converted Stripe skip markers
- Updated ADR-018: Phase A marked COMPLETE
- Full test suite passes
- Updated CLAUDE.md, CHANGELOG.md, Roadmap, Checklist
- Spoke Owner: Spoke 1 (Core Platform)"

git push origin develop
```

---

## Cross-Cutting Changes Summary (For Hub Handoff)

After completing Weeks 47–49, generate a Hub handoff note listing ALL cross-cutting changes:

| File | Change | Week |
|------|--------|------|
| `src/main.py` | Added square_payments_router registration | 48 |
| `src/config/settings.py` | Added 5 Square config vars | 47 |
| `.env.example` | Added Square env vars | 47 |
| `requirements.txt` | Added squareup, confirmed stripe removed | 47 |
| `src/templates/dues/payment.html` | Square SDK integration | 48 |
| `conftest.py` | Any new fixtures added | 49 (if needed) |

---

## Implementation Decision Points (For Claude Code)

These are places where you MUST inspect the existing codebase before coding, because the exact patterns may differ from what's shown above:

1. **Auth dependency import path** — Check `src/routers/` for how other routers import auth dependencies
2. **Database session dependency** — Verify `get_db` import path (could be `src/db/session.py` or `src/core/database.py`)
3. **DuesPayment model fields** — Check if `stripe_payment_id` exists, was renamed, or was removed
4. **Audit service pattern** — Read `src/services/audit_service.py` for the correct `log_action()` signature
5. **Test fixture names** — Check `conftest.py` for `db_session` vs `db`, `client` vs `test_client`, etc.
6. **Frontend route pattern** — Check how dues payment pages are currently routed (URL path, template name)
7. **Settings pattern** — Verify if settings use Pydantic BaseSettings, dataclass, or plain module

**When in doubt, read the existing code first.** The patterns in this document are based on the project's documented conventions, but the actual implementation may have evolved.

---

## Version Progression

| Week | Version | Milestone |
|------|---------|-----------|
| 47 | v0.9.21-alpha | Square SDK + service layer |
| 48 | v0.9.22-alpha | Square API + frontend |
| 49 | v0.9.23-alpha | Square tested + Phase 8A complete |

---

*Claude Code Instructions — Weeks 47–49 — Phase 8A Square Online Payments*
*Spoke Owner: Spoke 1 (Core Platform)*
*Generated by Hub Project — February 6, 2026*
*ADR Reference: ADR-018 (Stripe → Square Migration)*
