"""Tests for Stripe payment integration."""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from sqlalchemy.orm import Session

from src.services.payment_service import PaymentService
from src.models.member import Member


class TestPaymentService:
    """Tests for PaymentService."""

    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session(self, mock_create, db_session, test_member):
        """Test creating a Stripe Checkout Session."""
        # Arrange
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_create.return_value = mock_session

        # Act
        result = PaymentService.create_dues_checkout_session(
            db=db_session,
            member_id=test_member.id,
            amount=Decimal("50.00"),
            period_id=1,
            description="Test Payment",
            success_url="http://localhost/success",
            cancel_url="http://localhost/cancel"
        )

        # Assert
        assert result == "https://checkout.stripe.com/test"
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs['mode'] == 'payment'
        assert call_kwargs['line_items'][0]['price_data']['unit_amount'] == 5000  # cents

    @patch('stripe.checkout.Session.create')
    def test_checkout_session_includes_metadata(self, mock_create, db_session, test_member):
        """Test that checkout session includes member/period metadata."""
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_create.return_value = mock_session

        PaymentService.create_dues_checkout_session(
            db=db_session,
            member_id=42,
            amount=Decimal("100.00"),
            period_id=7,
            description="Dues",
            success_url="http://localhost/success",
            cancel_url="http://localhost/cancel"
        )

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs['metadata']['member_id'] == '42'
        assert call_kwargs['metadata']['period_id'] == '7'
        assert call_kwargs['metadata']['payment_type'] == 'dues'

    @patch('stripe.checkout.Session.create')
    def test_checkout_uses_existing_customer_id(self, mock_create, db_session, test_member):
        """Test that existing stripe_customer_id is included in checkout session."""
        # Set stripe_customer_id on member
        test_member.stripe_customer_id = "cus_test123"
        db_session.commit()

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_create.return_value = mock_session

        PaymentService.create_dues_checkout_session(
            db=db_session,
            member_id=test_member.id,
            amount=Decimal("50.00"),
            period_id=1,
            description="Test",
            success_url="http://localhost/success",
            cancel_url="http://localhost/cancel"
        )

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs['customer'] == "cus_test123"

    def test_save_stripe_customer_id(self, db_session, test_member):
        """Test saving Stripe customer ID to member record."""
        # Act
        PaymentService.save_stripe_customer_id(
            db=db_session,
            member_id=test_member.id,
            stripe_customer_id="cus_new123"
        )

        # Assert
        db_session.refresh(test_member)
        assert test_member.stripe_customer_id == "cus_new123"

    def test_save_stripe_customer_id_invalid_member(self, db_session):
        """Test saving customer ID for non-existent member raises error."""
        with pytest.raises(ValueError, match="Member .* not found"):
            PaymentService.save_stripe_customer_id(
                db=db_session,
                member_id=99999,
                stripe_customer_id="cus_test123"
            )

    @patch('stripe.Webhook.construct_event')
    def test_construct_webhook_event_valid(self, mock_construct):
        """Test webhook event construction with valid signature."""
        mock_event = {'type': 'checkout.session.completed'}
        mock_construct.return_value = mock_event

        result = PaymentService.construct_webhook_event(
            payload=b'test_payload',
            sig_header='test_signature'
        )

        assert result == mock_event
        mock_construct.assert_called_once()

    @patch('stripe.Webhook.construct_event')
    def test_construct_webhook_event_invalid_signature(self, mock_construct):
        """Test webhook event construction with invalid signature."""
        import stripe
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", "test_sig"
        )

        with pytest.raises(ValueError, match="Invalid signature"):
            PaymentService.construct_webhook_event(
                payload=b'test_payload',
                sig_header='invalid_signature'
            )


class TestStripeWebhook:
    """Tests for Stripe webhook endpoint."""

    def test_webhook_requires_signature(self, client):
        """Test that webhook rejects requests without signature."""
        response = client.post(
            "/webhooks/stripe",
            json={"type": "test"}
        )
        assert response.status_code == 400
        assert "Stripe-Signature" in response.json()["detail"]

    @patch('src.services.payment_service.PaymentService.construct_webhook_event')
    @patch('src.services.dues_payment_service.create_payment')
    def test_webhook_checkout_session_completed(
        self, mock_create_payment, mock_construct, client, db_session, test_member, test_period
    ):
        """Test webhook handles checkout.session.completed event."""
        mock_construct.return_value = {
            'type': 'checkout.session.completed',
            'id': 'evt_test123',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'metadata': {
                        'member_id': str(test_member.id),
                        'period_id': str(test_period.id),
                        'payment_type': 'dues'
                    },
                    'amount_total': 5000,  # $50.00 in cents
                    'payment_method_types': ['card'],
                    'customer': 'cus_test123'
                }
            }
        }

        # Mock payment creation
        mock_payment = MagicMock()
        mock_payment.id = 1
        mock_create_payment.return_value = mock_payment

        response = client.post(
            "/webhooks/stripe",
            content=b'test_payload',
            headers={"Stripe-Signature": "test_sig"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "received"


class TestMemberModel:
    """Tests for Member model with Stripe integration."""

    def test_member_has_stripe_customer_id_field(self, db_session, test_member):
        """Test that Member model has stripe_customer_id field."""
        assert hasattr(test_member, 'stripe_customer_id')
        assert test_member.stripe_customer_id is None  # Default

    def test_member_stripe_customer_id_unique(self, db_session, test_member):
        """Test that stripe_customer_id must be unique."""
        from src.models.member import Member
        from src.db.enums import MemberStatus, MemberClassification

        # Set customer ID on first member
        test_member.stripe_customer_id = "cus_unique123"
        db_session.commit()

        # Try to create second member with same customer ID
        member2 = Member(
            member_number="TEST002",
            first_name="Jane",
            last_name="Doe",
            status=MemberStatus.ACTIVE,
            classification=MemberClassification.APPRENTICE,
            stripe_customer_id="cus_unique123"
        )
        db_session.add(member2)

        # Should raise IntegrityError due to unique constraint
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db_session.commit()


class TestDuesPaymentMethodEnum:
    """Tests for DuesPaymentMethod enum updates."""

    def test_stripe_payment_methods_exist(self):
        """Test that Stripe payment methods are in the enum."""
        from src.db.enums import DuesPaymentMethod

        assert hasattr(DuesPaymentMethod, 'STRIPE_CARD')
        assert hasattr(DuesPaymentMethod, 'STRIPE_ACH')
        assert hasattr(DuesPaymentMethod, 'STRIPE_OTHER')

        assert DuesPaymentMethod.STRIPE_CARD.value == 'stripe_card'
        assert DuesPaymentMethod.STRIPE_ACH.value == 'stripe_ach'
        assert DuesPaymentMethod.STRIPE_OTHER.value == 'stripe_other'
