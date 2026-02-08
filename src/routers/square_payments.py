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
from src.routers.dependencies.auth_cookie import require_auth

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
    current_user: dict = Depends(require_auth),
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
    current_user: dict = Depends(require_auth),
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
    current_user: dict = Depends(require_auth),
):
    """
    Process a refund. Requires Officer role or higher.

    Note: Role-based authorization should be enforced via middleware or dependency.
    For now, any authenticated user can refund (to be restricted in production).
    """
    service = SquarePaymentService(db)
    idempotency_key = str(uuid.uuid4())

    # Extract user ID from current_user dict
    user_id = current_user.get("id", 0) if isinstance(current_user, dict) else 0

    result = service.process_refund(
        square_payment_id=square_payment_id,
        amount_cents=request.amount_cents,
        reason=request.reason,
        requested_by_user_id=user_id,
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
        # Update DuesPayment status if needed (future enhancement)

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
