# Hub → Spoke 1 Handoff: Square Payment Migration (Phase A)

**Handoff Type:** Hub Decision → Spoke Implementation Planning
**Date:** February 5, 2026
**From:** Hub Project
**To:** Spoke 1 (Core Platform) — or direct to Claude Code when Spoke 1 is created
**Priority:** Planned — DO NOT EXECUTE until Phase 7 is stable
**Governing ADR:** ADR-018 (Square Payment Integration)

---

## ⚠️ THIS IS A PLANNING HANDOFF, NOT AN EXECUTION ORDER

Phase 7 referral/dispatch stabilization takes priority. The user will explicitly say when to begin Square migration. This handoff exists so the Spoke has full context when the time comes.

---

## Hub Decision Summary

**ADR-018 accepted February 5, 2026.** Stripe is being replaced by Square as the sole payment processor. The union hall already uses Square for in-person payments — running two payment ecosystems is operationally inefficient.

### Migration Phases (from ADR-018)

| Phase | Scope | Type | Hours Est. |
|-------|-------|------|------------|
| **A** | Replace Stripe → Square online payments | **Migration** (direct swap) | 15-20 |
| B | Square Terminal/POS at the hall | New feature | 10-15 |
| C | Square Invoices for dues billing | New feature | 10-15 |

**Only Phase A is covered by this handoff.** Phases B and C are separate future handoffs — they deliver capabilities that don't exist today and should be scoped independently.

---

## What the Spoke Needs to Know

### Architecture (from ADR-018)

- **Same PCI posture:** SAQ-A. Card data never touches our servers. Square Web Payments SDK tokenizes client-side, server receives a nonce.
- **Same service layer pattern:** `SquarePaymentService` replaces `StripePaymentService` with the same interface (create/get/refund/list payments, verify webhook).
- **Database change:** `stripe_payment_id` column needs renaming. Hub recommends processor-agnostic naming (`processor_payment_id` + `payment_processor` column) but Spoke should assess what makes sense given current codebase references.
- **Existing Stripe records are audit data.** 7-year NLRA retention. Archive, never delete.

### Key Square API Patterns

- Python SDK: `squareup` package (replaces `stripe`)
- Frontend SDK: `https://sandbox.web.squarecdn.com/v1/square.js` (sandbox) / `https://web.squarecdn.com/v1/square.js` (production)
- Payment creation uses a `source_id` (nonce from frontend tokenization)
- All payments require an `idempotency_key` (UUID)
- Amounts are in integer cents with explicit currency
- Webhook verification via `square.utilities.webhooks_helper.is_valid_webhook_event_signature`
- Sandbox test nonce: `cnon:card-nonce-ok`

### Environment Variables (New)
```
SQUARE_ENVIRONMENT=sandbox|production
SQUARE_APPLICATION_ID=xxx
SQUARE_ACCESS_TOKEN=xxx
SQUARE_LOCATION_ID=xxx
SQUARE_WEBHOOK_SIGNATURE_KEY=xxx
```

Sandbox credentials are in the user's `.env` — never in documentation or code.

### Files to Remove (Stripe)
- Stripe service file
- Stripe webhook router
- Stripe test files (already skip-marked per immediate test cleanup handoff)
- Stripe.js references in templates
- `stripe` from requirements

### Files to Create (Square)
- `src/services/square_payment_service.py`
- `src/routers/square_webhook.py`
- `src/tests/test_square_integration.py`
- `src/tests/test_square_frontend.py`
- Updated payment Jinja2 templates with Square Web Payments SDK

---

## What the Spoke Should Do With This Handoff

When the user says "begin Square migration":

1. **Read ADR-018** (`docs/decisions/ADR-018-square-payment-integration.md`) for full architectural context
2. **Examine the existing Stripe implementation** — the Spoke has codebase access the Hub doesn't. Understand the current service interface, router patterns, template structure, and test patterns before writing instructions.
3. **Generate a Claude Code instruction document** that accounts for the actual codebase state — file paths, import patterns, existing test fixtures, template inheritance, etc.
4. **Phase the work into 3-4 Claude Code sessions** (backend service → DB migration + frontend → tests + cleanup → documentation)
5. **Include a verification checklist** to confirm complete Stripe removal

---

## Scope Boundaries for Spoke

**Phase A includes:**
- Stripe → Square SDK swap (backend)
- Payment form frontend update (Stripe.js → Square Web Payments SDK)
- Database migration for payment ID column
- Webhook handler replacement
- Complete test coverage for Square
- Complete removal of all Stripe code
- Documentation updates (CLAUDE.md, ADRs, README)

**Phase A does NOT include:**
- Square Terminal/POS (Phase B)
- Square Invoices (Phase C)
- Changes to dues calculation logic
- Changes to member portal beyond payment SDK swap
- Production credential setup (user handles this)

---

**This handoff will be delivered to Spoke 1 when it is created, or directly to Claude Code if the user prefers. The user decides the timing.**
