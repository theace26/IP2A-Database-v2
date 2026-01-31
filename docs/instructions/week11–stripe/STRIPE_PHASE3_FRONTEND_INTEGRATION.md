# Stripe Integration Phase 3: Frontend Payment Flow

**Project:** UnionCore (IP2A Database v2)
**Phase:** Stripe Integration - Phase 3 of 3
**Estimated Duration:** 2.5-3 hours
**Branch:** `develop` (ALWAYS work on develop, main is frozen for Railway demo)
**Prerequisite:** Stripe Phase 2 complete (Database migrations + Local testing)

---

## Session Overview

This session implements the user-facing payment flow in the dues frontend. Members will be able to click "Pay Dues" and complete payment through Stripe's hosted checkout page.

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

# 4. Verify Phase 2 complete
# - stripe_customer_id column exists in members table
# - DuesPaymentMethod enum includes stripe_card, stripe_ach
# - Stripe CLI webhook forwarding tested

# 5. Start Stripe CLI (separate terminal)
stripe listen --forward-to localhost:8000/webhooks/stripe
```

---

## Tasks

### Task 1: Create Payment Initiation Endpoint (30 min)

**Goal:** Backend endpoint that creates Stripe Checkout Session and returns redirect URL.

#### 1.1 Add Route to Dues Frontend Router

**File:** `src/routers/dues_frontend.py`

Add new endpoint:

```python
from fastapi import Request
from fastapi.responses import RedirectResponse
from src.services.payment_service import PaymentService
from src.services.dues_period_service import dues_period_service
from src.services.member_service import member_service


@router.post("/payments/initiate/{member_id}/{period_id}")
async def initiate_payment(
    request: Request,
    member_id: int,
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie)
):
    """
    Initiate Stripe Checkout Session for dues payment.
    Redirects user to Stripe's hosted payment page.
    """
    # Get member and period
    member = member_service.get_by_id(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    period = dues_period_service.get_by_id(db, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
    
    # Get member's rate for this classification
    rate = dues_frontend_service.get_rate_for_member(db, member_id)
    if not rate:
        raise HTTPException(status_code=400, detail="No active rate found for member classification")
    
    # Calculate amount due (could be customized for partial payments later)
    amount = rate.monthly_amount
    
    # Build URLs
    base_url = str(request.base_url).rstrip('/')
    success_url = f"{base_url}/dues/payments/success"
    cancel_url = f"{base_url}/dues/payments/cancel"
    
    # Create Checkout Session
    try:
        checkout_url = await PaymentService.create_dues_checkout_session(
            member_id=member_id,
            period_id=period_id,
            amount=amount,
            description=f"IBEW Local 46 Dues - {period.period_name}",
            success_url=success_url,
            cancel_url=cancel_url,
            member_email=member.email if hasattr(member, 'email') else None
        )
        
        # Redirect to Stripe Checkout
        return RedirectResponse(url=checkout_url, status_code=303)
        
    except Exception as e:
        # Log error and show user-friendly message
        import logging
        logging.error(f"Stripe checkout creation failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Unable to initiate payment. Please try again later."
        )
```

#### 1.2 Add Rate Lookup to DuesFrontendService

**File:** `src/services/dues_frontend_service.py`

```python
def get_rate_for_member(self, db: Session, member_id: int) -> Optional[DuesRate]:
    """Get the active dues rate for a member's classification."""
    from src.services.member_service import member_service
    from src.services.dues_rate_service import dues_rate_service
    from datetime import date
    
    member = member_service.get_by_id(db, member_id)
    if not member:
        return None
    
    # Get active rate for member's classification
    rates = dues_rate_service.get_by_classification(db, member.classification)
    today = date.today()
    
    for rate in rates:
        if rate.effective_date <= today:
            if rate.end_date is None or rate.end_date >= today:
                return rate
    
    return None
```

---

### Task 2: Create Success Page (30 min)

**Goal:** Page shown after successful payment, confirming the transaction.

#### 2.1 Add Success Route

**File:** `src/routers/dues_frontend.py`

```python
@router.get("/payments/success")
async def payment_success(
    request: Request,
    session_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie)
):
    """
    Payment success page. Shown after Stripe checkout completes.
    The webhook will have already processed the payment by now.
    """
    payment_info = None
    
    if session_id:
        # Optionally retrieve session details from Stripe
        try:
            session = PaymentService.retrieve_checkout_session(session_id)
            if session:
                payment_info = {
                    "amount": session.get("amount_total", 0) / 100,
                    "member_id": session.get("metadata", {}).get("member_id"),
                    "period_id": session.get("metadata", {}).get("period_id"),
                    "payment_status": session.get("payment_status"),
                }
        except Exception:
            pass  # Session retrieval is optional
    
    return templates.TemplateResponse(
        "dues/payments/success.html",
        {
            "request": request,
            "current_user": current_user,
            "payment_info": payment_info,
            "page_title": "Payment Successful",
        }
    )
```

#### 2.2 Create Success Template

**File:** `src/templates/dues/payments/success.html`

```html
{% extends "base_auth.html" %}

{% block title %}Payment Successful - Dues{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto">
    <!-- Success Card -->
    <div class="card bg-base-100 shadow-xl">
        <div class="card-body items-center text-center">
            <!-- Success Icon -->
            <div class="text-success mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-24 w-24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
            
            <h1 class="card-title text-3xl text-success">Payment Successful!</h1>
            
            <p class="text-lg mt-2">
                Thank you for your dues payment. Your transaction has been processed successfully.
            </p>
            
            {% if payment_info %}
            <div class="stats stats-vertical lg:stats-horizontal shadow mt-6">
                <div class="stat">
                    <div class="stat-title">Amount Paid</div>
                    <div class="stat-value text-primary">${{ "%.2f"|format(payment_info.amount) }}</div>
                </div>
                <div class="stat">
                    <div class="stat-title">Status</div>
                    <div class="stat-value text-success text-lg">{{ payment_info.payment_status|title }}</div>
                </div>
            </div>
            {% endif %}
            
            <div class="alert alert-info mt-6">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span>A receipt has been sent to your email address. You can also view your payment history in the Dues section.</span>
            </div>
            
            <div class="card-actions mt-6">
                <a href="/dues/payments" class="btn btn-primary">
                    View Payment History
                </a>
                <a href="/dues" class="btn btn-ghost">
                    Back to Dues Overview
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

### Task 3: Create Cancel Page (20 min)

**Goal:** Page shown when user cancels checkout, allowing retry.

#### 3.1 Add Cancel Route

**File:** `src/routers/dues_frontend.py`

```python
@router.get("/payments/cancel")
async def payment_cancel(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_cookie)
):
    """
    Payment cancelled page. Shown when user cancels Stripe checkout.
    """
    return templates.TemplateResponse(
        "dues/payments/cancel.html",
        {
            "request": request,
            "current_user": current_user,
            "page_title": "Payment Cancelled",
        }
    )
```

#### 3.2 Create Cancel Template

**File:** `src/templates/dues/payments/cancel.html`

```html
{% extends "base_auth.html" %}

{% block title %}Payment Cancelled - Dues{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto">
    <!-- Cancel Card -->
    <div class="card bg-base-100 shadow-xl">
        <div class="card-body items-center text-center">
            <!-- Cancel Icon -->
            <div class="text-warning mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-24 w-24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
            </div>
            
            <h1 class="card-title text-3xl">Payment Cancelled</h1>
            
            <p class="text-lg mt-2">
                Your payment was not completed. No charges have been made to your account.
            </p>
            
            <div class="alert mt-6">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span>If you experienced any issues or have questions about paying your dues, please contact the union office.</span>
            </div>
            
            <div class="card-actions mt-6">
                <a href="/dues" class="btn btn-primary">
                    Return to Dues
                </a>
                <a href="/dashboard" class="btn btn-ghost">
                    Go to Dashboard
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

### Task 4: Add "Pay Dues" Button to UI (45 min)

**Goal:** Add payment initiation button to relevant dues pages.

#### 4.1 Update Member Payment History Page

**File:** `src/templates/dues/payments/member.html`

Add payment button in the header area:

```html
<!-- Add to the card-actions or header section -->
{% if outstanding_balance > 0 and current_period %}
<div class="alert alert-warning mb-4">
    <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
    <div class="flex-1">
        <h3 class="font-bold">Outstanding Balance: ${{ "%.2f"|format(outstanding_balance) }}</h3>
        <p class="text-sm">Payment due for {{ current_period.period_name }}</p>
    </div>
    <form action="/dues/payments/initiate/{{ member.id }}/{{ current_period.id }}" method="POST">
        <button type="submit" class="btn btn-primary">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
            Pay Now
        </button>
    </form>
</div>
{% endif %}
```

#### 4.2 Add Pay Button to Period Detail Page

**File:** `src/templates/dues/periods/detail.html`

Add in the overdue members section:

```html
<!-- In the table or list of members with outstanding payments -->
<td class="text-right">
    {% if member.balance_due > 0 %}
    <form action="/dues/payments/initiate/{{ member.id }}/{{ period.id }}" method="POST" class="inline">
        <button type="submit" class="btn btn-sm btn-primary">
            Pay ${{ "%.2f"|format(member.balance_due) }}
        </button>
    </form>
    {% else %}
    <span class="badge badge-success">Paid</span>
    {% endif %}
</td>
```

#### 4.3 Add Quick Pay Card to Dues Landing

**File:** `src/templates/dues/index.html`

Add a quick pay section:

```html
<!-- Quick Pay Section (for staff to help members pay) -->
<div class="card bg-base-100 shadow-xl mt-6">
    <div class="card-body">
        <h2 class="card-title">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
            Quick Pay
        </h2>
        <p class="text-sm text-gray-600">Help a member pay their dues online</p>
        
        <form action="/dues/payments/quick-pay" method="GET" class="mt-4">
            <div class="join w-full">
                <input 
                    type="text" 
                    name="member_search" 
                    placeholder="Search member by name or ID..."
                    class="input input-bordered join-item flex-1"
                />
                <button type="submit" class="btn btn-primary join-item">
                    Find Member
                </button>
            </div>
        </form>
    </div>
</div>
```

---

### Task 5: Add DuesFrontendService Updates (20 min)

**Goal:** Service methods to support payment UI.

**File:** `src/services/dues_frontend_service.py`

```python
def get_member_payment_summary(self, db: Session, member_id: int) -> dict:
    """Get payment summary for a member including outstanding balance."""
    from src.services.member_service import member_service
    from src.services.dues_period_service import dues_period_service
    from src.services.dues_payment_service import dues_payment_service
    
    member = member_service.get_by_id(db, member_id)
    if not member:
        return None
    
    # Get current period
    current_period = dues_period_service.get_current_period(db)
    
    # Get rate for member's classification
    rate = self.get_rate_for_member(db, member_id)
    
    # Calculate balance
    if rate and current_period:
        payments = dues_payment_service.get_by_member_and_period(
            db, member_id, current_period.id
        )
        total_paid = sum(p.amount for p in payments if p.status == 'completed')
        outstanding_balance = float(rate.monthly_amount) - float(total_paid)
    else:
        outstanding_balance = 0
    
    return {
        "member": member,
        "current_period": current_period,
        "rate": rate,
        "outstanding_balance": max(0, outstanding_balance),
        "can_pay_online": outstanding_balance > 0 and current_period is not None,
    }
```

---

### Task 6: Write Frontend Tests (30 min)

**Goal:** Test payment flow UI components.

**File:** `src/tests/test_stripe_frontend.py`

```python
"""Tests for Stripe payment frontend integration."""
import pytest
from unittest.mock import patch, MagicMock


class TestPaymentInitiation:
    """Tests for payment initiation endpoint."""

    def test_initiate_payment_requires_auth(self, client):
        """Test that payment initiation requires authentication."""
        response = client.post("/dues/payments/initiate/1/1")
        assert response.status_code in [401, 302]  # Redirect to login

    @patch('src.services.payment_service.PaymentService.create_dues_checkout_session')
    def test_initiate_payment_redirects_to_stripe(
        self, mock_create, client, auth_cookies
    ):
        """Test that valid payment request redirects to Stripe."""
        mock_create.return_value = "https://checkout.stripe.com/test_session"
        
        response = client.post(
            "/dues/payments/initiate/1/1",
            cookies=auth_cookies,
            follow_redirects=False
        )
        
        assert response.status_code == 303
        assert "checkout.stripe.com" in response.headers.get("location", "")

    def test_initiate_payment_invalid_member(self, client, auth_cookies):
        """Test payment initiation with invalid member ID."""
        response = client.post(
            "/dues/payments/initiate/99999/1",
            cookies=auth_cookies
        )
        assert response.status_code == 404


class TestPaymentSuccessPage:
    """Tests for payment success page."""

    def test_success_page_requires_auth(self, client):
        """Test that success page requires authentication."""
        response = client.get("/dues/payments/success")
        assert response.status_code in [401, 302]

    def test_success_page_renders(self, client, auth_cookies):
        """Test that success page renders correctly."""
        response = client.get(
            "/dues/payments/success",
            cookies=auth_cookies
        )
        assert response.status_code == 200
        assert b"Payment Successful" in response.content

    def test_success_page_with_session_id(self, client, auth_cookies):
        """Test success page with session ID parameter."""
        response = client.get(
            "/dues/payments/success?session_id=cs_test_123",
            cookies=auth_cookies
        )
        assert response.status_code == 200


class TestPaymentCancelPage:
    """Tests for payment cancel page."""

    def test_cancel_page_requires_auth(self, client):
        """Test that cancel page requires authentication."""
        response = client.get("/dues/payments/cancel")
        assert response.status_code in [401, 302]

    def test_cancel_page_renders(self, client, auth_cookies):
        """Test that cancel page renders correctly."""
        response = client.get(
            "/dues/payments/cancel",
            cookies=auth_cookies
        )
        assert response.status_code == 200
        assert b"Payment Cancelled" in response.content

    def test_cancel_page_shows_retry_option(self, client, auth_cookies):
        """Test that cancel page shows option to retry."""
        response = client.get(
            "/dues/payments/cancel",
            cookies=auth_cookies
        )
        assert response.status_code == 200
        assert b"Return to Dues" in response.content


class TestPayButtonDisplay:
    """Tests for Pay button visibility."""

    def test_pay_button_shown_for_outstanding_balance(self, client, auth_cookies):
        """Test that Pay button appears when member has balance due."""
        # This test would check the member payment page
        # Implementation depends on test fixtures and data setup
        pass

    def test_pay_button_hidden_when_paid(self, client, auth_cookies):
        """Test that Pay button is hidden when dues are current."""
        pass
```

Run tests:
```bash
pytest src/tests/test_stripe_frontend.py -v
```

---

## Acceptance Criteria

- [ ] Payment initiation endpoint creates Checkout Session and redirects
- [ ] Success page displays after completed payment
- [ ] Cancel page displays when user cancels checkout
- [ ] "Pay Dues" button appears on member payment history page
- [ ] "Pay Dues" button appears on period detail page (for overdue members)
- [ ] Payment amount calculated correctly from member's rate
- [ ] All frontend tests pass
- [ ] Full end-to-end payment flow works (start to finish)

---

## Files Created/Modified

### Created
```
src/templates/dues/payments/success.html
src/templates/dues/payments/cancel.html
src/tests/test_stripe_frontend.py
```

### Modified
```
src/routers/dues_frontend.py           # Added payment routes
src/services/dues_frontend_service.py  # Added rate lookup, payment summary
src/templates/dues/payments/member.html  # Added Pay button
src/templates/dues/periods/detail.html   # Added Pay button
src/templates/dues/index.html            # Added Quick Pay section
```

---

## End-to-End Test Flow

1. Navigate to `/dues`
2. Click into a member's payment history
3. If balance due, click "Pay Now"
4. Complete checkout on Stripe page with test card `4242 4242 4242 4242`
5. Verify redirect to success page
6. Check database for DuesPayment record
7. Verify payment appears in member's history

---

## Production Deployment Notes

Before deploying to Railway:

1. **Set Stripe environment variables:**
   ```bash
   STRIPE_SECRET_KEY=sk_live_xxxxx
   STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
   STRIPE_WEBHOOK_SECRET=whsec_xxxxx
   ```

2. **Configure webhook in Stripe Dashboard:**
   - URL: `https://your-railway-domain.com/webhooks/stripe`
   - Events: checkout.session.completed, checkout.session.expired, etc.

3. **Test with Stripe test mode first** before switching to live keys

---

## Next Session Preview

**Week 11: Audit Trail & Member History UI** will add:
- Immutability trigger on audit_logs table
- member_notes table and service
- Audit log viewer UI with role-based filtering
- Inline history on member detail pages

---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** 

### Before Ending This Session:

Scan all documentation in `/app/*`. Update *ANY* & *ALL* relevant documentation as necessary with current progress for the historical record. Do not forget to update ADRs, Roadmap, Checklist, again only if necessary.

**Documentation Checklist:**

| Document | Updated? | Notes |
|----------|----------|-------|
| CLAUDE.md | [ ] | Update Stripe Phase 3 status = COMPLETE |
| CHANGELOG.md | [ ] | Add Stripe frontend integration entry |
| CONTINUITY.md | [ ] | Update current status |
| IP2A_MILESTONE_CHECKLIST.md | [ ] | Mark Stripe integration complete |
| IP2A_BACKEND_ROADMAP.md | [ ] | Update if needed |
| ADR-013 | [ ] | Mark implementation complete |
| Session log created | [ ] | `docs/reports/session-logs/` |

This ensures historical record-keeping and project continuity ("bus factor" protection).

---

*End of instruction document*
