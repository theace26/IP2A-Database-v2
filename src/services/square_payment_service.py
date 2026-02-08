"""
Square Payment Service — Phase 8A (ADR-018)
Handles online payment processing via Square Web Payments SDK.
Card data NEVER touches UnionCore servers — tokenized client-side.

Spoke Owner: Spoke 1 (Core Platform)
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session
from square.client import Square as SquareClient

from src.config.settings import settings
from src.models.dues_payment import DuesPayment
from src.services import audit_service

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
    ) -> Dict[str, Any]:
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

                # Update DuesPayment record with Square payment ID
                self._update_dues_payment(
                    dues_payment_id=dues_payment_id,
                    square_payment_id=square_payment_id,
                    status="paid",
                )

                # AUDIT TRAIL — MANDATORY for all payment attempts
                self._log_payment_audit(
                    member_id=member_id,
                    dues_payment_id=dues_payment_id,
                    square_payment_id=square_payment_id,
                    amount_cents=amount_cents,
                    status="COMPLETED",
                    detail=description,
                )

                logger.info(
                    "Payment processed: member=%s amount=%s square_id=%s",
                    member_id,
                    amount_cents,
                    square_payment_id,
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
                    member_id,
                    amount_cents,
                    error_msg,
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

    def get_payment_status(self, square_payment_id: str) -> Dict[str, Any]:
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
    ) -> Dict[str, Any]:
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

                # Resolve member_id and dues_payment_id from reference_number
                payment_record = (
                    self.db.query(DuesPayment)
                    .filter(DuesPayment.reference_number == square_payment_id)
                    .first()
                )

                self._log_payment_audit(
                    member_id=payment_record.member_id if payment_record else None,
                    dues_payment_id=payment_record.id if payment_record else None,
                    square_payment_id=square_payment_id,
                    amount_cents=amount_cents,
                    status="REFUNDED",
                    detail=f"Refund by user {requested_by_user_id}: {reason}",
                )

                logger.info(
                    "Refund processed: square_payment=%s refund=%s amount=%s",
                    square_payment_id,
                    refund_id,
                    amount_cents,
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

        Uses the existing audit_service pattern for dues_payments table.
        """
        if dues_payment_id:
            # For creates/updates, use the standard audit service
            audit_service.log_update(
                db=self.db,
                table_name="dues_payments",
                record_id=dues_payment_id,
                old_values={},
                new_values={
                    "square_payment_id": square_payment_id,
                    "amount_cents": amount_cents,
                    "status": status,
                },
                changed_by="square_payment_service",
                notes=f"Payment {status}: {detail}",
            )
        else:
            # For operations without a dues_payment_id (e.g., webhook events)
            logger.info(
                "AUDIT: payment %s | member=%s | square=%s | amount=%s | %s",
                status,
                member_id,
                square_payment_id,
                amount_cents,
                detail,
            )

    def _update_dues_payment(
        self,
        dues_payment_id: int,
        square_payment_id: str,
        status: str,
    ):
        """
        Update DuesPayment record with Square payment reference.

        Uses the existing reference_number field to store the Square payment ID.
        """
        from src.db.enums import DuesPaymentStatus

        payment = self.db.query(DuesPayment).filter(DuesPayment.id == dues_payment_id).first()
        if payment:
            payment.reference_number = square_payment_id
            payment.status = DuesPaymentStatus.PAID if status == "paid" else payment.status
            payment.payment_date = datetime.now(timezone.utc).date()
            self.db.commit()
            self.db.refresh(payment)
