"""
Tests for Week 40 P2 Batch 1 Reports - Registration & Book Analytics.

Created: February 6, 2026
Phase 7g - Report Implementation
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from src.services.referral_report_service import ReferralReportService
from src.models.referral_book import ReferralBook
from src.models.book_registration import BookRegistration
from src.models.member import Member
from src.db.enums import RegistrationStatus, MemberStatus, MemberClassification


# --- Fixtures ---


@pytest.fixture
def test_member_w40(db_session):
    """Create test member with UUID suffix."""
    member = Member(
        first_name="Test",
        last_name=f"Member_{uuid4().hex[:8]}",
        email=f"test_{uuid4().hex[:8]}@example.com",
        status=MemberStatus.ACTIVE,
        classification=MemberClassification.JOURNEYMAN,
    )
    db_session.add(member)
    db_session.commit()
    return member


@pytest.fixture
def test_book_w40(db_session):
    """Create test referral book with UUID suffix."""
    book = ReferralBook(
        book_name=f"TEST_BOOK_{uuid4().hex[:8]}",
        classification="WIRE",
        region="TEST",
        book_priority_number=1,
    )
    db_session.add(book)
    db_session.commit()
    return book


@pytest.fixture
def test_registration_w40(db_session, test_member_w40, test_book_w40):
    """Create test registration."""
    # APN: 45000.50 (Excel serial ~2023)
    reg = BookRegistration(
        member_id=test_member_w40.id,
        book_id=test_book_w40.id,
        registration_number=45000.50,
        status=RegistrationStatus.REGISTERED,
    )
    db_session.add(reg)
    db_session.commit()
    return reg


# --- Report 1: Registration Aging ---


def test_registration_aging_service(db_session, test_registration_w40):
    """Service returns aging data structure."""
    service = ReferralReportService(db_session)
    result = service.generate_registration_aging_report(format="pdf")
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_registration_aging_api(client, auth_headers, test_registration_w40):
    """API endpoint returns PDF."""
    response = client.get("/api/v1/reports/referral/registration-aging", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


# --- Report 2: Registration Turnover ---


def test_registration_turnover_service(db_session):
    """Service returns turnover data structure."""
    service = ReferralReportService(db_session)
    result = service.generate_registration_turnover_report(format="pdf")
    assert isinstance(result, bytes)


def test_registration_turnover_api(client, auth_headers):
    """API endpoint returns PDF."""
    response = client.get("/api/v1/reports/referral/registration-turnover", headers=auth_headers)
    assert response.status_code == 200


# --- Report 3: Re-Sign Compliance ---


def test_re_sign_compliance_service(db_session):
    """Service returns re-sign compliance data."""
    service = ReferralReportService(db_session)
    result = service.generate_re_sign_compliance_report(format="pdf")
    assert isinstance(result, bytes)


def test_re_sign_compliance_api(client, auth_headers):
    """API endpoint returns PDF."""
    response = client.get("/api/v1/reports/referral/re-sign-compliance", headers=auth_headers)
    assert response.status_code == 200


# --- Report 4: Re-Registration Patterns ---


def test_re_registration_patterns_service(db_session):
    """Service returns re-registration pattern data."""
    service = ReferralReportService(db_session)
    result = service.generate_re_registration_patterns_report(format="pdf")
    assert isinstance(result, bytes)


def test_re_registration_patterns_api(client, auth_headers):
    """API endpoint returns PDF."""
    response = client.get("/api/v1/reports/referral/re-registration-patterns", headers=auth_headers)
    assert response.status_code == 200


# --- Report 5: Inactive Registrations ---


def test_inactive_registrations_service(db_session, test_registration_w40):
    """Service returns inactive registration data."""
    service = ReferralReportService(db_session)
    result = service.generate_inactive_registrations_report(format="pdf")
    assert isinstance(result, bytes)


def test_inactive_registrations_api(client, auth_headers):
    """API endpoint returns PDF."""
    response = client.get("/api/v1/reports/referral/inactive-registrations", headers=auth_headers)
    assert response.status_code == 200


# --- Report 6: Cross-Book Registration ---


def test_cross_book_registration_service(db_session):
    """Service returns cross-book registration data."""
    service = ReferralReportService(db_session)
    result = service.generate_cross_book_registration_report(format="pdf")
    assert isinstance(result, bytes)


def test_cross_book_registration_api(client, auth_headers):
    """API endpoint returns PDF."""
    response = client.get("/api/v1/reports/referral/cross-book-registration", headers=auth_headers)
    assert response.status_code == 200


# --- Report 7: Classification Demand Gap ---


def test_classification_demand_gap_service(db_session):
    """Service returns demand gap data."""
    service = ReferralReportService(db_session)
    result = service.generate_classification_demand_gap_report(format="pdf")
    assert isinstance(result, bytes)


def test_classification_demand_gap_api(client, auth_headers):
    """API endpoint returns PDF."""
    response = client.get("/api/v1/reports/referral/classification-demand-gap", headers=auth_headers)
    assert response.status_code == 200


# --- Report 8: Book Comparison Dashboard ---


def test_book_comparison_service(db_session, test_book_w40):
    """Service returns book comparison data."""
    service = ReferralReportService(db_session)
    result = service.generate_book_comparison_report(format="pdf")
    assert isinstance(result, bytes)


def test_book_comparison_api(client, auth_headers):
    """API endpoint returns PDF."""
    response = client.get("/api/v1/reports/referral/book-comparison-dashboard", headers=auth_headers)
    assert response.status_code == 200


# --- Report 9: Tier Distribution ---


def test_tier_distribution_service(db_session, test_book_w40):
    """Service returns tier distribution data."""
    service = ReferralReportService(db_session)
    result = service.generate_tier_distribution_report(format="pdf")
    assert isinstance(result, bytes)


def test_tier_distribution_api(client, auth_headers):
    """API endpoint returns PDF."""
    response = client.get("/api/v1/reports/referral/tier-distribution", headers=auth_headers)
    assert response.status_code == 200


# --- Report 10: Book Capacity Trends ---


def test_book_capacity_trends_service(db_session):
    """Service returns capacity trend data."""
    service = ReferralReportService(db_session)
    result = service.generate_book_capacity_trends_report(format="pdf")
    assert isinstance(result, bytes)


def test_book_capacity_trends_api(client, auth_headers):
    """API endpoint returns PDF."""
    response = client.get("/api/v1/reports/referral/book-capacity-trends", headers=auth_headers)
    assert response.status_code == 200


# --- Report 11: APN Wait Time ---


def test_apn_wait_time_service(db_session):
    """Service returns APN wait time data."""
    service = ReferralReportService(db_session)
    result = service.generate_apn_wait_time_report(format="pdf")
    assert isinstance(result, bytes)


def test_apn_wait_time_api(client, auth_headers):
    """API endpoint returns PDF."""
    response = client.get("/api/v1/reports/referral/apn-wait-time", headers=auth_headers)
    assert response.status_code == 200


# --- Report 12: Seasonal Registration ---


def test_seasonal_registration_service(db_session):
    """Service returns seasonal pattern data."""
    service = ReferralReportService(db_session)
    result = service.generate_seasonal_registration_report(format="pdf")
    assert isinstance(result, bytes)


def test_seasonal_registration_api(client, auth_headers):
    """API endpoint returns PDF."""
    response = client.get("/api/v1/reports/referral/seasonal-registration", headers=auth_headers)
    assert response.status_code == 200
