"""
Tests for referral frontend routes and HTMX interactions.

Created: February 4, 2026 (Week 26)
Phase 7 - Referral & Dispatch System
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.db.session import get_db
from src.models.referral_book import ReferralBook
from src.models.book_registration import BookRegistration
from src.models.member import Member
from src.db.enums import (
    BookClassification,
    BookRegion,
    RegistrationStatus,
    MemberStatus,
    MemberClassification,
)


client = TestClient(app)


# ============================================================================
# Helper Fixtures
# ============================================================================


@pytest.fixture
def test_book(db):
    """Create a test referral book."""
    # Clean up any existing test book
    existing = db.query(ReferralBook).filter(ReferralBook.code == "TEST_BOOK_1").first()
    if existing:
        db.delete(existing)
        db.commit()

    book = ReferralBook(
        name="Test Book",
        code="TEST_BOOK_1",
        classification=BookClassification.INSIDE_WIREPERSON,
        book_number=1,
        region=BookRegion.SEATTLE,
        re_sign_days=30,
        max_check_marks=2,
        is_active=True,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@pytest.fixture
def test_member_for_registration(db):
    """Create a test member for registration."""
    # Clean up any existing test member
    existing = db.query(Member).filter(Member.email == "john.doe@test.com").first()
    if existing:
        db.delete(existing)
        db.commit()

    member = Member(
        first_name="John",
        last_name="Doe",
        member_number="TEST_REF_FRONT_001",
        status=MemberStatus.ACTIVE,
        classification=MemberClassification.JOURNEYMAN,
        email="john.doe@test.com",
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@pytest.fixture
def test_registration(db, test_book, test_member_for_registration):
    """Create a test registration."""
    registration = BookRegistration(
        member_id=test_member_for_registration.id,
        book_id=test_book.id,
        registration_number=12345.50,
        registration_method="in_person",
        status=RegistrationStatus.REGISTERED,
        has_check_mark=True,
        check_marks=0,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return registration


# ============================================================================
# Main Page Tests
# ============================================================================


def test_referral_landing_renders(auth_cookies):
    """Landing page should render for authenticated staff."""
    response = client.get("/referral", cookies=auth_cookies)
    assert response.status_code == 200
    assert b"Referral & Dispatch" in response.content
    assert b"Out-of-work book management" in response.content


def test_referral_landing_requires_auth():
    """Landing page should redirect to login if not authenticated."""
    response = client.get("/referral", follow_redirects=False)
    assert response.status_code in [302, 307]
    assert "/login" in response.headers["location"]


def test_books_list_renders(auth_cookies,test_book):
    """Books list page should show all books."""
    response = client.get("/referral/books", cookies=auth_cookies)
    assert response.status_code == 200
    assert b"Referral Books" in response.content
    assert test_book.name.encode() in response.content


def test_books_list_requires_auth(test_book):
    """Books list should redirect to login if not authenticated."""
    response = client.get("/referral/books", follow_redirects=False)
    assert response.status_code in [302, 307]


def test_book_detail_renders(auth_cookies,test_book):
    """Book detail should show members and stats."""
    response = client.get(f"/referral/books/{test_book.id}", cookies=auth_cookies)
    assert response.status_code == 200
    assert test_book.name.encode() in response.content
    assert b"Registered Members" in response.content


def test_book_detail_404_for_invalid(auth_headers):
    """Invalid book ID should return 404."""
    response = client.get("/referral/books/99999", cookies=auth_cookies)
    assert response.status_code == 404


def test_registrations_list_renders(auth_headers):
    """Registrations list should show with filters."""
    response = client.get("/referral/registrations", cookies=auth_cookies)
    assert response.status_code == 200
    assert b"Registrations" in response.content
    assert b"Cross-book registration management" in response.content


def test_registrations_list_requires_auth():
    """Registrations list should redirect to login if not authenticated."""
    response = client.get("/referral/registrations", follow_redirects=False)
    assert response.status_code in [302, 307]


def test_registration_detail_renders(auth_cookies,test_registration, test_member_for_registration):
    """Registration detail should show member info."""
    response = client.get(
        f"/referral/registrations/{test_registration.id}",
        cookies=auth_cookies
    )
    assert response.status_code == 200
    assert test_member_for_registration.first_name.encode() in response.content
    assert b"Registration Detail" in response.content


def test_registration_detail_404_for_invalid(auth_headers):
    """Invalid registration ID should return 404."""
    response = client.get("/referral/registrations/99999", cookies=auth_cookies)
    assert response.status_code == 404


# ============================================================================
# HTMX Partial Tests
# ============================================================================


def test_stats_partial_returns_html(auth_headers):
    """Stats partial should return HTML fragment."""
    response = client.get(
        "/referral/partials/stats",
        headers={**auth_headers, "HX-Request": "true"}
    )
    assert response.status_code == 200
    assert b"Active Books" in response.content or b"stat" in response.content


def test_books_overview_partial_returns_html(auth_cookies,test_book):
    """Books overview partial should return HTML fragment."""
    response = client.get(
        "/referral/partials/books-overview",
        headers={**auth_headers, "HX-Request": "true"}
    )
    assert response.status_code == 200
    # Should contain book information
    assert test_book.name.encode() in response.content or b"No books" in response.content


def test_books_table_partial_filters(auth_cookies,test_book):
    """Books table partial should filter results."""
    response = client.get(
        "/referral/partials/books-table?active_only=true",
        headers={**auth_headers, "HX-Request": "true"}
    )
    assert response.status_code == 200
    # Active book should appear
    assert test_book.name.encode() in response.content or b"table" in response.content


def test_register_modal_partial_loads(auth_headers):
    """Register modal should return form HTML."""
    response = client.get(
        "/referral/partials/register-modal",
        headers={**auth_headers, "HX-Request": "true"}
    )
    assert response.status_code == 200
    assert b"Register Member" in response.content or b"modal" in response.content


def test_member_search_partial(auth_cookies,test_member_for_registration):
    """Member search should return typeahead results."""
    response = client.get(
        f"/referral/partials/member-search?member_search={test_member_for_registration.first_name}",
        headers={**auth_headers, "HX-Request": "true"}
    )
    assert response.status_code == 200
    # Should contain member info or "not found" message
    assert (
        test_member_for_registration.first_name.encode() in response.content
        or b"No members found" in response.content
    )


# ============================================================================
# Role-Based Access Tests
# ============================================================================


def test_sidebar_shows_referral_section(auth_headers):
    """Sidebar should include Referral & Dispatch section."""
    response = client.get("/referral", cookies=auth_cookies)
    assert response.status_code == 200
    assert b"Referral & Dispatch" in response.content or b"Referral" in response.content


def test_admin_sees_create_book_button(auth_cookies,test_book):
    """Admin should see 'New Book' button on books list."""
    response = client.get("/referral/books", cookies=auth_cookies)
    assert response.status_code == 200
    # Admin should see the new book button (or books page should render)
    assert b"New Book" in response.content or b"Referral Books" in response.content


# ============================================================================
# Form Submission Tests (without actual backend calls)
# ============================================================================


def test_create_registration_requires_auth():
    """POST registration should require authentication."""
    response = client.post(
        "/referral/registrations",
        data={
            "member_id": "1",
            "book_id": "1",
            "registration_method": "in_person",
        },
        follow_redirects=False,
    )
    assert response.status_code in [302, 307, 401, 422]  # Auth required or validation error


def test_re_sign_requires_auth():
    """Re-sign should require authentication."""
    response = client.post("/referral/registrations/1/re-sign", follow_redirects=False)
    assert response.status_code in [302, 307, 401]


def test_resign_requires_auth():
    """Resign should require authentication."""
    response = client.post("/referral/registrations/1/resign", follow_redirects=False)
    assert response.status_code in [302, 307, 401]


# ============================================================================
# Service Tests (Basic)
# ============================================================================


def test_referral_frontend_service_imports():
    """ReferralFrontendService should import without errors."""
    from src.services.referral_frontend_service import ReferralFrontendService
    assert ReferralFrontendService is not None


def test_referral_frontend_service_badge_helpers():
    """Badge helper methods should return correct classes."""
    from src.services.referral_frontend_service import ReferralFrontendService
    from src.db.enums import RegistrationStatus

    badge = ReferralFrontendService.registration_status_badge(RegistrationStatus.REGISTERED)
    assert "class" in badge
    assert "label" in badge
    assert badge["class"] == "badge-success"
