# Stripe Payment Integration - Continuity Document

**Project:** UnionCore (formerly IP2A Database v2)
**Date:** January 30, 2026
**Handoff From:** Planning session (Claude)
**Handoff To:** Developer chatbot
**Repository:** github.com/theace26/IP2A-Database-v2

---

## ⚠️ Important Reminder

> **Documentation Requirement:** Every development session MUST end with a documentation review. See "End-of-Session Documentation" section at the bottom of this document.

---

## Context

Xerxes is building UnionCore, a union management platform for IBEW Local 46. The backend is at v0.7.0-ready with FastAPI, PostgreSQL 16, and ~120 API endpoints. Frontend development (Jinja2 + HTMX + Alpine.js) is the next phase.

We discussed adding **payment processing for dues collection** and determined the approach.

---

## Decision: Use Stripe (Not Square)

**Rationale:**
- Superior developer experience and documentation
- Better subscription/recurring support (dues are inherently recurring)
- ACH bank transfers at 0.8% vs 2.9% for card (significant for large dues)
- Industry standard = more community support
- Pricing identical to Square (2.9% + $0.30 per card transaction)

---

## Integration Approach: Stripe Checkout Sessions

**Pattern:** Redirect users to Stripe's hosted payment page. Never handle card numbers directly. This keeps PCI compliance on Stripe's side.

```
Member clicks "Pay Dues"
    │
    ▼
Backend creates Checkout Session (via Stripe API)
    │
    ▼
Member redirected to Stripe's hosted page
    │
    ├── Pays successfully → Redirect to success_url
    │                       Webhook fires to /api/v1/webhooks/stripe
    │
    └── Cancels → Redirect to cancel_url
```

**Critical:** Never trust the redirect alone. Always verify payment via webhook.

---

## Technical Details Discussed

### SDK Installation

```bash
pip install stripe --break-system-packages
```

Add to `requirements.txt`:
```
stripe>=8.0.0
```

### Environment Variables Needed

```bash
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

### Stripe Dashboard Configuration Needed

1. **API Keys:** Dashboard → Developers → API Keys
2. **Webhook Endpoint:** Dashboard → Developers → Webhooks → Add endpoint
   - URL: `https://your-domain.com/api/v1/webhooks/stripe`
   - Events to subscribe:
     - `checkout.session.completed`
     - `checkout.session.expired`
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`
     - `charge.refunded`

**NOT needed:** OAuth redirect URIs (that's for Stripe Connect platforms)

### Stripe CLI for Local Development

```bash
# Install
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local dev server
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe

# Trigger test events
stripe trigger checkout.session.completed
```

### Test Card Numbers

| Card Number | Result |
|-------------|--------|
| 4242 4242 4242 4242 | Success |
| 4000 0000 0000 0002 | Decline |
| 4000 0000 0000 3220 | 3D Secure required |

---

## Code Snippets Provided

### PaymentService (Starter)

```python
# services/payment_service.py
import stripe
from decimal import Decimal
from app.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    @staticmethod
    async def create_dues_checkout_session(
        member_id: int,
        amount: Decimal,
        description: str,
        success_url: str,
        cancel_url: str
    ) -> str:
        amount_cents = int(amount * 100)
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card', 'us_bank_account'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': amount_cents,
                    'product_data': {
                        'name': description,
                        'description': f'IBEW Local 46 - Member #{member_id}',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            metadata={
                'member_id': str(member_id),
                'payment_type': 'dues',
            },
            billing_address_collection='required',
        )
        
        return session.url
```

### Webhook Handler (Starter)

```python
# api/v1/webhooks/stripe_webhook.py
from fastapi import APIRouter, Request, HTTPException, Header
import stripe
from app.config import settings
from app.services.dues_service import DuesService

router = APIRouter()

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature")
):
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        member_id = int(session['metadata']['member_id'])
        amount_paid = Decimal(session['amount_total']) / 100
        
        await DuesService.record_payment(
            member_id=member_id,
            amount=amount_paid,
            stripe_session_id=session['id'],
            payment_method=session['payment_method_types'][0],
        )
    
    return {"status": "received"}
```

---

## Recommended Sequencing

```
Phase 1: Basic frontend (login, dashboard, staff list, IP2A entry)  ← CURRENT
    │
Phase 2: Dues tracking UI (view balances, payment history)
    │
Phase 3: Stripe integration  ← THIS WORK
    │   - PaymentService
    │   - Webhook endpoint (no auth, signature verified)
    │   - "Pay Now" button in dues UI
    │   - stripe_customer_id field on Member model
    │
Phase 4: Recurring subscriptions (if needed)
    │
Phase 5: QuickBooks sync (payment data → accounting)
```

---

## Components to Build

| Component | Complexity | Notes |
|-----------|------------|-------|
| `PaymentService` | Medium | Wrapper around Stripe SDK |
| Webhook endpoint `/api/v1/webhooks/stripe` | Medium | No auth, verify signature |
| `stripe_customer_id` on Member model | Easy | For recurring payments |
| Payment link generation | Easy | "Pay Now" redirects to Stripe |
| Payment history view | Easy | Query Stripe or store locally |
| Reconciliation job | Medium | Verify records match Stripe |

---

## Open Questions for Developer Session

1. Do we need recurring subscriptions immediately, or just one-time payments first?
2. Should payment history be stored locally or queried from Stripe on demand?
3. Where does the "Pay Dues" button live in the frontend hierarchy?
4. Do we need an ADR-009 for payment integration decisions?

---

## Reference Links

- Stripe Python SDK: https://github.com/stripe/stripe-python
- Stripe Checkout Docs: https://stripe.com/docs/payments/checkout
- Webhook Integration: https://stripe.com/docs/webhooks
- Stripe CLI: https://stripe.com/docs/stripe-cli
- Test Cards: https://stripe.com/docs/testing#cards

---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session.

### Before Ending This Session:

1. **Scan `/docs/*`** - Review all documentation files
2. **Update existing docs** - Reflect changes, progress, and decisions
3. **Create new docs** - If needed for new components or concepts
4. **ADR Review** - Update or create Architecture Decision Records as necessary
5. **Session log entry** - Record what was accomplished

### Documentation Checklist:

| Document | Updated? | Notes |
|----------|----------|-------|
| SESSION_LOG.md | [ ] | |
| CHANGELOG.md | [ ] | |
| ADR-009 (Payments)? | [ ] | Create if architectural decisions made |
| MILESTONE_*.md | [ ] | |
| This continuity doc | [ ] | |

This ensures historical record-keeping and project continuity ("bus factor" protection).

---

*End of continuity document*
