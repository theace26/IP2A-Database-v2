"""Service for Stripe payment processing."""
import logging
from decimal import Decimal
from typing import Optional

import stripe
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.models.member import Member

logger = logging.getLogger(__name__)

# Initialize Stripe with API key if configured
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY
else:
    logger.warning("STRIPE_SECRET_KEY not configured - Stripe integration disabled")


class PaymentService:
    """Service for handling Stripe payment operations."""

    @staticmethod
    def create_dues_checkout_session(
        db: Session,
        member_id: int,
        amount: Decimal,
        period_id: int,
        description: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """
        Create a Stripe Checkout Session for dues payment.

        Args:
            db: Database session
            member_id: ID of the member making payment
            amount: Payment amount in dollars (will be converted to cents)
            period_id: ID of the dues period being paid
            description: Payment description (e.g., "Monthly Dues - January 2026")
            success_url: URL to redirect to after successful payment
            cancel_url: URL to redirect to if payment is cancelled

        Returns:
            Stripe Checkout Session URL for redirect

        Raises:
            ValueError: If Stripe is not configured or member not found
            stripe.error.StripeError: If Stripe API call fails
        """
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("Stripe integration not configured - missing STRIPE_SECRET_KEY")

        # Get member for metadata and customer lookup
        member = db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise ValueError(f"Member {member_id} not found")

        # Convert amount to cents (Stripe expects integer cents)
        amount_cents = int(amount * 100)

        # Prepare session parameters
        session_params = {
            "payment_method_types": ["card", "us_bank_account"],
            "line_items": [
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount_cents,
                        "product_data": {
                            "name": description,
                            "description": f"IBEW Local 46 - Member #{member_id}",
                        },
                    },
                    "quantity": 1,
                }
            ],
            "mode": "payment",
            "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": cancel_url,
            "metadata": {
                "member_id": str(member_id),
                "period_id": str(period_id),
                "payment_type": "dues",
            },
            "billing_address_collection": "required",
            "customer_email": member.email if hasattr(member, "email") and member.email else None,
        }

        # If member already has a Stripe customer ID, associate it
        if member.stripe_customer_id:
            session_params["customer"] = member.stripe_customer_id
        else:
            # Customer will be created automatically, we'll save it from webhook
            pass

        # Create the Checkout Session
        try:
            session = stripe.checkout.Session.create(**session_params)
            logger.info(
                f"Created Stripe Checkout Session {session.id} for member {member_id}, "
                f"amount ${amount}, period {period_id}"
            )
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API error creating checkout session: {e}")
            raise

    @staticmethod
    def retrieve_checkout_session(session_id: str) -> stripe.checkout.Session:
        """
        Retrieve a Checkout Session from Stripe.

        Args:
            session_id: Stripe Checkout Session ID

        Returns:
            Stripe Checkout Session object

        Raises:
            ValueError: If Stripe is not configured
            stripe.error.StripeError: If Stripe API call fails
        """
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("Stripe integration not configured")

        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API error retrieving session {session_id}: {e}")
            raise

    @staticmethod
    def save_stripe_customer_id(
        db: Session,
        member_id: int,
        stripe_customer_id: str,
    ) -> None:
        """
        Save Stripe customer ID to member record.

        Args:
            db: Database session
            member_id: ID of the member
            stripe_customer_id: Stripe customer ID to save

        Raises:
            ValueError: If member not found
        """
        member = db.query(Member).filter(Member.id == member_id).first()
        if not member:
            raise ValueError(f"Member {member_id} not found")

        member.stripe_customer_id = stripe_customer_id
        db.commit()
        logger.info(f"Saved Stripe customer ID {stripe_customer_id} for member {member_id}")

    @staticmethod
    def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
        """
        Construct and verify a Stripe webhook event.

        Args:
            payload: Raw request body bytes
            sig_header: Stripe-Signature header value

        Returns:
            Verified Stripe Event object

        Raises:
            ValueError: If webhook secret is not configured or signature is invalid
        """
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise ValueError("Stripe webhook secret not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise ValueError("Invalid signature")
