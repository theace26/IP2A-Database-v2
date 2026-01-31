# ADR-013: Stripe Payment Integration for Dues Collection

## Status
Accepted

## Date
2026-01-30

## Context

UnionCore (IP2A Database v2) manages dues tracking for IBEW Local 46 members. The existing system tracks:
- Dues rates per member classification
- Billing periods (monthly/quarterly)
- Payment records and adjustments
- Member balances and payment history

However, members currently must pay dues via:
- Cash/check at the union hall
- Manual bank transfers
- Phone payment over the counter

This creates operational burden:
- Staff manually records payments
- Reconciliation takes time
- Members have limited payment options
- No automatic payment confirmations
- No online payment history for members

We need to integrate online payment processing to:
1. Allow members to pay dues online 24/7
2. Reduce manual data entry for staff
3. Provide instant payment confirmations
4. Support both card and ACH bank transfers
5. Maintain PCI compliance without handling card data directly
6. Track payment history automatically

## Decision

We will integrate **Stripe Checkout Sessions** for online dues payment processing.

### Payment Flow

```
Member clicks "Pay Dues" in frontend
    │
    ▼
Backend creates Stripe Checkout Session (via Stripe API)
    │
    ▼
Member redirected to Stripe's hosted payment page
    │
    ├── Pays successfully → Redirect to success_url
    │                       Webhook fires to /api/v1/webhooks/stripe
    │                       Backend records payment in DuesPayment table
    │
    └── Cancels → Redirect to cancel_url
```

### Key Design Choices

1. **Stripe Checkout (not Elements)**
   - Stripe hosts the payment page (PCI compliance stays with Stripe)
   - No need to handle card numbers in our application
   - Simpler integration, faster time to market
   - Built-in fraud detection and 3D Secure support

2. **Payment Methods Supported**
   - Credit/Debit cards (2.9% + $0.30 per transaction)
   - ACH bank transfers (0.8% per transaction, $5 cap)
   - ACH preferred for large dues payments (significant cost savings)

3. **Webhook Verification**
   - Never trust redirect URLs alone (can be manipulated)
   - Always verify payment via Stripe webhook signature
   - Webhook endpoint at `/api/v1/webhooks/stripe` (no auth, signature verified)

4. **Member Association**
   - Store `stripe_customer_id` on Member model for recurring payments
   - Pass `member_id` in Checkout Session metadata
   - Webhook handler creates DuesPayment record linked to member

5. **Payment Modes**
   - Phase 1: One-time payments (`mode='payment'`)
   - Phase 2 (future): Recurring subscriptions (`mode='subscription'`)

### Environment Configuration

Required environment variables:
- `STRIPE_SECRET_KEY` - Server-side API key
- `STRIPE_PUBLISHABLE_KEY` - Client-side key (future, if using Stripe.js)
- `STRIPE_WEBHOOK_SECRET` - Webhook signature verification

### Stripe Dashboard Setup

1. **API Keys**: Dashboard → Developers → API Keys
2. **Webhook Endpoint**: Dashboard → Developers → Webhooks
   - URL: `https://unioncore.domain.com/api/v1/webhooks/stripe`
   - Events to subscribe:
     - `checkout.session.completed` - Payment succeeded
     - `checkout.session.expired` - Session timed out
     - `payment_intent.succeeded` - Alternate success event
     - `payment_intent.payment_failed` - Payment failed
     - `charge.refunded` - Refund processed

## Consequences

### Positive

- **Member Convenience** - Pay dues online 24/7 from any device
- **Reduced Staff Work** - No manual payment entry, automatic reconciliation
- **PCI Compliance** - Stripe handles all card data, we never touch it
- **Cost-Effective ACH** - 0.8% ACH fees vs 2.9% card (big savings for large payments)
- **Instant Confirmation** - Members get email receipt from Stripe immediately
- **Audit Trail** - All payments logged in both Stripe dashboard and our database
- **Fraud Protection** - Stripe's built-in fraud detection and 3D Secure
- **Future-Ready** - Easy to add recurring subscriptions later

### Negative

- **Transaction Fees** - 2.9% + $0.30 per card, 0.8% per ACH
- **Vendor Lock-In** - Switching payment processors later requires code changes
- **External Dependency** - Downtime at Stripe affects our payment capability
- **Webhook Delays** - Webhook processing is async (5-30 second delay typical)
- **Test Mode Limitations** - Must use production mode for real payments (test cards don't work in prod)

### Mitigations

- **Fee Transparency** - Show members ACH option for lower fees
- **Webhook Retry Logic** - Stripe retries failed webhooks up to 3 days
- **Fallback Payment Methods** - Keep cash/check option for members without cards
- **Monitoring** - Alert on webhook failures or processing delays
- **Reconciliation Job** - Nightly job to verify Stripe payments match our database

## Implementation Components

| Component | Location | Purpose |
|-----------|----------|---------|
| PaymentService | `src/services/payment_service.py` | Create Checkout Sessions, retrieve payment details |
| Stripe webhook router | `src/routers/webhooks/stripe_webhook.py` | Handle Stripe events |
| stripe_customer_id field | Migration to add to `members` table | Link member to Stripe customer |
| Frontend "Pay Dues" button | `src/templates/dues/payments/` | Initiate payment flow |
| Environment config | `src/config/settings.py` | Load Stripe API keys |

### New Database Fields

```sql
ALTER TABLE members ADD COLUMN stripe_customer_id VARCHAR(100) UNIQUE;

-- DuesPayment already has these fields (from existing schema):
-- - payment_method (add 'stripe_card', 'stripe_ach' to enum)
-- - notes (store Stripe session ID for reference)
```

## Alternatives Considered

### Option A: Square Payments
- **Pros:** Same pricing as Stripe (2.9% + $0.30), well-known brand
- **Cons:** Weaker developer docs, less robust subscription support, fewer ACH options
- **Verdict:** Rejected - Stripe has better developer experience

### Option B: PayPal Business
- **Pros:** Familiar to users, no merchant account needed
- **Cons:** Higher fees (3.49% + $0.49), worse developer experience, poor subscription API
- **Verdict:** Rejected - More expensive, harder to integrate

### Option C: Direct Merchant Account + Authorize.net
- **Pros:** Lower per-transaction fees (~2.5%), more control
- **Cons:** Complex PCI compliance, must handle card data, higher fixed monthly costs
- **Verdict:** Rejected - PCI burden not worth 0.4% savings

### Option D: Build Custom ACH Integration (Plaid + Dwolla)
- **Pros:** Lowest fees (0.25% via Dwolla), full control
- **Cons:** Complex integration, bank account verification delays, higher development cost
- **Verdict:** Rejected - Over-engineering for v1, can add later if needed

### Option E: Stripe Elements (custom UI)
- **Pros:** More control over payment form design
- **Cons:** More complex integration, we handle more PCI scope
- **Verdict:** Rejected for v1 - Checkout Sessions are simpler, can upgrade to Elements later

## Testing Strategy

### Test Mode (Development)

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local dev
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe

# Trigger test events
stripe trigger checkout.session.completed
```

### Test Cards

| Card Number | Result | Use Case |
|-------------|--------|----------|
| 4242 4242 4242 4242 | Success | Happy path testing |
| 4000 0000 0000 0002 | Decline | Error handling |
| 4000 0000 0000 3220 | 3D Secure required | Auth flow testing |
| 4000 0025 0000 3155 | Requires authentication | SCA testing |

### Test Bank Accounts (ACH)

- Routing: `110000000`
- Account: `000123456789`

## Future Enhancements

1. **Recurring Subscriptions** (Phase 2)
   - Use `mode='subscription'` in Checkout Session
   - Auto-charge members monthly/quarterly
   - Handle subscription cancellation, upgrades

2. **Payment Plans** (Phase 3)
   - Allow members to pay large balances in installments
   - Use Stripe Billing for multi-payment plans

3. **Stripe Customer Portal** (Phase 4)
   - Let members manage their payment methods
   - View past invoices, download receipts

4. **QuickBooks Integration** (Phase 5)
   - Sync Stripe payments to QuickBooks for accounting
   - Use Stripe webhooks to trigger QuickBooks API calls

## References

- [Stripe Python SDK Documentation](https://github.com/stripe/stripe-python)
- [Stripe Checkout Sessions](https://stripe.com/docs/payments/checkout)
- [Stripe Webhooks Guide](https://stripe.com/docs/webhooks)
- [Stripe CLI](https://stripe.com/docs/stripe-cli)
- [Stripe Test Cards](https://stripe.com/docs/testing#cards)
- [Stripe ACH Direct Debit](https://stripe.com/docs/payments/ach-debit)
- [PCI Compliance Levels](https://www.pcisecuritystandards.org/)

---

*This ADR documents the decision to use Stripe Checkout Sessions for online dues payment processing, chosen for its superior developer experience, PCI compliance handling, and cost-effective ACH support.*

---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session.

### Before Ending This Session:

1. **Scan `/docs/*`** - Review all documentation files
2. **Update existing docs** - Reflect changes, progress, and decisions
3. **Create new docs** - If needed for new components or concepts
4. **ADR Review** - Update or create Architecture Decision Records as necessary
5. **Session log entry** - Record what was accomplished

This ensures historical record-keeping and project continuity ("bus factor" protection).
