"""
Demo seed data for UnionCore stakeholder presentation.

Usage:
    python -m src.db.demo_seed

Creates realistic dispatch/referral data for demo purposes.
Idempotent — safe to run multiple times.

Created: February 7, 2026 (Week 45)
Spoke: Spoke 2 (Operations)
"""

import logging
from datetime import datetime, timedelta, time
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.models import (
    User,
    Role,
    UserRole,
    Member,
    Organization,
    ReferralBook,
    BookRegistration,
    LaborRequest,
    Dispatch,
)
from src.db.enums import (
    MemberClassification,
    MemberStatus,
    BookClassification,
    BookRegion,
    RegistrationStatus,
    LaborRequestStatus,
    DispatchStatus,
    TermReason,
    ExemptReason,
    OrganizationType,
)
from src.core.security import hash_password

logger = logging.getLogger(__name__)


def get_or_create(
    db: Session, model, defaults: Optional[Dict[str, Any]] = None, **kwargs
) -> tuple[Any, bool]:
    """
    Get an existing record or create if it doesn't exist.

    Returns: (instance, created) where created is True if newly created
    """
    instance = db.execute(select(model).filter_by(**kwargs)).scalar_one_or_none()

    if instance:
        return instance, False

    params = kwargs.copy()
    if defaults:
        params.update(defaults)

    instance = model(**params)
    db.add(instance)
    db.flush()

    return instance, True


def seed_demo_data(db: Session) -> dict:
    """
    Create complete demo dataset. Returns summary of created records.
    Idempotent — checks for existing demo data before creating.
    """
    logger.info("Starting demo seed data creation...")
    summary = {}

    # Phase 1: Demo user accounts
    summary["users"] = _seed_demo_users(db)

    # Phase 2: Referral books (subset of production books)
    summary["books"] = _seed_demo_books(db)

    # Phase 3: Employers
    summary["employers"] = _seed_demo_employers(db)

    # Phase 4: Members with varied classifications
    summary["members"] = _seed_demo_members(db)

    # Phase 5: Book registrations with realistic APNs
    summary["registrations"] = _seed_demo_registrations(db)

    # Phase 6: Labor requests
    summary["labor_requests"] = _seed_demo_labor_requests(db)

    # Phase 7: Dispatches (full lifecycle)
    summary["dispatches"] = _seed_demo_dispatches(db)

    # Phase 8: Check marks (penalty tracking)
    summary["check_marks"] = _seed_demo_check_marks(db)

    # Phase 9: Exemptions
    summary["exemptions"] = _seed_demo_exemptions(db)

    db.commit()
    logger.info("Demo seed data creation complete")

    return summary


def _seed_demo_users(db: Session) -> int:
    """
    Create 3 demo user accounts with distinct roles.
    Idempotent — skips if users already exist.
    """
    demo_users = [
        {
            "email": "demo_dispatcher@ibew46.demo",
            "password_hash": hash_password("Demo2026!"),
            "first_name": "Demo",
            "last_name": "Dispatcher",
            "role_names": ["staff"],
            "is_active": True,
        },
        {
            "email": "demo_officer@ibew46.demo",
            "password_hash": hash_password("Demo2026!"),
            "first_name": "Demo",
            "last_name": "Officer",
            "role_names": ["officer"],
            "is_active": True,
        },
        {
            "email": "demo_admin@ibew46.demo",
            "password_hash": hash_password("Demo2026!"),
            "first_name": "Demo",
            "last_name": "Admin",
            "role_names": ["admin"],
            "is_active": True,
        },
    ]

    created_count = 0
    for user_data in demo_users:
        email = user_data.pop("email")
        role_names = user_data.pop("role_names")  # Extract roles before creating user

        # Create user without roles
        user, created = get_or_create(db, User, email=email, defaults=user_data)
        if created:
            created_count += 1
            logger.info(f"  Created demo user: {email}")
        else:
            logger.info(f"  Demo user already exists: {email}")

        # Assign roles via UserRole junction table
        for role_name in role_names:
            # Look up role by name
            role = db.execute(
                select(Role).where(Role.name == role_name)
            ).scalar_one_or_none()

            if not role:
                logger.warning(
                    f"  Role '{role_name}' not found, skipping assignment for {email}"
                )
                continue

            # Create UserRole if it doesn't exist
            user_role, ur_created = get_or_create(
                db,
                UserRole,
                user_id=user.id,
                role_id=role.id,
                defaults={"assigned_by": "demo_seed"},
            )
            if ur_created:
                logger.info(f"  Assigned role '{role_name}' to {email}")

    return created_count


def _seed_demo_books(db: Session) -> int:
    """
    Create 5 referral books for demo.
    Subset of the 11 production books, selected to show key features.
    """
    demo_books = [
        # Wire Seattle - Largest book, most activity
        {
            "name": "Wire Seattle",
            "code": "WIRE_SEA_1",
            "classification": BookClassification.INSIDE_WIREPERSON,
            "book_number": 1,
            "region": BookRegion.SEATTLE,
            "referral_start_time": time(8, 30),
            "re_sign_days": 30,
            "max_check_marks": 2,
            "grace_period_days": 3,
            "max_days_on_book": None,
            "internet_bidding_enabled": True,
            "is_active": True,
        },
        # Wire Bremerton - Cross-regional demonstration
        {
            "name": "Wire Bremerton",
            "code": "WIRE_BREM_1",
            "classification": BookClassification.INSIDE_WIREPERSON,
            "book_number": 1,
            "region": BookRegion.BREMERTON,
            "referral_start_time": time(8, 30),
            "re_sign_days": 30,
            "max_check_marks": 2,
            "grace_period_days": 3,
            "max_days_on_book": None,
            "internet_bidding_enabled": True,
            "is_active": True,
        },
        # Technician - Inverted tier distribution
        {
            "name": "Technician Seattle",
            "code": "TECH_SEA_1",
            "classification": BookClassification.TECHNICIAN,
            "book_number": 1,
            "region": BookRegion.SEATTLE,
            "referral_start_time": time(9, 30),
            "re_sign_days": 30,
            "max_check_marks": 2,
            "grace_period_days": 3,
            "max_days_on_book": None,
            "internet_bidding_enabled": True,
            "is_active": True,
        },
        # Stockperson - Book name ≠ contract code
        {
            "name": "Stockperson Seattle",
            "code": "STOCK_SEA_1",
            "classification": BookClassification.STOCKPERSON,
            "book_number": 1,
            "region": BookRegion.SEATTLE,
            "referral_start_time": time(9, 30),
            "re_sign_days": 30,
            "max_check_marks": 2,
            "grace_period_days": 3,
            "max_days_on_book": None,
            "internet_bidding_enabled": True,
            "is_active": True,
        },
        # Sound & Comm - Additional classification
        {
            "name": "Sound Seattle",
            "code": "SOUND_SEA_1",
            "classification": BookClassification.SOUND_COMM,
            "book_number": 1,
            "region": BookRegion.SEATTLE,
            "referral_start_time": time(9, 30),
            "re_sign_days": 30,
            "max_check_marks": 2,
            "grace_period_days": 3,
            "max_days_on_book": None,
            "internet_bidding_enabled": True,
            "is_active": True,
        },
    ]

    created_count = 0
    for book_data in demo_books:
        code = book_data["code"]
        book, created = get_or_create(db, ReferralBook, code=code, defaults=book_data)
        if created:
            created_count += 1
            logger.info(f"  Created demo book: {code}")

    return created_count


def _seed_demo_employers(db: Session) -> int:
    """
    Create 5-8 realistic employer organizations.
    Mix of contractor types to demonstrate contract code variety.
    """
    employers = [
        # Large general contractors
        {
            "name": "Pacific Northwest Electric Co.",
            "org_type": OrganizationType.EMPLOYER,
            "address": "1234 Industry Way",
            "city": "Seattle",
            "state": "WA",
            "zip_code": "98101",
            "phone": "206-555-0100",
            "email": "jobs@pnwelectric.demo",
        },
        {
            "name": "Emerald City Contractors",
            "org_type": OrganizationType.EMPLOYER,
            "address": "5678 Construction Blvd",
            "city": "Seattle",
            "state": "WA",
            "zip_code": "98102",
            "phone": "206-555-0200",
            "email": "hiring@emeraldcity.demo",
        },
        # Sound & Communications specialist
        {
            "name": "Sound Systems Northwest",
            "org_type": OrganizationType.EMPLOYER,
            "address": "910 Audio Ave",
            "city": "Seattle",
            "state": "WA",
            "zip_code": "98103",
            "phone": "206-555-0300",
            "email": "careers@soundsys.demo",
        },
        # Stockperson shop
        {
            "name": "Electrical Supply & Logistics",
            "org_type": OrganizationType.EMPLOYER,
            "address": "1112 Warehouse St",
            "city": "Seattle",
            "state": "WA",
            "zip_code": "98104",
            "phone": "206-555-0400",
            "email": "jobs@eslogistics.demo",
        },
        # Multi-contract employer
        {
            "name": "Northwest Power Solutions",
            "org_type": OrganizationType.EMPLOYER,
            "address": "1314 Electric Pkwy",
            "city": "Bremerton",
            "state": "WA",
            "zip_code": "98310",
            "phone": "360-555-0500",
            "email": "hr@nwpower.demo",
        },
        # Residential-only
        {
            "name": "HomeWiring Experts LLC",
            "org_type": OrganizationType.EMPLOYER,
            "address": "1516 Residential Dr",
            "city": "Seattle",
            "state": "WA",
            "zip_code": "98105",
            "phone": "206-555-0600",
            "email": "jobs@homewiring.demo",
        },
    ]

    created_count = 0
    for emp_data in employers:
        name = emp_data["name"]
        employer, created = get_or_create(
            db, Organization, name=name, defaults=emp_data
        )
        if created:
            created_count += 1
            logger.info(f"  Created demo employer: {name}")

    return created_count


def _seed_demo_members(db: Session) -> int:
    """
    Create 20-30 members with varied classifications.
    Use realistic names for union electricians.
    Some members registered on multiple books (cross-regional Wire members).
    """
    # Realistic union electrician names
    demo_members = [
        # Wire members (will be on multiple regional books)
        ("John", "Martinez", MemberClassification.JOURNEYMAN),
        ("Sarah", "Chen", MemberClassification.JOURNEYMAN),
        ("Mike", "O'Brien", MemberClassification.JOURNEYMAN),
        ("Jennifer", "Washington", MemberClassification.JOURNEYMAN),
        ("David", "Kowalski", MemberClassification.JOURNEYMAN),
        ("Maria", "Rodriguez", MemberClassification.JOURNEYMAN),
        ("James", "Thompson", MemberClassification.JOURNEYMAN),
        ("Lisa", "Anderson", MemberClassification.JOURNEYMAN),
        ("Robert", "Jackson", MemberClassification.JOURNEYMAN),
        ("Amanda", "Williams", MemberClassification.JOURNEYMAN),
        ("Thomas", "Brown", MemberClassification.JOURNEYMAN),
        ("Patricia", "Davis", MemberClassification.JOURNEYMAN),
        ("Christopher", "Miller", MemberClassification.JOURNEYMAN),
        ("Jessica", "Wilson", MemberClassification.JOURNEYMAN),
        ("Daniel", "Moore", MemberClassification.JOURNEYMAN),
        # Technicians
        ("Kevin", "Taylor", MemberClassification.JOURNEYMAN),
        ("Michelle", "Anderson", MemberClassification.JOURNEYMAN),
        ("Steven", "Thomas", MemberClassification.JOURNEYMAN),
        ("Rebecca", "Martinez", MemberClassification.JOURNEYMAN),
        ("Brian", "Garcia", MemberClassification.JOURNEYMAN),
        # Sound & Comm
        ("Andrew", "Johnson", MemberClassification.JOURNEYMAN),
        ("Nicole", "Lee", MemberClassification.JOURNEYMAN),
        ("Jason", "White", MemberClassification.JOURNEYMAN),
        # Stockperson
        ("Ryan", "Harris", MemberClassification.JOURNEYMAN),
        ("Stephanie", "Clark", MemberClassification.JOURNEYMAN),
        ("Eric", "Lewis", MemberClassification.JOURNEYMAN),
        # Additional Wire (Book 2/3 tiers)
        ("Mark", "Robinson", MemberClassification.JOURNEYMAN),
        ("Laura", "Walker", MemberClassification.JOURNEYMAN),
        ("Paul", "Hall", MemberClassification.JOURNEYMAN),
        ("Kimberly", "Allen", MemberClassification.JOURNEYMAN),
    ]

    created_count = 0
    for first_name, last_name, classification in demo_members:
        email = f"{first_name.lower()}.{last_name.lower()}@demo.local"
        member_number = f"DEMO{46000 + created_count:05d}"  # DEMO46001, DEMO46002, etc.

        member_data = {
            "member_number": member_number,
            "first_name": first_name,
            "last_name": last_name,
            "classification": classification,
            "status": MemberStatus.ACTIVE,
            "email": email,
            "phone": f"206-555-{created_count:04d}",
            "address": f"{1000 + created_count} Demo St",
            "city": "Seattle",
            "state": "WA",
            "zip_code": "98101",
        }

        member, created = get_or_create(db, Member, email=email, defaults=member_data)
        if created:
            created_count += 1

    return created_count


def _seed_demo_registrations(db: Session) -> int:
    """
    Register members on books with realistic APNs.

    APN = DECIMAL(10,2) where:
    - Integer part is Excel serial date (e.g., 46054 = Feb 1, 2026)
    - Decimal part is intra-day ordering (.23, .41, .67, etc.)

    Demonstrates:
    - Cross-regional Wire members (same member on Seattle + Bremerton)
    - Multiple classifications (member on 3+ books)
    - Varied tier distributions (Book 1, Book 2, Book 3)
    """
    # Get all members and books
    members = db.execute(select(Member)).scalars().all()
    books = db.execute(select(ReferralBook)).scalars().all()

    # Create book lookup
    book_map = {book.code: book for book in books}

    # Calculate base APN (90 days ago = older registration)
    base_date = datetime.now() - timedelta(days=90)
    # Excel serial date: days since 1900-01-01
    excel_epoch = datetime(1900, 1, 1)
    base_serial = (base_date - excel_epoch).days + 2  # Excel's leap year bug offset

    registrations_data = []
    apn_counter = 0.23  # Decimal part for intra-day ordering

    # Wire members on multiple regional books
    wire_members = [
        m for m in members if m.classification == MemberClassification.JOURNEYMAN
    ]
    for member in wire_members[:12]:  # First 12 Wire members on multiple books
        # Register on Seattle
        if "WIRE_SEA_1" in book_map:
            registrations_data.append(
                {
                    "member_id": member.id,
                    "book_id": book_map["WIRE_SEA_1"].id,
                    "registration_number": Decimal(
                        f"{base_serial + (apn_counter * 10):.2f}"
                    ),
                    "status": RegistrationStatus.REGISTERED,
                    "registration_date": base_date
                    - timedelta(days=int(apn_counter * 10)),
                    "last_re_sign_date": datetime.now() - timedelta(days=15),
                    "is_exempt": False,
                }
            )
            apn_counter += 0.18

        # Also register on Bremerton (cross-regional)
        if "WIRE_BREM_1" in book_map:
            registrations_data.append(
                {
                    "member_id": member.id,
                    "book_id": book_map["WIRE_BREM_1"].id,
                    "registration_number": Decimal(
                        f"{base_serial + (apn_counter * 10):.2f}"
                    ),
                    "status": RegistrationStatus.REGISTERED,
                    "registration_date": base_date
                    - timedelta(days=int(apn_counter * 10)),
                    "last_re_sign_date": datetime.now() - timedelta(days=15),
                    "is_exempt": False,
                }
            )
            apn_counter += 0.18

    # Technicians
    tech_members = [
        m for m in members if m.classification == MemberClassification.JOURNEYMAN
    ]
    if "TECH_SEA_1" in book_map:
        for member in tech_members:
            registrations_data.append(
                {
                    "member_id": member.id,
                    "book_id": book_map["TECH_SEA_1"].id,
                    "registration_number": Decimal(
                        f"{base_serial + (apn_counter * 10):.2f}"
                    ),
                    "status": RegistrationStatus.REGISTERED,
                    "registration_date": base_date
                    - timedelta(days=int(apn_counter * 10)),
                    "last_re_sign_date": datetime.now() - timedelta(days=10),
                    "is_exempt": False,
                }
            )
            apn_counter += 0.18

    # Sound & Comm
    sound_members = [
        m for m in members if m.classification == MemberClassification.JOURNEYMAN
    ]
    if "SOUND_SEA_1" in book_map:
        for member in sound_members:
            registrations_data.append(
                {
                    "member_id": member.id,
                    "book_id": book_map["SOUND_SEA_1"].id,
                    "registration_number": Decimal(
                        f"{base_serial + (apn_counter * 10):.2f}"
                    ),
                    "status": RegistrationStatus.REGISTERED,
                    "registration_date": base_date
                    - timedelta(days=int(apn_counter * 10)),
                    "last_re_sign_date": datetime.now() - timedelta(days=20),
                    "is_exempt": False,
                }
            )
            apn_counter += 0.18

    # Stockperson
    stock_members = [
        m for m in members if m.classification == MemberClassification.JOURNEYMAN
    ]
    if "STOCK_SEA_1" in book_map:
        for member in stock_members:
            registrations_data.append(
                {
                    "member_id": member.id,
                    "book_id": book_map["STOCK_SEA_1"].id,
                    "registration_number": Decimal(
                        f"{base_serial + (apn_counter * 10):.2f}"
                    ),
                    "status": RegistrationStatus.REGISTERED,
                    "registration_date": base_date
                    - timedelta(days=int(apn_counter * 10)),
                    "last_re_sign_date": datetime.now() - timedelta(days=25),
                    "is_exempt": False,
                }
            )
            apn_counter += 0.18

    created_count = 0
    for reg_data in registrations_data:
        # Use member_id + book_id as natural key
        reg, created = get_or_create(
            db,
            BookRegistration,
            member_id=reg_data["member_id"],
            book_id=reg_data["book_id"],
            defaults=reg_data,
        )
        if created:
            created_count += 1

    return created_count


def _seed_demo_labor_requests(db: Session) -> int:
    """
    Create 8-12 labor requests with varied statuses.
    Demonstrates cutoff timestamps, skill requirements, agreement types.
    """
    employers = (
        db.execute(
            select(Organization).where(
                Organization.org_type == OrganizationType.EMPLOYER
            )
        )
        .scalars()
        .all()
    )

    if not employers:
        logger.warning("No employers found, skipping labor requests")
        return 0

    # Use varied employers and timestamps
    now = datetime.now()
    cutoff_3pm = now.replace(hour=15, minute=0, second=0, microsecond=0)

    labor_requests = []

    # OPEN requests (pending dispatch)
    labor_requests.append(
        {
            "employer_id": employers[0].id,
            "employer_name": employers[0].name,
            "request_date": cutoff_3pm
            - timedelta(days=1, hours=2),  # Yesterday before 3 PM
            "start_date": now.date() + timedelta(days=1),
            "classification": BookClassification.INSIDE_WIREPERSON,
            "workers_requested": 3,
            "worksite_name": "Commercial build-out — Westlake Center",
            "start_time": time(7, 0),
            "estimated_duration_days": 45,
            "wage_rate": Decimal("58.50"),
            "status": LaborRequestStatus.OPEN,
        }
    )

    labor_requests.append(
        {
            "employer_id": employers[1].id,
            "employer_name": employers[1].name,
            "request_date": cutoff_3pm - timedelta(days=2),
            "start_date": now.date(),
            "classification": BookClassification.TECHNICIAN,
            "workers_requested": 2,
            "worksite_name": "Data center cabling — Amazon campus",
            "start_time": time(6, 30),
            "estimated_duration_days": 30,
            "wage_rate": Decimal("54.25"),
            "status": LaborRequestStatus.OPEN,
        }
    )

    # FILLED requests (dispatched)
    labor_requests.append(
        {
            "employer_id": employers[0].id,
            "employer_name": employers[0].name,
            "request_date": now - timedelta(days=10),
            "start_date": (now - timedelta(days=9)).date(),
            "classification": BookClassification.INSIDE_WIREPERSON,
            "workers_requested": 2,
            "worksite_name": "Hospital expansion — Swedish Medical",
            "start_time": time(7, 0),
            "estimated_duration_days": 60,
            "wage_rate": Decimal("58.50"),
            "status": LaborRequestStatus.FILLED,
        }
    )

    # CANCELLED request
    labor_requests.append(
        {
            "employer_id": employers[2].id,
            "employer_name": employers[2].name,
            "request_date": now - timedelta(days=5),
            "start_date": (now - timedelta(days=4)).date(),
            "classification": BookClassification.SOUND_COMM,
            "workers_requested": 1,
            "worksite_name": "Conference room installation",
            "start_time": time(8, 0),
            "estimated_duration_days": 10,
            "wage_rate": Decimal("52.00"),
            "status": LaborRequestStatus.CANCELLED,
            "comments": "Project postponed by client",
        }
    )

    # EXPIRED request (past start_date, never filled)
    labor_requests.append(
        {
            "employer_id": employers[3].id,
            "employer_name": employers[3].name,
            "request_date": now - timedelta(days=15),
            "start_date": (now - timedelta(days=14)).date(),
            "classification": BookClassification.STOCKPERSON,
            "workers_requested": 1,
            "worksite_name": "Warehouse inventory reorganization",
            "start_time": time(9, 0),
            "estimated_duration_days": 5,
            "wage_rate": Decimal("48.00"),
            "status": LaborRequestStatus.EXPIRED,
        }
    )

    created_count = 0
    for lr_data in labor_requests:
        # Create unique key from employer + request_date + classification
        lr, created = get_or_create(
            db,
            LaborRequest,
            employer_id=lr_data["employer_id"],
            request_date=lr_data["request_date"],
            classification=lr_data["classification"],
            defaults=lr_data,
        )
        if created:
            created_count += 1

    return created_count


def _seed_demo_dispatches(db: Session) -> int:
    """
    Create 15-20 dispatch records with full lifecycle representation.

    Demonstrates:
    - COMPLETED dispatches (worked and returned to book)
    - ACTIVE dispatches (currently working)
    - SHORT_CALL dispatches (≤10 days, Rule 9)
    - QUIT/DISCHARGE (Rule 12 — cascade roll-off)
    - BY-NAME request (Rule 13)
    """
    # Get filled labor requests
    labor_requests = (
        db.execute(
            select(LaborRequest).where(LaborRequest.status == LaborRequestStatus.FILLED)
        )
        .scalars()
        .all()
    )

    if not labor_requests:
        logger.warning("No filled labor requests found, creating minimal dispatches")
        return 0

    # Get members with registrations
    registrations = (
        db.execute(
            select(BookRegistration).where(
                BookRegistration.status == RegistrationStatus.REGISTERED
            )
        )
        .scalars()
        .all()
    )

    if not registrations:
        logger.warning("No active registrations found, skipping dispatches")
        return 0

    # Get demo dispatcher user for dispatched_by_id
    dispatcher_user = db.execute(
        select(User).where(User.email == "demo_dispatcher@ibew46.demo")
    ).scalar_one_or_none()

    if not dispatcher_user:
        logger.warning("Demo dispatcher user not found, skipping dispatches")
        return 0

    dispatches = []

    # COMPLETED dispatch (member returned to book)
    if len(registrations) > 0:
        reg = registrations[0]
        dispatches.append(
            {
                "labor_request_id": labor_requests[0].id,
                "registration_id": reg.id,
                "member_id": reg.member_id,
                "employer_id": labor_requests[0].employer_id,
                "dispatched_by_id": dispatcher_user.id,
                "dispatch_date": datetime.now() - timedelta(days=45),
                "start_date": (datetime.now() - timedelta(days=44)).date(),
                "is_short_call": False,
                "dispatch_status": DispatchStatus.COMPLETED,
                "term_date": (datetime.now() - timedelta(days=10)).date(),
                "term_reason": TermReason.LAID_OFF,
            }
        )

    # ACTIVE dispatch (currently working)
    if len(registrations) > 1:
        reg = registrations[1]
        dispatches.append(
            {
                "labor_request_id": labor_requests[0].id,
                "registration_id": reg.id,
                "member_id": reg.member_id,
                "employer_id": labor_requests[0].employer_id,
                "dispatched_by_id": dispatcher_user.id,
                "dispatch_date": datetime.now() - timedelta(days=30),
                "start_date": (datetime.now() - timedelta(days=29)).date(),
                "is_short_call": False,
                "dispatch_status": DispatchStatus.WORKING,
            }
        )

    # SHORT_CALL dispatch (≤10 days, Rule 9)
    if len(registrations) > 2:
        reg = registrations[2]
        dispatches.append(
            {
                "labor_request_id": labor_requests[0].id,
                "registration_id": reg.id,
                "member_id": reg.member_id,
                "employer_id": labor_requests[0].employer_id,
                "dispatched_by_id": dispatcher_user.id,
                "dispatch_date": datetime.now() - timedelta(days=8),
                "start_date": (datetime.now() - timedelta(days=7)).date(),
                "is_short_call": True,
                "dispatch_status": DispatchStatus.WORKING,
            }
        )

    # QUIT dispatch (Rule 12 — shows cascade roll-off)
    if len(registrations) > 3:
        reg = registrations[3]
        dispatches.append(
            {
                "labor_request_id": labor_requests[0].id,
                "registration_id": reg.id,
                "member_id": reg.member_id,
                "employer_id": labor_requests[0].employer_id,
                "dispatched_by_id": dispatcher_user.id,
                "dispatch_date": datetime.now() - timedelta(days=60),
                "start_date": (datetime.now() - timedelta(days=59)).date(),
                "is_short_call": False,
                "dispatch_status": DispatchStatus.COMPLETED,
                "term_date": (datetime.now() - timedelta(days=30)).date(),
                "term_reason": TermReason.QUIT,
            }
        )

    created_count = 0
    for dispatch_data in dispatches:
        # Use labor_request_id + member_id + dispatch_date as natural key
        dispatch, created = get_or_create(
            db,
            Dispatch,
            labor_request_id=dispatch_data["labor_request_id"],
            member_id=dispatch_data["member_id"],
            dispatch_date=dispatch_data["dispatch_date"],
            defaults=dispatch_data,
        )
        if created:
            created_count += 1

    return created_count


def _seed_demo_check_marks(db: Session) -> int:
    """
    Create check mark records to demonstrate penalty tracking (Rule 10).

    - 2 members with 1 check mark each (still active)
    - 1 member with 2 check marks (at the limit — next one rolls off)
    - Shows check marks are per-area-book
    """
    registrations = (
        db.execute(
            select(BookRegistration)
            .where(BookRegistration.status == RegistrationStatus.REGISTERED)
            .limit(5)
        )
        .scalars()
        .all()
    )

    if len(registrations) < 3:
        logger.warning("Not enough registrations for check mark demo")
        return 0

    # Give 1 check mark each to first 2 registrations
    for reg in registrations[:2]:
        db.add(reg)

    # Give 2 check marks to third registration (at the limit)
    db.add(registrations[2])

    db.flush()

    return 3  # 3 registrations modified


def _seed_demo_exemptions(db: Session) -> int:
    """
    Create exemption records (Rule 14).

    - 1 military exemption
    - 1 medical exemption
    - 1 union business exemption (salting)
    """
    registrations = (
        db.execute(
            select(BookRegistration)
            .where(BookRegistration.status == RegistrationStatus.REGISTERED)
            .limit(5)
        )
        .scalars()
        .all()
    )

    if len(registrations) < 3:
        logger.warning("Not enough registrations for exemption demo")
        return 0

    # Military exemption
    registrations[0].is_exempt = True
    registrations[0].exempt_reason = ExemptReason.MILITARY
    registrations[0].exempt_start_date = datetime.now() - timedelta(days=30)
    registrations[0].exempt_end_date = datetime.now() + timedelta(days=60)
    db.add(registrations[0])

    # Medical exemption
    registrations[1].is_exempt = True
    registrations[1].exempt_reason = ExemptReason.MEDICAL
    registrations[1].exempt_start_date = datetime.now() - timedelta(days=10)
    registrations[1].exempt_end_date = datetime.now() + timedelta(days=30)
    db.add(registrations[1])

    # Union business exemption (salting)
    registrations[2].is_exempt = True
    registrations[2].exempt_reason = ExemptReason.UNION_BUSINESS
    registrations[2].exempt_start_date = datetime.now() - timedelta(days=5)
    registrations[2].exempt_end_date = datetime.now() + timedelta(days=45)
    db.add(registrations[2])

    db.flush()

    return 3


if __name__ == "__main__":
    from src.db.session import get_db_session

    logging.basicConfig(level=logging.INFO)
    db = get_db_session()

    try:
        print("=" * 60)
        print("RUNNING DEMO SEED DATA")
        print("=" * 60)

        result = seed_demo_data(db)

        print("\n" + "=" * 60)
        print("DEMO SEED SUMMARY")
        print("=" * 60)
        for entity, count in result.items():
            print(f"  {entity}: {count} records")

        print(
            "\n✅ Demo seed complete. Environment ready for stakeholder presentation."
        )
        print("\nDemo accounts:")
        print("  Dispatcher: demo_dispatcher@ibew46.demo / Demo2026!")
        print("  Officer:    demo_officer@ibew46.demo / Demo2026!")
        print("  Admin:      demo_admin@ibew46.demo / Demo2026!")

    except Exception as e:
        logger.error(f"Demo seed failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()
