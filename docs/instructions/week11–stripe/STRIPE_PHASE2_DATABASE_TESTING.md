# Stripe Integration Phase 2: Database Migrations & Local Testing

**Project:** UnionCore (IP2A Database v2)
**Phase:** Stripe Integration - Phase 2 of 3
**Estimated Duration:** 1.5-2 hours
**Branch:** `develop` (ALWAYS work on develop, main is frozen for Railway demo)
**Prerequisite:** Stripe Phase 1 complete (PaymentService + Webhook handler)

---

## Session Overview

This session completes the database layer for Stripe integration and sets up local testing infrastructure. After this session, you'll be able to test the full payment flow locally.

---

## Pre-Session Checklist

```bash
# 1. Switch to develop branch
git checkout develop
git pull origin develop

# 2. Start environment
docker-compose up -d

# 3. Verify tests pass
pytest -v --tb=short

# 4. Verify Phase 1 files exist
ls -la src/services/payment_service.py
ls -la src/routers/webhooks/stripe_webhook.py
```

---

## Tasks

### Task 1: Create Database Migration for stripe_customer_id (30 min)

**Goal:** Add `stripe_customer_id` column to `members` table for tracking Stripe customers.

#### 1.1 Create Alembic Migration

```bash
# Generate migration
alembic revision --autogenerate -m "add_stripe_customer_id_to_members"
```

**Migration content:**
```python
"""add_stripe_customer_id_to_members

Revision ID: [auto-generated]
Revises: [previous]
Create Date: 2026-01-30

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '[auto-generated]'
down_revision = '[previous]'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add stripe_customer_id column
    op.add_column(
        'members',
        sa.Column('stripe_customer_id', sa.String(100), nullable=True, unique=True)
    )
    
    # Create index for faster lookups
    op.create_index(
        'ix_members_stripe_customer_id',
        'members',
        ['stripe_customer_id'],
        unique=True
    )


def downgrade() -> None:
    op.drop_index('ix_members_stripe_customer_id', table_name='members')
    op.drop_column('members', 'stripe_customer_id')
```

#### 1.2 Update Member Model

**File:** `src/models/member.py`

Add to the Member class:
```python
# Stripe Integration
stripe_customer_id: Mapped[Optional[str]] = mapped_column(
    String(100), 
    unique=True, 
    nullable=True,
    index=True,
    comment="Stripe customer ID for payment processing"
)
```

#### 1.3 Update Member Schema (if needed)

**File:** `src/schemas/member.py`

If schemas need updating for the new field:
```python
class MemberRead(MemberBase):
    # ... existing fields ...
    stripe_customer_id: Optional[str] = None
```

#### 1.4 Run Migration

```bash
# Apply migration
alembic upgrade head

# Verify
alembic current
```

---

### Task 2: Update DuesPayment Enum (20 min)

**Goal:** Add Stripe payment methods to the DuesPaymentMethod enum.

#### 2.1 Update Enum Definition

**File:** `src/db/enums/dues_enums.py`

```python
class DuesPaymentMethod(str, Enum):
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYROLL_DEDUCTION = "payroll_deduction"
    # Stripe payment methods (added Phase 2)
    STRIPE_CARD = "stripe_card"          # Credit/debit via Stripe Checkout
    STRIPE_ACH = "stripe_ach"            # ACH bank transfer via Stripe
    STRIPE_OTHER = "stripe_other"        # Future Stripe methods (Apple Pay, etc.)
```

#### 2.2 Create Migration for Enum Update

```bash
alembic revision --autogenerate -m "add_stripe_payment_methods_to_enum"
```

**Note:** PostgreSQL enum changes require special handling. The migration should:
```python
def upgrade() -> None:
    # Add new enum values
    op.execute("ALTER TYPE duespaymentmethod ADD VALUE IF NOT EXISTS 'stripe_card'")
    op.execute("ALTER TYPE duespaymentmethod ADD VALUE IF NOT EXISTS 'stripe_ach'")
    op.execute("ALTER TYPE duespaymentmethod ADD VALUE IF NOT EXISTS 'stripe_other'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values
    # This is intentionally left empty - enum values are additive only
    pass
```

#### 2.3 Apply Migration

```bash
alembic upgrade head
```

---

### Task 3: Install Stripe CLI (15 min)

**Goal:** Set up Stripe CLI for local webhook testing.

#### 3.1 Install Stripe CLI

**macOS:**
```bash
brew install stripe/stripe-cli/stripe
```

**Linux:**
```bash
# Download
curl -s https://packages.stripe.dev/api/security/keypair/stripe-cli-gpg/public | gpg --dearmor | sudo tee /usr/share/keyrings/stripe.gpg
echo "deb [signed-by=/usr/share/keyrings/stripe.gpg] https://packages.stripe.dev/stripe-cli-debian-local stable main" | sudo tee -a /etc/apt/sources.list.d/stripe.list
sudo apt update
sudo apt install stripe
```

**Docker (alternative):**
```bash
docker run --rm -it stripe/stripe-cli:latest login
```

#### 3.2 Login to Stripe

```bash
stripe login
```

This will open a browser to authenticate with your Stripe account.

#### 3.3 Get Webhook Secret

```bash
# Start webhook forwarding
stripe listen --forward-to localhost:8000/webhooks/stripe

# Note the webhook signing secret that's displayed:
# > Ready! Your webhook signing secret is whsec_xxxxxxxxxxxxx
```

**IMPORTANT:** Copy this `whsec_` secret to your `.env` file.

---

### Task 4: Configure Local Environment (10 min)

**Goal:** Set up `.env` with Stripe test keys.

#### 4.1 Get API Keys from Stripe Dashboard

1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy the **Publishable key** (`pk_test_...`)
3. Copy the **Secret key** (`sk_test_...`)

#### 4.2 Update .env File

```bash
# .env (local development)

# Stripe Payment Processing (TEST MODE)
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_from_cli
```

#### 4.3 Verify Configuration Loads

```python
# Quick test in Python shell
from src.config.settings import settings
print(f"Stripe configured: {bool(settings.STRIPE_SECRET_KEY)}")
```

---

### Task 5: Test Payment Flow (30 min)

**Goal:** Verify end-to-end payment flow works locally.

#### 5.1 Start Services

**Terminal 1 - API Server:**
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Stripe CLI Webhook Forwarding:**
```bash
stripe listen --forward-to localhost:8000/webhooks/stripe
```

#### 5.2 Create Test Checkout Session

Create a test script or use Python REPL:

```python
# test_stripe_payment.py
import asyncio
from decimal import Decimal
from src.services.payment_service import PaymentService

async def test_checkout():
    session_url = await PaymentService.create_dues_checkout_session(
        member_id=1,
        period_id=1,
        amount=Decimal("50.00"),
        description="January 2026 Dues",
        success_url="http://localhost:8000/dues/payments/success",
        cancel_url="http://localhost:8000/dues/payments/cancel",
        member_email="test@example.com"
    )
    print(f"Checkout URL: {session_url}")
    return session_url

# Run
asyncio.run(test_checkout())
```

#### 5.3 Complete Test Payment

1. Open the checkout URL in browser
2. Use test card: `4242 4242 4242 4242`
3. Any future expiry, any CVC, any postal code
4. Complete payment
5. Verify webhook received in Terminal 2
6. Check database for DuesPayment record

#### 5.4 Test Webhook Directly

```bash
# Trigger test webhook event
stripe trigger checkout.session.completed

# Watch Terminal 2 for webhook forwarding
# Check logs for payment processing
```

#### 5.5 Verify Database Records

```sql
-- Check for payment record
SELECT * FROM dues_payments 
WHERE notes LIKE 'Stripe%'
ORDER BY created_at DESC
LIMIT 5;

-- Check for stripe_customer_id on member
SELECT id, first_name, last_name, stripe_customer_id 
FROM members 
WHERE stripe_customer_id IS NOT NULL;
```

---

### Task 6: Write Integration Tests (20 min)

**Goal:** Add tests for Stripe integration.

**File:** `src/tests/test_stripe_integration.py`

```python
"""Tests for Stripe payment integration."""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from src.services.payment_service import PaymentService


class TestPaymentService:
    """Tests for PaymentService."""

    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session(self, mock_create):
        """Test creating a Stripe Checkout Session."""
        # Arrange
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_create.return_value = mock_session

        # Act
        result = PaymentService.create_dues_checkout_session(
            member_id=1,
            period_id=1,
            amount=Decimal("50.00"),
            description="Test Payment",
            success_url="http://localhost/success",
            cancel_url="http://localhost/cancel"
        )

        # Assert
        assert result == "https://checkout.stripe.com/test"
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs['mode'] == 'payment'
        assert call_kwargs['line_items'][0]['price_data']['unit_amount'] == 5000  # cents

    @patch('stripe.checkout.Session.create')
    def test_checkout_session_includes_metadata(self, mock_create):
        """Test that checkout session includes member/period metadata."""
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_create.return_value = mock_session

        PaymentService.create_dues_checkout_session(
            member_id=42,
            period_id=7,
            amount=Decimal("100.00"),
            description="Dues",
            success_url="http://localhost/success",
            cancel_url="http://localhost/cancel"
        )

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs['metadata']['member_id'] == '42'
        assert call_kwargs['metadata']['period_id'] == '7'
        assert call_kwargs['metadata']['payment_type'] == 'dues'

    @patch('stripe.Webhook.construct_event')
    def test_construct_webhook_event_valid(self, mock_construct):
        """Test webhook event construction with valid signature."""
        mock_event = {'type': 'checkout.session.completed'}
        mock_construct.return_value = mock_event

        result = PaymentService.construct_webhook_event(
            payload=b'test_payload',
            signature='test_signature'
        )

        assert result == mock_event
        mock_construct.assert_called_once()

    @patch('stripe.Webhook.construct_event')
    def test_construct_webhook_event_invalid_signature(self, mock_construct):
        """Test webhook event construction with invalid signature."""
        import stripe
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", "test_sig"
        )

        with pytest.raises(stripe.error.SignatureVerificationError):
            PaymentService.construct_webhook_event(
                payload=b'test_payload',
                signature='invalid_signature'
            )


class TestStripeWebhook:
    """Tests for Stripe webhook endpoint."""

    def test_webhook_requires_signature(self, client):
        """Test that webhook rejects requests without signature."""
        response = client.post(
            "/webhooks/stripe",
            json={"type": "test"}
        )
        assert response.status_code == 400

    @patch('src.services.payment_service.PaymentService.construct_webhook_event')
    def test_webhook_returns_200_on_success(self, mock_construct, client):
        """Test webhook returns 200 for valid events."""
        mock_construct.return_value = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'metadata': {'member_id': '1', 'period_id': '1'},
                    'amount_total': 5000,
                    'payment_method_types': ['card'],
                    'customer': 'cus_test123'
                }
            }
        }

        response = client.post(
            "/webhooks/stripe",
            content=b'test_payload',
            headers={"Stripe-Signature": "test_sig"}
        )
        
        assert response.status_code == 200
```

Run tests:
```bash
pytest src/tests/test_stripe_integration.py -v
```

---

## Acceptance Criteria

- [ ] Migration adds `stripe_customer_id` to `members` table
- [ ] `DuesPaymentMethod` enum includes `stripe_card`, `stripe_ach`, `stripe_other`
- [ ] Stripe CLI installed and authenticated
- [ ] `.env` configured with test Stripe keys
- [ ] Test checkout session creates successfully
- [ ] Webhook forwarding works (events received)
- [ ] Test card payment completes end-to-end
- [ ] DuesPayment record created on successful payment
- [ ] `stripe_customer_id` saved to member on first payment
- [ ] Integration tests pass

---

## Files Created/Modified

### Created
```
src/tests/test_stripe_integration.py
alembic/versions/xxx_add_stripe_customer_id_to_members.py
alembic/versions/xxx_add_stripe_payment_methods_to_enum.py
```

### Modified
```
src/models/member.py              # Added stripe_customer_id field
src/db/enums/dues_enums.py        # Added Stripe payment methods
src/schemas/member.py             # Added stripe_customer_id to schema (if needed)
.env                              # Added Stripe test credentials
```

---

## Test Cards Reference

| Card Number | Result |
|-------------|--------|
| 4242 4242 4242 4242 | Success |
| 4000 0000 0000 0002 | Decline |
| 4000 0000 0000 3220 | 3D Secure required |
| 4000 0025 0000 3155 | Requires auth (incomplete) |

**ACH Test Account:**
- Routing: 110000000
- Account: 000123456789

---

## Troubleshooting

### Webhook not receiving events
1. Verify Stripe CLI is running: `stripe listen --forward-to localhost:8000/webhooks/stripe`
2. Check webhook secret in `.env` matches CLI output
3. Verify API server is running on port 8000

### Checkout session fails
1. Verify `STRIPE_SECRET_KEY` is set correctly
2. Check Stripe dashboard for error logs
3. Verify amount is positive and reasonable

### Migration fails
1. Check existing enum values: `\dT+ duespaymentmethod` in psql
2. PostgreSQL enums are case-sensitive
3. Use `IF NOT EXISTS` to handle idempotency

---

## Next Session Preview

**Stripe Phase 3: Frontend Integration** will add:
- "Pay Dues" button to dues UI
- Payment initiation endpoint
- Success/cancel redirect pages
- Payment status display

---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** 

### Before Ending This Session:

Scan all documentation in `/app/*`. Update *ANY* & *ALL* relevant documentation as necessary with current progress for the historical record. Do not forget to update ADRs, Roadmap, Checklist, again only if necessary.

**Documentation Checklist:**

| Document | Updated? | Notes |
|----------|----------|-------|
| CLAUDE.md | [ ] | Update Stripe Phase 2 status |
| CHANGELOG.md | [ ] | Add Stripe Phase 2 entry |
| CONTINUITY.md | [ ] | Update current status |
| IP2A_MILESTONE_CHECKLIST.md | [ ] | Mark Phase 2 complete |
| IP2A_BACKEND_ROADMAP.md | [ ] | Update if needed |
| Session log created | [ ] | `docs/reports/session-logs/` |

This ensures historical record-keeping and project continuity ("bus factor" protection).

---

*End of instruction document*
