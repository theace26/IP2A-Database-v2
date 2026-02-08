# ADR-018: Square Payment Integration

**Status:** Phase A Complete — Square Payment Integration Live
**Date:** February 5, 2026 (Updated February 8, 2026)
**Supersedes:** ADR-013 (Stripe Payment Integration)
**Decision Makers:** Xerxes (Project Lead), Hub Project
**Related ADRs:** ADR-008 (Audit Logging), ADR-003 (Authentication)

---

## Context

UnionCore requires payment processing for member dues, fees, and other financial transactions. ADR-013 originally selected Stripe as the payment processor, and a Stripe integration was implemented during Week 11 (Stripe Checkout + webhook handling).

**The union hall already uses Square for in-person payment processing.** This creates an operational split: walk-in payments go through Square, online payments go through Stripe, and staff must reconcile two separate payment ecosystems. This is inefficient, error-prone, and unnecessary.

### Why Square Over Stripe

| Factor | Stripe (Current) | Square (Proposed) |
|--------|-------------------|-------------------|
| In-person payments | Not used | **Already deployed at the hall** |
| Staff familiarity | Requires training | **Staff already knows Square Dashboard** |
| Merchant account | Separate from hall operations | **Same account as hall operations** |
| Reconciliation | Two systems to reconcile | **One unified system** |
| Terminal/POS | Would require new hardware | **Hardware already exists** |
| Invoicing | Stripe Invoices (unused) | **Square Invoices (potential)** |
| Online tokenization | Stripe.js (client-side) | Square Web Payments SDK (client-side) |
| PCI posture | SAQ-A (card data never touches server) | **SAQ-A (identical posture)** |

The deciding factor is not technical — both processors are capable. The deciding factor is **operational integration**: one payment ecosystem for the entire union hall instead of two.

---

## Decision

**Replace Stripe with Square as the sole payment processor for UnionCore.** Implementation will be phased:

### Phase A: Online Payment Migration (Replace Stripe)
- Replace Stripe.js with Square Web Payments SDK (client-side tokenization)
- Replace `stripe` Python package with `squareup` Python SDK
- Replace StripePaymentService with SquarePaymentService
- Replace Stripe webhooks with Square webhooks
- Update frontend payment forms (Jinja2 templates)
- Remove all Stripe code, tests, and configuration
- **This is the only phase that constitutes "migration." Phases B and C are new features.**

### Phase B: Square Terminal/POS Integration (New Feature)
- Connect Square Terminal at the union hall to UnionCore
- Walk-in dues payments automatically recorded in UnionCore
- Unified payment history: online + in-person in one view
- Uses Square Terminal API (device pairing, checkout creation)

### Phase C: Square Invoices Integration (New Feature)
- Automated dues billing via Square Invoices API
- Members receive professional invoices with online pay links
- Reduces manual follow-up for overdue dues
- Potential for recurring billing automation

### Phasing Rules
- **Phase A must be complete before removing any Stripe code from production**
- **Phase B and C are independent** — they can be built in any order after Phase A
- **Phase B and C are scope expansions** — they deliver capabilities UnionCore doesn't have today
- **Phase B and C should not block Phase 7 stabilization** — schedule them after referral/dispatch is stable

---

## Stripe Removal (Week 35 — February 2026)

All Stripe code was removed from the codebase in Week 35 sprint:

### What Was Removed
- Stripe SDK (`stripe` package) from requirements.txt
- `src/services/payment_service.py` — Stripe Checkout session creation
- `src/routers/webhooks/stripe_webhook.py` — Webhook handler and verification
- Stripe payment routes from `src/routers/dues_frontend.py` (initiate, success, cancel)
- Stripe configuration from `src/config/settings.py` (STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET)
- Stripe router registration from `src/main.py`
- Stripe health check from `src/routers/health.py`
- Stripe CSP entries from `src/middleware/security_headers.py`
- Stripe environment variables from `.env.example`
- Stripe test files: `src/tests/test_stripe_integration.py`, `src/tests/test_stripe_frontend.py` (~27 tests)

### What Was Preserved
- Dues tracking models (DuesPayment, DuesRate, DuesPeriod, DuesAdjustment)
- Dues service layer (calculation, recording, querying)
- Dues API routes and frontend routes
- Dues frontend templates and partials
- All non-Stripe dues tests
- `stripe_customer_id` column on Member (historical data — to be renamed to `processor_customer_id` in Phase A)
- `DuesPaymentMethod.STRIPE_*` enum values (historical payment records)
- Payment success/cancel templates (generic, reusable for Square)
- Alembic migrations (historical record — never deleted)
- ADR-013 (marked Superseded, retained for historical reference)

### Status
- **Stripe Code Removed:** Week 35 (February 6, 2026)
- **Square Phase A:** ✅ **COMPLETE** (Weeks 47-49, February 8, 2026)
- **Square Phase B:** Pending — Terminal/POS integration
- **Square Phase C:** Pending — Invoice automation

---

## Phase A Implementation (Weeks 47-49 — February 2026)

### Week 47: Square SDK Integration & Service Layer

**Completed:**
- Installed Square SDK (`squareup>=35.0.0`)
- Added configuration to `.env.example` and `src/config/settings.py`
- Created `SquarePaymentService` at `src/services/square_payment_service.py`
  - `create_payment()` - Process payments via Square Web Payments SDK nonces
  - `get_payment_status()` - Query payment status from Square API
  - `process_refund()` - Refund processing with audit trails (Officer+ role)
  - `verify_webhook()` - Webhook signature verification
- Added `dues_payments` to `AUDITED_TABLES` (7-year NLRA compliance)
- Verified Stripe code fully archived (only in historical migrations)

**Technical Implementation:**
- Square client import: `from square.client import Square`
- DuesPayment model uses existing `reference_number` field for Square payment ID
- All payment operations logged via `audit_service.log_update()`
- Full error handling with graceful degradation

### Week 48: API Router & Frontend Integration

**Completed:**
- Created payment API router (`src/routers/square_payments.py`) with 4 endpoints:
  - `POST /api/v1/payments/process` - Process payment with Square nonce
  - `GET /api/v1/payments/{square_payment_id}` - Query payment status
  - `POST /api/v1/payments/{square_payment_id}/refund` - Process refunds
  - `POST /api/v1/payments/webhooks/square` - Webhook handler (no auth, signature verification)
- Built frontend payment form (`src/templates/dues/payments/pay.html`)
  - Square Web Payments SDK integration (client-side tokenization)
  - Conditional SDK loading (sandbox vs production based on SQUARE_ENVIRONMENT)
  - Real-time payment processing with error handling
  - Automatic redirect to success page after payment
- Created payment initiation route in `dues_frontend.py`
  - `/dues/payments/initiate/{member_id}/{period_id}` - Renders payment form
  - Creates or retrieves DuesPayment record
  - Calculates amount from member's dues rate
  - Passes Square config to template
- Updated "Pay Now Online" button in member payment history
- Registered router in `src/main.py`

**Payment Flow:**
1. Member clicks "Pay Now Online" → Payment initiation route
2. Backend creates/retrieves DuesPayment record
3. Payment form renders with Square Web Payments SDK
4. Member enters card → Square tokenizes client-side (generates nonce)
5. JavaScript sends nonce to `/api/v1/payments/process`
6. SquarePaymentService processes payment via Square API
7. Backend updates `DuesPayment.reference_number` with Square payment ID
8. Success → redirect to success page

### Week 49: Testing & Phase A Close-Out

**Completed:**
- Created comprehensive test suite (`src/tests/test_square_payments.py`)
  - 8 service tests (create_payment, get_payment_status, process_refund, error handling)
  - 4 API router tests (process endpoint, status endpoint, refund endpoint, webhooks)
  - 6 webhook tests (signature verification, event handling)
  - **Total: 18 tests** — all Square API calls mocked
- Verified Stripe skip markers already removed (Week 35)
- Updated ADR-018 with Phase A completion (this section)
- Updated CLAUDE.md and CHANGELOG.md with implementation details

**Files Created:**
- `src/services/square_payment_service.py`
- `src/routers/square_payments.py`
- `src/templates/dues/payments/pay.html`
- `src/tests/test_square_payments.py`

**Files Modified:**
- `requirements.txt` - Added squareup SDK
- `.env.example` - Added 5 Square config vars
- `src/config/settings.py` - Added Square settings
- `src/services/audit_service.py` - Added dues_payments to AUDITED_TABLES
- `src/main.py` - Registered square_payments router
- `src/routers/dues_frontend.py` - Added payment initiation route
- `src/templates/dues/payments/member.html` - Updated Pay Now button

**Security Posture:**
- PCI SAQ-A compliance (card data never touches UnionCore servers)
- Client-side tokenization via Square Web Payments SDK
- All payment endpoints require authentication (except webhook, which uses signature verification)
- Full audit trail for all payment attempts (success, failure, error)

**Version:** v0.9.23-alpha

---

## Technical Architecture

### Client-Side Tokenization (Phase A)
```
Browser                          UnionCore Server              Square API
  |                                    |                          |
  |  1. Load Square Web Payments SDK   |                          |
  |  2. User enters card info          |                          |
  |  3. SDK tokenizes → nonce          |                          |
  |  4. POST /payments {nonce, amount} |                          |
  |  --------------------------------> |                          |
  |                                    | 5. CreatePayment(nonce)  |
  |                                    | -----------------------> |
  |                                    | 6. Payment result        |
  |                                    | <----------------------- |
  |                                    | 7. Log to audit trail    |
  |  8. Confirmation                   |                          |
  |  <-------------------------------- |                          |
```

**Critical:** Card data NEVER touches UnionCore servers. The Square Web Payments SDK handles PCI-sensitive data entirely in the browser. UnionCore only receives a single-use nonce.

### Environment Configuration
```env
# Square Configuration
SQUARE_ENVIRONMENT=sandbox          # sandbox | production
SQUARE_APPLICATION_ID=sq0idp-xxx    # Application ID from Square Developer
SQUARE_ACCESS_TOKEN=EAAAl-xxx       # Access token (NEVER in code or docs)
SQUARE_LOCATION_ID=LID-xxx          # Union hall location ID
SQUARE_WEBHOOK_SIGNATURE_KEY=xxx    # For webhook verification

# Feature Flags (for phased rollout)
SQUARE_ONLINE_PAYMENTS_ENABLED=true
SQUARE_TERMINAL_ENABLED=false       # Phase B
SQUARE_INVOICES_ENABLED=false       # Phase C
```

### Service Layer Pattern
```python
# src/services/square_payment_service.py
class SquarePaymentService:
    """Replaces StripePaymentService. Same interface pattern."""

    def create_payment(self, nonce: str, amount_cents: int, ...) -> PaymentResult
    def get_payment(self, payment_id: str) -> PaymentResult
    def refund_payment(self, payment_id: str, amount_cents: int) -> RefundResult
    def list_payments(self, member_id: int, ...) -> List[PaymentResult]
    def verify_webhook(self, body: bytes, signature: str) -> WebhookEvent
```

### Webhook Events (Phase A)
| Square Event | UnionCore Action |
|-------------|-----------------|
| `payment.completed` | Record payment, update dues status |
| `payment.failed` | Log failure, notify staff |
| `refund.completed` | Record refund, adjust dues balance |
| `refund.failed` | Log failure, alert admin |

### Terminal Events (Phase B — Future)
| Square Event | UnionCore Action |
|-------------|-----------------|
| `terminal.checkout.completed` | Record walk-in payment |
| `terminal.checkout.cancelled` | Log cancellation |

### Database Impact
- `dues_payments` table: Add `square_payment_id` column (VARCHAR), drop `stripe_payment_id`
- Or: Rename column `stripe_payment_id` → `processor_payment_id` (processor-agnostic)
- `payment_processor` enum or config value for future flexibility
- **Migration must handle existing Stripe payment records** — archive, don't delete

### Audit Requirements (Unchanged)
- All payment transactions logged to business audit trail (ADR-008)
- Payment amounts, member IDs, timestamps in audit log
- Square API credentials NEVER logged
- PII redaction in operational logs (Loki) unchanged

---

## Files Affected

### Remove (Stripe)
- `src/services/stripe_payment_service.py` (or equivalent)
- `src/routers/stripe_webhook.py` (or equivalent)
- `src/tests/test_stripe_integration.py`
- `src/tests/test_stripe_frontend.py`
- Stripe.js references in Jinja2 templates
- `stripe` from `requirements.txt`

### Create (Square)
- `src/services/square_payment_service.py`
- `src/routers/square_webhook.py`
- `src/tests/test_square_integration.py`
- `src/tests/test_square_frontend.py`
- Square Web Payments SDK in payment templates
- `squareup` in `requirements.txt`

### Modify
- `src/config/settings.py` — Square environment variables
- `CLAUDE.md` — Update stack references (Stripe → Square)
- `docs/README.md` — Update ADR references
- `docs/decisions/README.md` — Add ADR-018, mark ADR-013 superseded
- Payment-related Jinja2 templates
- `dues_payments` migration (column rename or addition)
- `.env.example` — Square configuration template

---

## Consequences

### Positive
- **Unified payment ecosystem** — one processor for online and in-person
- **Reduced staff training** — Square Dashboard already familiar
- **Simplified reconciliation** — single source of truth for all payments
- **Future Terminal integration** — walk-in payments linkable to member records
- **Future Invoice automation** — automated dues billing possible

### Negative
- **Migration effort** — must replace working Stripe integration
- **Existing Stripe test data** — any test transactions in Stripe need archiving
- **Square SDK learning curve** — different API patterns from Stripe (nonce vs payment method)
- **Dependency on Square** — vendor lock-in (mitigated by service layer abstraction)

### Neutral
- PCI compliance posture unchanged (SAQ-A)
- Audit logging requirements unchanged
- Service layer pattern unchanged (swap implementation, keep interface)

---

## Square SDK Reference

### Python SDK
```bash
pip install squareup
```

### Web Payments SDK (Frontend)
```html
<!-- Square Web Payments SDK -->
<script src="https://sandbox.web.squarecdn.com/v1/square.js"></script>
<!-- Production: https://web.squarecdn.com/v1/square.js -->
```

### Sandbox Testing
- Sandbox Application ID and Access Token from Square Developer Dashboard
- Test card numbers: `4111 1111 1111 1111` (Visa, success)
- Sandbox payments don't charge real cards
- Square Developer Dashboard: https://developer.squareup.com

---

## Timeline

| Phase | Scope | Estimated Hours | Depends On |
|-------|-------|-----------------|------------|
| Phase A | Replace Stripe with Square online payments | 15-20 | Phase 7 stabilization |
| Phase B | Square Terminal/POS integration | 10-15 | Phase A |
| Phase C | Square Invoices integration | 10-15 | Phase A |

**Phase A target:** After Phase 7 referral/dispatch is stable (not before).
**Phases B & C:** Schedule based on union hall priorities. These are enhancements, not blockers.

---

## Migration Checklist

- [ ] Create Square Developer account and sandbox application
- [ ] Add Square sandbox credentials to `.env`
- [ ] Implement SquarePaymentService (mirror Stripe service interface)
- [ ] Implement Square webhook handler with signature verification
- [ ] Update payment frontend templates (Stripe.js → Square Web Payments SDK)
- [ ] Write Square integration tests (using sandbox)
- [ ] Write Square frontend tests
- [ ] Migration: `stripe_payment_id` → `square_payment_id` (or processor-agnostic)
- [ ] Archive existing Stripe payment records (don't delete — audit trail)
- [ ] Remove all Stripe code, package, and configuration
- [ ] Update ADR-013 status to "Superseded by ADR-018"
- [ ] Update CLAUDE.md stack references
- [ ] Update docs/README.md ADR index
- [ ] End-to-end test: sandbox payment → webhook → dues update → audit log
- [ ] Production cutover: swap sandbox → production credentials

---

**Document Version:** 1.0
**Created:** February 5, 2026
**Author:** Hub Project
