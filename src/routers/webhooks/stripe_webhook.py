"""Stripe webhook handler for payment events."""
import logging
from decimal import Decimal

import stripe
from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.enums import DuesPaymentStatus
from src.services.payment_service import PaymentService
from src.services import dues_payment_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    """
    Handle Stripe webhook events.

    This endpoint receives webhook events from Stripe when payment-related
    actions occur (checkout completed, payment failed, refunds, etc.).

    IMPORTANT:
    - This endpoint has NO authentication (Stripe calls it directly)
    - Security is provided by webhook signature verification
    - Never trust redirect URLs alone - always verify via webhook

    Supported Events:
    - checkout.session.completed: Payment succeeded
    - checkout.session.expired: Session timed out
    - payment_intent.succeeded: Payment confirmed
    - payment_intent.payment_failed: Payment failed
    - charge.refunded: Refund processed

    Args:
        request: FastAPI request object (for raw body access)
        stripe_signature: Stripe-Signature header value

    Returns:
        Success response with status "received"

    Raises:
        HTTPException 400: Invalid payload or signature verification failed
    """
    if not stripe_signature:
        logger.warning("Stripe webhook called without Stripe-Signature header")
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    # Get raw request body for signature verification
    payload = await request.body()

    # Verify webhook signature and construct event
    try:
        event = PaymentService.construct_webhook_event(payload, stripe_signature)
    except ValueError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Log the event type
    logger.info(f"Received Stripe webhook event: {event['type']} (ID: {event['id']})")

    # Get database session
    db: Session = next(get_db())

    try:
        # Handle different event types
        if event["type"] == "checkout.session.completed":
            await handle_checkout_session_completed(db, event)
        elif event["type"] == "checkout.session.expired":
            await handle_checkout_session_expired(db, event)
        elif event["type"] == "payment_intent.succeeded":
            await handle_payment_intent_succeeded(db, event)
        elif event["type"] == "payment_intent.payment_failed":
            await handle_payment_intent_failed(db, event)
        elif event["type"] == "charge.refunded":
            await handle_charge_refunded(db, event)
        else:
            logger.info(f"Unhandled webhook event type: {event['type']}")

        return {"status": "received"}

    except Exception as e:
        logger.error(f"Error processing webhook event {event['type']}: {e}", exc_info=True)
        # Return 200 anyway to prevent Stripe from retrying
        # (we log the error for investigation)
        return {"status": "error", "message": str(e)}

    finally:
        db.close()


async def handle_checkout_session_completed(db: Session, event: stripe.Event):
    """
    Handle successful checkout session completion.

    This is the primary event for recording successful payments.

    Args:
        db: Database session
        event: Stripe event object
    """
    session = event["data"]["object"]
    session_id = session["id"]
    member_id = int(session["metadata"]["member_id"])
    period_id = int(session["metadata"]["period_id"])
    payment_type = session["metadata"].get("payment_type", "dues")

    # Convert amount from cents to dollars
    amount_paid = Decimal(session["amount_total"]) / 100

    # Get payment method type
    payment_method_types = session.get("payment_method_types", [])
    payment_method = payment_method_types[0] if payment_method_types else "unknown"

    # Map Stripe payment method to our enum
    if payment_method == "card":
        payment_method_db = "stripe_card"
    elif payment_method == "us_bank_account":
        payment_method_db = "stripe_ach"
    else:
        payment_method_db = "stripe_other"

    # Save Stripe customer ID if this is a new customer
    customer_id = session.get("customer")
    if customer_id:
        try:
            PaymentService.save_stripe_customer_id(db, member_id, customer_id)
        except Exception as e:
            logger.error(f"Failed to save Stripe customer ID: {e}")

    # Record the payment in our database
    try:
        # Create payment record
        from src.schemas.dues_payment import DuesPaymentCreate

        payment_data = DuesPaymentCreate(
            member_id=member_id,
            period_id=period_id,
            amount=amount_paid,
            payment_method=payment_method_db,
            status=DuesPaymentStatus.PAID,
            notes=f"Stripe Checkout Session: {session_id}",
        )

        payment = dues_payment_service.create_payment(db, payment_data)

        logger.info(
            f"Recorded payment ID {payment.id} for member {member_id}, "
            f"period {period_id}, amount ${amount_paid}, "
            f"Stripe session {session_id}"
        )

    except Exception as e:
        logger.error(
            f"Failed to record payment for Stripe session {session_id}: {e}",
            exc_info=True,
        )
        raise


async def handle_checkout_session_expired(db: Session, event: stripe.Event):
    """
    Handle expired checkout session.

    Checkout sessions expire after 24 hours if unpaid.

    Args:
        db: Database session
        event: Stripe event object
    """
    session = event["data"]["object"]
    session_id = session["id"]
    member_id = session["metadata"].get("member_id")

    logger.info(f"Checkout session {session_id} expired for member {member_id}")
    # No action needed - member can create a new payment session


async def handle_payment_intent_succeeded(db: Session, event: stripe.Event):
    """
    Handle successful payment intent.

    This is a backup confirmation event that fires after checkout.session.completed.

    Args:
        db: Database session
        event: Stripe event object
    """
    payment_intent = event["data"]["object"]
    payment_intent_id = payment_intent["id"]

    logger.info(f"Payment intent {payment_intent_id} succeeded")
    # Payment already recorded in checkout.session.completed


async def handle_payment_intent_failed(db: Session, event: stripe.Event):
    """
    Handle failed payment intent.

    Args:
        db: Database session
        event: Stripe event object
    """
    payment_intent = event["data"]["object"]
    payment_intent_id = payment_intent["id"]
    failure_message = payment_intent.get("last_payment_error", {}).get("message", "Unknown error")

    logger.warning(f"Payment intent {payment_intent_id} failed: {failure_message}")
    # No action needed - member can retry payment


async def handle_charge_refunded(db: Session, event: stripe.Event):
    """
    Handle refunded charge.

    Args:
        db: Database session
        event: Stripe event object
    """
    charge = event["data"]["object"]
    charge_id = charge["id"]
    amount_refunded = Decimal(charge["amount_refunded"]) / 100

    logger.info(f"Charge {charge_id} refunded: ${amount_refunded}")

    # TODO: Create a dues adjustment record for the refund
    # For now, just log it - manual adjustment may be needed
