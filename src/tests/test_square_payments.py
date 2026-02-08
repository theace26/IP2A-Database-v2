"""
Tests for Square Payment Integration — Phase 8A (ADR-018)

CRITICAL: All Square API calls MUST be mocked. Tests should NEVER hit
Square's sandbox API. We test our code, not Square's API.

Spoke Owner: Spoke 1 (Core Platform)
"""
import json
import uuid
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from src.services.square_payment_service import SquarePaymentService


# ============================================================
# SERVICE TESTS
# ============================================================

class TestSquarePaymentService:
    """Tests for SquarePaymentService methods."""

    @patch("src.services.square_payment_service.SquareClient")
    def test_create_payment_success(self, mock_client_class, db):
        """Successful payment returns payment_id."""
        # Mock Square API response
        mock_result = MagicMock()
        mock_result.is_success.return_value = True
        mock_result.body = {
            "payment": {
                "id": "sq_payment_123",
                "status": "COMPLETED",
            }
        }
        mock_client = MagicMock()
        mock_client.payments.create_payment.return_value = mock_result
        mock_client_class.return_value = mock_client

        service = SquarePaymentService(db)

        result = service.create_payment(
            nonce="cnon:card-nonce-ok",
            amount_cents=5000,
            member_id=1,
            dues_payment_id=1,
            description="January 2026 Dues",
            idempotency_key=str(uuid.uuid4()),
        )

        assert result["success"] is True
        assert result["payment_id"] == "sq_payment_123"
        assert result["error"] is None

    @patch("src.services.square_payment_service.SquareClient")
    def test_create_payment_failure(self, mock_client_class, db):
        """Failed payment returns error message."""
        mock_result = MagicMock()
        mock_result.is_success.return_value = False
        mock_result.is_error.return_value = True
        mock_result.errors = [
            {"category": "PAYMENT_METHOD_ERROR", "detail": "Card declined"}
        ]
        mock_client = MagicMock()
        mock_client.payments.create_payment.return_value = mock_result
        mock_client_class.return_value = mock_client

        service = SquarePaymentService(db)

        result = service.create_payment(
            nonce="cnon:card-nonce-declined",
            amount_cents=5000,
            member_id=1,
            dues_payment_id=1,
            description="Test",
            idempotency_key=str(uuid.uuid4()),
        )

        assert result["success"] is False
        assert "Card declined" in result["error"]

    @patch("src.services.square_payment_service.SquareClient")
    def test_create_payment_exception(self, mock_client_class, db):
        """Exception during payment returns error gracefully."""
        mock_client = MagicMock()
        mock_client.payments.create_payment.side_effect = Exception("Network error")
        mock_client_class.return_value = mock_client

        service = SquarePaymentService(db)

        result = service.create_payment(
            nonce="test",
            amount_cents=5000,
            member_id=1,
            dues_payment_id=1,
            description="Test",
            idempotency_key=str(uuid.uuid4()),
        )

        assert result["success"] is False
        assert "Network error" in result["error"]

    @patch("src.services.square_payment_service.SquareClient")
    def test_get_payment_status_success(self, mock_client_class, db):
        """Can retrieve payment status from Square."""
        mock_result = MagicMock()
        mock_result.is_success.return_value = True
        mock_result.body = {
            "payment": {
                "id": "sq_payment_123",
                "status": "COMPLETED",
                "amount_money": {"amount": 5000, "currency": "USD"},
                "created_at": "2026-02-08T12:00:00Z",
            }
        }
        mock_client = MagicMock()
        mock_client.payments.get_payment.return_value = mock_result
        mock_client_class.return_value = mock_client

        service = SquarePaymentService(db)

        result = service.get_payment_status("sq_payment_123")

        assert result["success"] is True
        assert result["status"] == "COMPLETED"
        assert result["amount_cents"] == 5000

    @patch("src.services.square_payment_service.SquareClient")
    def test_get_payment_status_failure(self, mock_client_class, db):
        """Failed status query returns error."""
        mock_result = MagicMock()
        mock_result.is_success.return_value = False
        mock_result.errors = [{"detail": "Payment not found"}]
        mock_client = MagicMock()
        mock_client.payments.get_payment.return_value = mock_result
        mock_client_class.return_value = mock_client

        service = SquarePaymentService(db)

        result = service.get_payment_status("invalid_id")

        assert result["success"] is False

    @patch("src.services.square_payment_service.SquareClient")
    def test_process_refund_success(self, mock_client_class, db):
        """Successful refund returns refund_id."""
        mock_result = MagicMock()
        mock_result.is_success.return_value = True
        mock_result.body = {"refund": {"id": "sq_refund_456"}}
        mock_client = MagicMock()
        mock_client.refunds.refund_payment.return_value = mock_result
        mock_client_class.return_value = mock_client

        service = SquarePaymentService(db)

        result = service.process_refund(
            square_payment_id="sq_payment_123",
            amount_cents=5000,
            reason="Overpayment",
            requested_by_user_id=1,
            idempotency_key=str(uuid.uuid4()),
        )

        assert result["success"] is True
        assert result["refund_id"] == "sq_refund_456"

    @patch("src.services.square_payment_service.SquareClient")
    def test_process_refund_failure(self, mock_client_class, db):
        """Failed refund returns error."""
        mock_result = MagicMock()
        mock_result.is_success.return_value = False
        mock_result.errors = [{"detail": "Already refunded"}]
        mock_client = MagicMock()
        mock_client.refunds.refund_payment.return_value = mock_result
        mock_client_class.return_value = mock_client

        service = SquarePaymentService(db)

        result = service.process_refund(
            square_payment_id="sq_payment_123",
            amount_cents=5000,
            reason="Test",
            requested_by_user_id=1,
            idempotency_key=str(uuid.uuid4()),
        )

        assert result["success"] is False
        assert "Already refunded" in str(result["error"])


# ============================================================
# API ROUTER TESTS
# ============================================================

class TestSquarePaymentRouter:
    """Tests for payment API endpoints."""

    def test_process_payment_endpoint_success(self, client, test_user, mocker):
        """POST /api/v1/payments/process returns payment_id on success."""
        # Mock the service
        mock_service = mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        )
        mock_service.return_value.create_payment.return_value = {
            "success": True,
            "payment_id": "sq_pay_123",
            "error": None,
        }

        response = client.post(
            "/api/v1/payments/process",
            json={
                "nonce": "cnon:card-nonce-ok",
                "amount_cents": 5000,
                "member_id": 1,
                "dues_payment_id": 1,
                "description": "Test payment",
            },
        )

        assert response.status_code == 200
        assert response.json()["payment_id"] == "sq_pay_123"

    def test_process_payment_endpoint_failure(self, client, test_user, mocker):
        """POST /api/v1/payments/process returns 400 on failure."""
        mock_service = mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        )
        mock_service.return_value.create_payment.return_value = {
            "success": False,
            "payment_id": None,
            "error": "Card declined",
        }

        response = client.post(
            "/api/v1/payments/process",
            json={
                "nonce": "bad-nonce",
                "amount_cents": 5000,
                "member_id": 1,
                "dues_payment_id": 1,
                "description": "Test",
            },
        )

        assert response.status_code == 400
        assert "Card declined" in response.json()["detail"]

    def test_payment_status_endpoint(self, client, test_user, mocker):
        """GET /api/v1/payments/{id} returns payment status."""
        mock_service = mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        )
        mock_service.return_value.get_payment_status.return_value = {
            "success": True,
            "status": "COMPLETED",
            "amount_cents": 5000,
        }

        response = client.get("/api/v1/payments/sq_pay_123")

        assert response.status_code == 200
        assert response.json()["status"] == "COMPLETED"

    def test_refund_endpoint(self, client, test_user, mocker):
        """POST /api/v1/payments/{id}/refund processes refund."""
        mock_service = mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        )
        mock_service.return_value.process_refund.return_value = {
            "success": True,
            "refund_id": "sq_refund_789",
            "error": None,
        }

        response = client.post(
            "/api/v1/payments/sq_pay_123/refund",
            json={
                "amount_cents": 2500,
                "reason": "Partial refund",
            },
        )

        assert response.status_code == 200
        assert response.json()["refund_id"] == "sq_refund_789"


# ============================================================
# WEBHOOK TESTS
# ============================================================

class TestSquareWebhook:
    """Tests for Square webhook handler."""

    def test_webhook_valid_signature(self, client, mocker):
        """Webhook with valid signature returns 200."""
        mock_service = mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        )
        mock_service.return_value.verify_webhook.return_value = True

        event = {
            "type": "payment.completed",
            "data": {"object": {"payment": {"id": "sq_pay_123"}}},
        }

        response = client.post(
            "/api/v1/payments/webhooks/square",
            content=json.dumps(event),
            headers={
                "Content-Type": "application/json",
                "x-square-hmacsha256-signature": "valid-sig",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "received"

    def test_webhook_invalid_signature(self, client, mocker):
        """Webhook with invalid signature returns 401."""
        mock_service = mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        )
        mock_service.return_value.verify_webhook.return_value = False

        response = client.post(
            "/api/v1/payments/webhooks/square",
            content=json.dumps({"type": "test"}),
            headers={
                "Content-Type": "application/json",
                "x-square-hmacsha256-signature": "bad-sig",
            },
        )

        assert response.status_code == 401

    def test_webhook_payment_completed(self, client, mocker):
        """Webhook handles payment.completed event."""
        mock_service = mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        )
        mock_service.return_value.verify_webhook.return_value = True

        event = {
            "type": "payment.completed",
            "data": {
                "object": {
                    "payment": {
                        "id": "sq_pay_789",
                        "status": "COMPLETED",
                        "amount_money": {"amount": 5000},
                    }
                }
            },
        }

        response = client.post(
            "/api/v1/payments/webhooks/square",
            content=json.dumps(event),
            headers={
                "Content-Type": "application/json",
                "x-square-hmacsha256-signature": "valid",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "received"

    def test_webhook_payment_failed(self, client, mocker):
        """Webhook handles payment.failed event."""
        mock_service = mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        )
        mock_service.return_value.verify_webhook.return_value = True

        event = {
            "type": "payment.failed",
            "data": {"object": {"payment": {"id": "sq_pay_999"}}},
        }

        response = client.post(
            "/api/v1/payments/webhooks/square",
            content=json.dumps(event),
            headers={
                "Content-Type": "application/json",
                "x-square-hmacsha256-signature": "valid",
            },
        )

        assert response.status_code == 200

    def test_webhook_refund_created(self, client, mocker):
        """Webhook handles refund.created event."""
        mock_service = mocker.patch(
            "src.routers.square_payments.SquarePaymentService"
        )
        mock_service.return_value.verify_webhook.return_value = True

        event = {
            "type": "refund.created",
            "data": {"object": {"refund": {"id": "sq_refund_456"}}},
        }

        response = client.post(
            "/api/v1/payments/webhooks/square",
            content=json.dumps(event),
            headers={
                "Content-Type": "application/json",
                "x-square-hmacsha256-signature": "valid",
            },
        )

        assert response.status_code == 200
