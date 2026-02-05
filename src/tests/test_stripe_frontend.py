"""Tests for Stripe payment frontend integration."""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal

pytestmark = pytest.mark.skip(
    reason="Stripe deprecated — migrating to Square (ADR-018). Remove with Square migration."
)


class TestPaymentInitiation:
    """Tests for payment initiation endpoint."""

    def test_initiate_payment_requires_auth(self, client):
        """Test that payment initiation requires authentication."""
        response = client.post("/dues/payments/initiate/1/1", follow_redirects=False)
        # Should redirect to login
        assert response.status_code in [302, 303, 401]

    @patch('src.services.payment_service.PaymentService.create_dues_checkout_session')
    @patch('src.services.member_service.MemberService.get_by_id')
    @patch('src.services.dues_period_service.DuesPeriodService.get_by_id')
    @patch('src.services.dues_frontend_service.DuesFrontendService.get_rate_for_member')
    def test_initiate_payment_redirects_to_stripe(
        self, mock_get_rate, mock_get_period, mock_get_member, mock_create_checkout,
        client, auth_cookies, test_member, test_period
    ):
        """Test that valid payment request redirects to Stripe."""
        # Mock the service calls
        mock_get_member.return_value = test_member
        mock_get_period.return_value = test_period

        # Mock rate
        mock_rate = MagicMock()
        mock_rate.monthly_amount = Decimal("50.00")
        mock_get_rate.return_value = mock_rate

        # Mock Stripe checkout URL
        mock_create_checkout.return_value = "https://checkout.stripe.com/test_session"

        response = client.post(
            f"/dues/payments/initiate/{test_member.id}/{test_period.id}",
            cookies=auth_cookies,
            follow_redirects=False
        )

        # Should redirect to Stripe
        assert response.status_code == 303
        assert "checkout.stripe.com" in response.headers.get("location", "")

    @patch('src.services.member_service.MemberService.get_by_id')
    def test_initiate_payment_invalid_member(self, mock_get_member, client, auth_cookies):
        """Test payment initiation with invalid member ID."""
        mock_get_member.return_value = None

        response = client.post(
            "/dues/payments/initiate/99999/1",
            cookies=auth_cookies
        )
        assert response.status_code == 404

    @patch('src.services.member_service.MemberService.get_by_id')
    @patch('src.services.dues_period_service.DuesPeriodService.get_by_id')
    def test_initiate_payment_invalid_period(
        self, mock_get_period, mock_get_member, client, auth_cookies, test_member
    ):
        """Test payment initiation with invalid period ID."""
        mock_get_member.return_value = test_member
        mock_get_period.return_value = None

        response = client.post(
            f"/dues/payments/initiate/{test_member.id}/99999",
            cookies=auth_cookies
        )
        assert response.status_code == 404


class TestPaymentSuccessPage:
    """Tests for payment success page."""

    def test_success_page_requires_auth(self, client):
        """Test that success page requires authentication."""
        response = client.get("/dues/payments/success", follow_redirects=False)
        assert response.status_code in [302, 303, 401]

    def test_success_page_renders(self, client, auth_cookies):
        """Test that success page renders correctly."""
        response = client.get(
            "/dues/payments/success",
            cookies=auth_cookies
        )
        assert response.status_code == 200
        assert b"Payment Successful" in response.content or b"payment successful" in response.content.lower()

    @patch('src.services.payment_service.PaymentService.retrieve_checkout_session')
    def test_success_page_with_session_id(self, mock_retrieve, client, auth_cookies):
        """Test success page with session ID parameter."""
        # Mock Stripe session
        mock_session = {
            "amount_total": 5000,  # $50.00 in cents
            "metadata": {"member_id": "1", "period_id": "1"},
            "payment_status": "paid"
        }
        mock_retrieve.return_value = mock_session

        response = client.get(
            "/dues/payments/success?session_id=cs_test_123",
            cookies=auth_cookies
        )
        assert response.status_code == 200
        assert b"50.00" in response.content or b"$50" in response.content

    @patch('src.services.payment_service.PaymentService.retrieve_checkout_session')
    def test_success_page_handles_missing_session(self, mock_retrieve, client, auth_cookies):
        """Test success page gracefully handles missing session."""
        mock_retrieve.side_effect = Exception("Session not found")

        response = client.get(
            "/dues/payments/success?session_id=invalid",
            cookies=auth_cookies
        )
        # Should still render successfully even if session retrieval fails
        assert response.status_code == 200


class TestPaymentCancelPage:
    """Tests for payment cancel page."""

    def test_cancel_page_requires_auth(self, client):
        """Test that cancel page requires authentication."""
        response = client.get("/dues/payments/cancel", follow_redirects=False)
        assert response.status_code in [302, 303, 401]

    def test_cancel_page_renders(self, client, auth_cookies):
        """Test that cancel page renders correctly."""
        response = client.get(
            "/dues/payments/cancel",
            cookies=auth_cookies
        )
        assert response.status_code == 200
        assert b"Payment Cancelled" in response.content or b"payment cancelled" in response.content.lower()

    def test_cancel_page_shows_retry_option(self, client, auth_cookies):
        """Test that cancel page shows option to retry."""
        response = client.get(
            "/dues/payments/cancel",
            cookies=auth_cookies
        )
        assert response.status_code == 200
        # Should have links back to dues
        assert b"/dues" in response.content


class TestDuesFrontendServiceStripe:
    """Tests for DuesFrontendService Stripe-related methods."""

    def test_get_rate_for_member_returns_active_rate(self, db_session, test_member):
        """Test getting active rate for a member's classification."""
        from src.services.dues_frontend_service import DuesFrontendService
        from src.models.dues_rate import DuesRate
        from datetime import date, timedelta

        # Create a rate for the member's classification
        rate = DuesRate(
            classification=test_member.classification,
            monthly_amount=Decimal("50.00"),
            effective_date=date.today() - timedelta(days=30),
            end_date=None  # Active indefinitely
        )
        db_session.add(rate)
        db_session.commit()

        # Get the rate
        result = DuesFrontendService.get_rate_for_member(db_session, test_member.id)

        assert result is not None
        assert result.classification == test_member.classification
        assert result.monthly_amount == Decimal("50.00")

    def test_get_rate_for_member_returns_most_recent(self, db_session, test_member):
        """Test that most recent active rate is returned when multiple exist."""
        from src.services.dues_frontend_service import DuesFrontendService
        from src.models.dues_rate import DuesRate
        from datetime import date, timedelta

        today = date.today()

        # Create older rate
        old_rate = DuesRate(
            classification=test_member.classification,
            monthly_amount=Decimal("40.00"),
            effective_date=today - timedelta(days=60),
            end_date=today - timedelta(days=1)  # Ended yesterday
        )

        # Create newer active rate
        new_rate = DuesRate(
            classification=test_member.classification,
            monthly_amount=Decimal("50.00"),
            effective_date=today,
            end_date=None
        )

        db_session.add_all([old_rate, new_rate])
        db_session.commit()

        # Get the rate
        result = DuesFrontendService.get_rate_for_member(db_session, test_member.id)

        assert result is not None
        assert result.monthly_amount == Decimal("50.00")  # Should get the new rate

    def test_get_rate_for_member_invalid_member(self, db_session):
        """Test getting rate for non-existent member returns None."""
        from src.services.dues_frontend_service import DuesFrontendService

        result = DuesFrontendService.get_rate_for_member(db_session, 99999)
        assert result is None

    def test_payment_method_display_includes_stripe(self):
        """Test that Stripe payment methods have proper display names."""
        from src.services.dues_frontend_service import DuesFrontendService
        from src.db.enums import DuesPaymentMethod

        assert "Stripe" in DuesFrontendService.get_payment_method_display(DuesPaymentMethod.STRIPE_CARD)
        assert "Stripe" in DuesFrontendService.get_payment_method_display(DuesPaymentMethod.STRIPE_ACH)
        assert "Stripe" in DuesFrontendService.get_payment_method_display(DuesPaymentMethod.STRIPE_OTHER)
