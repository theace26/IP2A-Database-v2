"""
Tests for Phase 7 models - Referral & Dispatch System.

Created: February 4, 2026 (Week 20)
Tests: ReferralBook, BookRegistration, RegistrationActivity
"""
import pytest
from datetime import datetime, time, date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.base import Base
from src.models import (
    Member,
    ReferralBook,
    BookRegistration,
    RegistrationActivity,
    User,
    Role,
)
from src.db.enums import (
    MemberStatus,
    MemberClassification,
    BookClassification,
    BookRegion,
    RegistrationStatus,
    RegistrationAction,
    ExemptReason,
    RolloffReason,
)
from src.config.settings import get_settings


# Use the actual test database (PostgreSQL), not SQLite
settings = get_settings()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test using PostgreSQL."""
    engine = create_engine(str(settings.DATABASE_URL), echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.rollback()
    session.close()


@pytest.fixture
def test_member(db_session):
    """Create a test member."""
    member = Member(
        member_number="TEST001",
        first_name="John",
        last_name="Wireman",
        status=MemberStatus.ACTIVE,
        classification=MemberClassification.JOURNEYMAN_WIREMAN,
    )
    db_session.add(member)
    db_session.commit()
    return member


@pytest.fixture
def test_user(db_session):
    """Create a test user for performed_by fields."""
    # Create a role first
    role = Role(name="admin", description="Admin role", is_system_role=True)
    db_session.add(role)
    db_session.commit()

    user = User(
        email="dispatcher@test.com",
        hashed_password="fakehash",
        first_name="Test",
        last_name="Dispatcher",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_book(db_session):
    """Create a test referral book."""
    book = ReferralBook(
        name="Wire Seattle",
        code="WIRE_SEA_1",
        classification=BookClassification.INSIDE_WIREPERSON,
        book_number=1,
        region=BookRegion.SEATTLE,
        referral_start_time=time(8, 30),
        re_sign_days=30,
        max_check_marks=2,
        is_active=True,
        internet_bidding_enabled=True,
    )
    db_session.add(book)
    db_session.commit()
    return book


class TestReferralBook:
    """Tests for the ReferralBook model."""

    def test_create_referral_book(self, db_session):
        """Test creating a referral book."""
        book = ReferralBook(
            name="Wire Bremerton",
            code="WIRE_BREM_1",
            classification=BookClassification.INSIDE_WIREPERSON,
            book_number=1,
            region=BookRegion.BREMERTON,
            referral_start_time=time(8, 30),
            re_sign_days=30,
            max_check_marks=2,
        )
        db_session.add(book)
        db_session.commit()

        assert book.id is not None
        assert book.name == "Wire Bremerton"
        assert book.code == "WIRE_BREM_1"
        assert book.classification == BookClassification.INSIDE_WIREPERSON
        assert book.region == BookRegion.BREMERTON
        assert book.is_active is True

    def test_referral_book_unique_code(self, db_session, test_book):
        """Test that book codes are unique."""
        duplicate_book = ReferralBook(
            name="Duplicate Book",
            code="WIRE_SEA_1",  # Same code as test_book
            classification=BookClassification.INSIDE_WIREPERSON,
            book_number=1,
            region=BookRegion.SEATTLE,
        )
        db_session.add(duplicate_book)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_referral_book_defaults(self, db_session):
        """Test default values for referral book."""
        book = ReferralBook(
            name="Test Book",
            code="TEST_1",
            classification=BookClassification.TRADESHOW,
            region=BookRegion.SEATTLE,
        )
        db_session.add(book)
        db_session.commit()

        assert book.book_number == 1
        assert book.re_sign_days == 30
        assert book.max_check_marks == 2
        assert book.is_active is True
        assert book.internet_bidding_enabled is True

    def test_referral_book_full_name_property(self, test_book):
        """Test the full_name property."""
        assert test_book.full_name == "Wire Seattle Book 1"

    def test_referral_book_is_wire_book_property(self, db_session):
        """Test the is_wire_book property."""
        wire_book = ReferralBook(
            name="Wire Test",
            code="WIRE_TEST",
            classification=BookClassification.INSIDE_WIREPERSON,
            region=BookRegion.SEATTLE,
        )
        tradeshow_book = ReferralBook(
            name="Trade Test",
            code="TRADE_TEST",
            classification=BookClassification.TRADESHOW,
            region=BookRegion.SEATTLE,
        )
        db_session.add_all([wire_book, tradeshow_book])
        db_session.commit()

        assert wire_book.is_wire_book is True
        assert tradeshow_book.is_wire_book is False


class TestBookRegistration:
    """Tests for the BookRegistration model."""

    def test_create_registration(self, db_session, test_member, test_book):
        """Test creating a book registration."""
        registration = BookRegistration(
            member_id=test_member.id,
            book_id=test_book.id,
            registration_number=Decimal("1000.00"),
            registration_method="in_person",
            status=RegistrationStatus.REGISTERED,
        )
        db_session.add(registration)
        db_session.commit()

        assert registration.id is not None
        assert registration.member_id == test_member.id
        assert registration.book_id == test_book.id
        assert registration.registration_number == Decimal("1000.00")
        assert registration.status == RegistrationStatus.REGISTERED
        assert registration.check_marks == 0
        assert registration.is_exempt is False

    def test_registration_decimal_apn(self, db_session, test_member, test_book):
        """Test that APN is properly handled as decimal."""
        reg1 = BookRegistration(
            member_id=test_member.id,
            book_id=test_book.id,
            registration_number=Decimal("45880.41"),
            status=RegistrationStatus.REGISTERED,
        )
        db_session.add(reg1)
        db_session.commit()

        fetched = db_session.query(BookRegistration).filter_by(id=reg1.id).first()
        assert fetched.registration_number == Decimal("45880.41")

    def test_registration_is_active_property(self, db_session, test_member, test_book):
        """Test the is_active property."""
        reg = BookRegistration(
            member_id=test_member.id,
            book_id=test_book.id,
            registration_number=Decimal("1000.00"),
            status=RegistrationStatus.REGISTERED,
        )
        db_session.add(reg)
        db_session.commit()

        assert reg.is_active is True

        reg.status = RegistrationStatus.ROLLED_OFF
        db_session.commit()
        assert reg.is_active is False

    def test_registration_can_be_dispatched(self, db_session, test_member, test_book):
        """Test the can_be_dispatched property."""
        reg = BookRegistration(
            member_id=test_member.id,
            book_id=test_book.id,
            registration_number=Decimal("1000.00"),
            status=RegistrationStatus.REGISTERED,
            is_exempt=False,
        )
        db_session.add(reg)
        db_session.commit()

        assert reg.can_be_dispatched is True

        # Exempt members cannot be dispatched
        reg.is_exempt = True
        assert reg.can_be_dispatched is False

    def test_registration_check_marks_remaining(self, db_session, test_member, test_book):
        """Test the check_marks_remaining property."""
        reg = BookRegistration(
            member_id=test_member.id,
            book_id=test_book.id,
            registration_number=Decimal("1000.00"),
            status=RegistrationStatus.REGISTERED,
            check_marks=0,
        )
        db_session.add(reg)
        db_session.commit()

        assert reg.check_marks_remaining == 2

        reg.check_marks = 1
        assert reg.check_marks_remaining == 1

        reg.check_marks = 2
        assert reg.check_marks_remaining == 0

    def test_registration_exempt_status(self, db_session, test_member, test_book):
        """Test exempt status fields."""
        reg = BookRegistration(
            member_id=test_member.id,
            book_id=test_book.id,
            registration_number=Decimal("1000.00"),
            status=RegistrationStatus.REGISTERED,
            is_exempt=True,
            exempt_reason=ExemptReason.MEDICAL,
            exempt_start_date=date.today(),
            exempt_end_date=date.today() + timedelta(days=180),
        )
        db_session.add(reg)
        db_session.commit()

        assert reg.is_exempt is True
        assert reg.exempt_reason == ExemptReason.MEDICAL
        assert reg.exempt_end_date == date.today() + timedelta(days=180)

    def test_registration_rolloff(self, db_session, test_member, test_book):
        """Test rolloff fields."""
        reg = BookRegistration(
            member_id=test_member.id,
            book_id=test_book.id,
            registration_number=Decimal("1000.00"),
            status=RegistrationStatus.ROLLED_OFF,
            roll_off_date=datetime.utcnow(),
            roll_off_reason=RolloffReason.CHECK_MARKS,
        )
        db_session.add(reg)
        db_session.commit()

        assert reg.is_rolled_off is True
        assert reg.roll_off_reason == RolloffReason.CHECK_MARKS

    def test_registration_relationship_to_member(self, db_session, test_member, test_book):
        """Test the registration-member relationship."""
        reg = BookRegistration(
            member_id=test_member.id,
            book_id=test_book.id,
            registration_number=Decimal("1000.00"),
            status=RegistrationStatus.REGISTERED,
        )
        db_session.add(reg)
        db_session.commit()

        # Access through relationship
        assert reg.member.first_name == "John"
        assert len(test_member.book_registrations) == 1


class TestRegistrationActivity:
    """Tests for the RegistrationActivity model."""

    def test_create_activity(self, db_session, test_member, test_book, test_user):
        """Test creating a registration activity."""
        reg = BookRegistration(
            member_id=test_member.id,
            book_id=test_book.id,
            registration_number=Decimal("1000.00"),
            status=RegistrationStatus.REGISTERED,
        )
        db_session.add(reg)
        db_session.commit()

        activity = RegistrationActivity(
            registration_id=reg.id,
            member_id=test_member.id,
            book_id=test_book.id,
            action=RegistrationAction.REGISTER,
            new_status=RegistrationStatus.REGISTERED,
            performed_by_id=test_user.id,
            processor="SYSTEM",
            details="Initial registration",
        )
        db_session.add(activity)
        db_session.commit()

        assert activity.id is not None
        assert activity.action == RegistrationAction.REGISTER
        assert activity.new_status == RegistrationStatus.REGISTERED
        assert activity.processor == "SYSTEM"

    def test_activity_status_tracking(self, db_session, test_member, test_book, test_user):
        """Test tracking status changes in activity."""
        reg = BookRegistration(
            member_id=test_member.id,
            book_id=test_book.id,
            registration_number=Decimal("1000.00"),
            status=RegistrationStatus.REGISTERED,
        )
        db_session.add(reg)
        db_session.commit()

        activity = RegistrationActivity(
            registration_id=reg.id,
            member_id=test_member.id,
            book_id=test_book.id,
            action=RegistrationAction.ROLL_OFF,
            previous_status=RegistrationStatus.REGISTERED,
            new_status=RegistrationStatus.ROLLED_OFF,
            performed_by_id=test_user.id,
            reason="3rd check mark",
        )
        db_session.add(activity)
        db_session.commit()

        assert activity.previous_status == RegistrationStatus.REGISTERED
        assert activity.new_status == RegistrationStatus.ROLLED_OFF
        assert activity.reason == "3rd check mark"

    def test_activity_immutability_no_updated_at(self, db_session, test_member, test_book, test_user):
        """Test that RegistrationActivity has no updated_at (append-only)."""
        activity = RegistrationActivity(
            member_id=test_member.id,
            book_id=test_book.id,
            action=RegistrationAction.REGISTER,
            new_status=RegistrationStatus.REGISTERED,
            performed_by_id=test_user.id,
        )
        db_session.add(activity)
        db_session.commit()

        # RegistrationActivity should not have updated_at attribute
        assert not hasattr(activity, "updated_at") or activity.updated_at is None


class TestBookClassification:
    """Tests for BookClassification enum."""

    def test_all_classifications_exist(self):
        """Verify all expected classifications exist."""
        expected = [
            "INSIDE_WIREPERSON",
            "TRADESHOW",
            "SEATTLE_SCHOOL",
            "SOUND_COMM",
            "MARINE",
            "STOCKPERSON",
            "LIGHT_FIXTURE",
            "RESIDENTIAL",
            "TECHNICIAN",
            "UTILITY_WORKER",
            "TERO_APPRENTICE",
        ]
        for name in expected:
            assert hasattr(BookClassification, name)


class TestBookRegion:
    """Tests for BookRegion enum."""

    def test_all_regions_exist(self):
        """Verify all expected regions exist."""
        expected = ["SEATTLE", "BREMERTON", "PORT_ANGELES"]
        for name in expected:
            assert hasattr(BookRegion, name)


class TestRegistrationStatus:
    """Tests for RegistrationStatus enum."""

    def test_all_statuses_exist(self):
        """Verify all expected statuses exist."""
        expected = ["REGISTERED", "DISPATCHED", "ROLLED_OFF", "RESIGNED", "EXEMPT"]
        for name in expected:
            assert hasattr(RegistrationStatus, name)
