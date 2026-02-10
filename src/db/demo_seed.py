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
import random
from datetime import datetime, timedelta, time, date
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
    Student,
    Cohort,
    Course,
    DuesPayment,
    DuesPeriod,
    DuesRate,
    FileAttachment,
    Grievance,
    BenevolenceApplication,
    SALTingActivity,
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
    StudentStatus,
    DuesPaymentMethod,
    DuesPaymentStatus,
    GrievanceStatus,
    GrievanceStep,
    BenevolenceStatus,
    BenevolenceReason,
    SALTingActivityType,
    SALTingOutcome,
)
from src.core.security import hash_password

logger = logging.getLogger(__name__)

# Name pools for generating realistic member/student names
FIRST_NAMES = [
    "James",
    "Mary",
    "John",
    "Patricia",
    "Robert",
    "Jennifer",
    "Michael",
    "Linda",
    "William",
    "Barbara",
    "David",
    "Elizabeth",
    "Richard",
    "Susan",
    "Joseph",
    "Jessica",
    "Thomas",
    "Sarah",
    "Charles",
    "Karen",
    "Christopher",
    "Nancy",
    "Daniel",
    "Lisa",
    "Matthew",
    "Betty",
    "Anthony",
    "Margaret",
    "Mark",
    "Sandra",
    "Donald",
    "Ashley",
    "Steven",
    "Kimberly",
    "Paul",
    "Emily",
    "Andrew",
    "Donna",
    "Joshua",
    "Michelle",
    "Kenneth",
    "Dorothy",
    "Kevin",
    "Carol",
    "Brian",
    "Amanda",
    "George",
    "Melissa",
    "Timothy",
    "Deborah",
    "Ronald",
    "Stephanie",
    "Edward",
    "Rebecca",
    "Jason",
    "Sharon",
    "Jeffrey",
    "Laura",
    "Ryan",
    "Cynthia",
    "Jacob",
    "Kathleen",
    "Gary",
    "Amy",
    "Nicholas",
    "Shirley",
    "Eric",
    "Angela",
    "Jonathan",
    "Helen",
    "Stephen",
    "Anna",
    "Larry",
    "Brenda",
    "Justin",
    "Pamela",
    "Scott",
    "Nicole",
    "Brandon",
    "Emma",
    "Benjamin",
    "Samantha",
    "Samuel",
    "Katherine",
    "Raymond",
    "Christine",
    "Gregory",
    "Debra",
    "Frank",
    "Rachel",
    "Alexander",
    "Catherine",
    "Patrick",
    "Carolyn",
    "Raymond",
    "Janet",
    "Jack",
    "Ruth",
    "Dennis",
    "Maria",
    "Jerry",
    "Heather",
    "Tyler",
    "Diane",
    "Aaron",
    "Virginia",
    "Jose",
    "Julie",
    "Adam",
    "Joyce",
    "Nathan",
    "Victoria",
    "Henry",
    "Olivia",
    "Douglas",
    "Kelly",
    "Zachary",
    "Christina",
    "Peter",
    "Lauren",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
    "Lee",
    "Perez",
    "Thompson",
    "White",
    "Harris",
    "Sanchez",
    "Clark",
    "Ramirez",
    "Lewis",
    "Robinson",
    "Walker",
    "Young",
    "Allen",
    "King",
    "Wright",
    "Scott",
    "Torres",
    "Nguyen",
    "Hill",
    "Flores",
    "Green",
    "Adams",
    "Nelson",
    "Baker",
    "Hall",
    "Rivera",
    "Campbell",
    "Mitchell",
    "Carter",
    "Roberts",
    "Gomez",
    "Phillips",
    "Evans",
    "Turner",
    "Diaz",
    "Parker",
    "Cruz",
    "Edwards",
    "Collins",
    "Reyes",
    "Stewart",
    "Morris",
    "Morales",
    "Murphy",
    "Cook",
    "Rogers",
    "Gutierrez",
    "Ortiz",
    "Morgan",
    "Cooper",
    "Peterson",
    "Bailey",
    "Reed",
    "Kelly",
    "Howard",
    "Ramos",
    "Kim",
    "Cox",
    "Ward",
    "Richardson",
    "Watson",
    "Brooks",
    "Chavez",
    "Wood",
    "James",
    "Bennett",
    "Gray",
    "Mendoza",
    "Ruiz",
    "Hughes",
    "Price",
    "Alvarez",
    "Castillo",
    "Sanders",
    "Patel",
    "Myers",
    "Long",
    "Ross",
    "Foster",
    "Jimenez",
    "Powell",
    "Jenkins",
    "Perry",
    "Russell",
]


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


def generate_person_name(index: int) -> tuple[str, str]:
    """Generate a unique first/last name combination using index."""
    first_idx = index % len(FIRST_NAMES)
    last_idx = (index // len(FIRST_NAMES)) % len(LAST_NAMES)

    # Add numeric suffix for uniqueness when we run out of combinations
    suffix_num = index // (len(FIRST_NAMES) * len(LAST_NAMES))

    first_name = FIRST_NAMES[first_idx]
    last_name = LAST_NAMES[last_idx]

    if suffix_num > 0:
        last_name = f"{last_name}{suffix_num}"

    return first_name, last_name


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

    # Phase 10: Cohorts (100 total)
    summary["cohorts"] = _seed_demo_cohorts(db)

    # Phase 11: Students (1000 total)
    summary["students"] = _seed_demo_students(db)

    # Phase 12: Dues periods and rates
    summary["dues_setup"] = _seed_demo_dues_setup(db)

    # Phase 13: Dues payments ($500k monthly collected)
    summary["dues_payments"] = _seed_demo_dues_payments(db)

    # Phase 14: Delinquent dues ($10k overdue)
    summary["delinquent_dues"] = _seed_demo_delinquent_dues(db)

    # Phase 15: File attachments (10,000 total)
    summary["attachments"] = _seed_demo_attachments(db)

    # Phase 16: Grievances (10 total in various states)
    summary["grievances"] = _seed_demo_grievances(db)

    # Phase 17: Benevolence applications (20 total in various states)
    summary["benevolence"] = _seed_demo_benevolence(db)

    # Phase 18: SALTing activities (15 total tied to existing members)
    summary["salting"] = _seed_demo_salting(db)

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
    Create 2000 members with varied classifications.
    Use realistic generated names for union electricians.
    Mix of active, inactive, and suspended statuses.
    """
    # Classification distribution (realistic mix)
    classifications = [
        (MemberClassification.JOURNEYMAN, 0.70),  # 70% journeyman
        (MemberClassification.APPRENTICE_3RD_YEAR, 0.15),  # 15% apprentice (3rd year)
        (MemberClassification.FOREMAN, 0.15),  # 15% foreman
    ]

    # Status distribution
    statuses = [
        (MemberStatus.ACTIVE, 0.85),  # 85% active
        (MemberStatus.INACTIVE, 0.10),  # 10% inactive
        (MemberStatus.SUSPENDED, 0.05),  # 5% suspended
    ]

    total_members = 2000
    created_count = 0

    logger.info(f"  Creating {total_members} members...")

    for i in range(total_members):
        first_name, last_name = generate_person_name(i)

        # Determine classification based on distribution
        rand_class = random.random()
        cum_prob = 0
        classification = MemberClassification.JOURNEYMAN
        for cls, prob in classifications:
            cum_prob += prob
            if rand_class <= cum_prob:
                classification = cls
                break

        # Determine status based on distribution
        rand_status = random.random()
        cum_prob = 0
        status = MemberStatus.ACTIVE
        for st, prob in statuses:
            cum_prob += prob
            if rand_status <= cum_prob:
                status = st
                break

        email = f"{first_name.lower()}.{last_name.lower()}{i}@ibew46.org"
        member_number = f"{46000 + i:06d}"  # 046000, 046001, etc.

        member_data = {
            "member_number": member_number,
            "first_name": first_name,
            "last_name": last_name,
            "classification": classification,
            "status": status,
            "email": email,
            "phone": f"206-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
            "address": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Cedar', 'Pine'])} St",
            "city": random.choice(
                ["Seattle", "Tacoma", "Bellevue", "Everett", "Renton", "Kent"]
            ),
            "state": "WA",
            "zip_code": f"98{random.randint(100, 199)}",
        }

        member, created = get_or_create(
            db, Member, member_number=member_number, defaults=member_data
        )
        if created:
            created_count += 1

        # Log progress every 500 members
        if (i + 1) % 500 == 0:
            logger.info(f"    Created {i + 1}/{total_members} members...")

    logger.info(f"  Completed: {created_count} new members created")
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


def _seed_demo_cohorts(db: Session) -> int:
    """
    Create 100 cohorts with varied start dates and statuses.
    Mix of active, completed, and upcoming cohorts.
    """
    # Get or create a default course
    course, _ = get_or_create(
        db,
        Course,
        code="ELEC101",
        defaults={
            "code": "ELEC101",
            "name": "Electrical Fundamentals",
            "description": "Core electrical training program",
            "hours": 40,
        },
    )

    total_cohorts = 100
    created_count = 0

    logger.info(f"  Creating {total_cohorts} cohorts...")

    base_date = datetime.now() - timedelta(days=365 * 3)  # Start 3 years ago

    for i in range(total_cohorts):
        cohort_number = (
            f"C{2022 + (i // 25)}-{(i % 25) + 1:02d}"  # C2022-01, C2022-02, etc.
        )
        start_date = base_date + timedelta(
            days=i * 30
        )  # Each cohort starts ~30 days apart
        end_date = start_date + timedelta(days=180)  # 6-month programs

        cohort_data = {
            "code": cohort_number,
            "name": f"Cohort {cohort_number}",
            "start_date": start_date.date(),
            "end_date": end_date.date(),
            "max_students": random.randint(15, 25),
        }

        cohort, created = get_or_create(
            db, Cohort, code=cohort_number, defaults=cohort_data
        )
        if created:
            created_count += 1

    logger.info(f"  Completed: {created_count} new cohorts created")
    return created_count


def _seed_demo_students(db: Session) -> int:
    """
    Create 1000 students enrolled in cohorts.
    Mix of active, completed, and withdrawn students.
    """
    # Get all cohorts
    cohorts = db.execute(select(Cohort)).scalars().all()

    if not cohorts:
        logger.warning("No cohorts found, skipping student creation")
        return 0

    total_students = 1000
    created_count = 0

    logger.info(f"  Creating {total_students} students...")

    # Student status distribution
    statuses = [
        (StudentStatus.ENROLLED, 0.30),  # 30% currently enrolled
        (StudentStatus.COMPLETED, 0.60),  # 60% completed
        (StudentStatus.DROPPED, 0.10),  # 10% dropped
    ]

    for i in range(total_students):
        first_name, last_name = generate_person_name(i + 10000)  # Offset from members

        # Determine status
        rand_status = random.random()
        cum_prob = 0
        status = StudentStatus.ENROLLED
        for st, prob in statuses:
            cum_prob += prob
            if rand_status <= cum_prob:
                status = st
                break

        email = f"{first_name.lower()}.{last_name.lower()}{i}@student.ibew46.org"
        student_number = f"S{46000 + i:05d}"
        member_number = f"M{46000 + i:05d}"  # Unique member number for student
        phone = f"206-{random.randint(200, 999)}-{random.randint(1000, 9999)}"

        # Assign to a cohort
        cohort = random.choice(cohorts)

        # Step 1: Create Member first (Student requires member_id FK)
        member_data = {
            "member_number": member_number,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "classification": MemberClassification.APPRENTICE_1ST_YEAR,
            "status": MemberStatus.ACTIVE,
        }
        member, _ = get_or_create(
            db, Member, member_number=member_number, defaults=member_data
        )

        # Step 2: Create Student linked to Member
        application_date = cohort.start_date - timedelta(
            days=30
        )  # Applied 30 days before enrollment
        student_data = {
            "member_id": member.id,  # Link to Member (provides name/email/phone)
            "student_number": student_number,
            "status": status,
            "application_date": application_date,
            "enrollment_date": cohort.start_date,
            "cohort": cohort.code,  # String field, not FK
        }

        student, created = get_or_create(
            db, Student, student_number=student_number, defaults=student_data
        )
        if created:
            created_count += 1

        # Log progress every 250 students
        if (i + 1) % 250 == 0:
            logger.info(f"    Created {i + 1}/{total_students} students...")

    logger.info(f"  Completed: {created_count} new students created")
    return created_count


def _seed_demo_dues_setup(db: Session) -> int:
    """
    Create dues periods and rates for the past 12 months.
    Required for dues payment seeding.
    """
    # Create default dues rates for each classification
    # DuesRate uses (classification, effective_date) as unique key
    created_count = 0
    effective_date = date(2026, 1, 1)

    # Standard rates by classification
    rates_config = [
        (MemberClassification.JOURNEYMAN, Decimal("75.00"), "Journeyman standard rate"),
        (MemberClassification.FOREMAN, Decimal("85.00"), "Foreman standard rate"),
        (
            MemberClassification.APPRENTICE_1ST_YEAR,
            Decimal("30.00"),
            "1st year apprentice rate",
        ),
        (
            MemberClassification.APPRENTICE_2ND_YEAR,
            Decimal("40.00"),
            "2nd year apprentice rate",
        ),
        (
            MemberClassification.APPRENTICE_3RD_YEAR,
            Decimal("50.00"),
            "3rd year apprentice rate",
        ),
        (
            MemberClassification.APPRENTICE_4TH_YEAR,
            Decimal("60.00"),
            "4th year apprentice rate",
        ),
        (
            MemberClassification.APPRENTICE_5TH_YEAR,
            Decimal("70.00"),
            "5th year apprentice rate",
        ),
    ]

    for classification, monthly_amount, description in rates_config:
        rate, rate_created = get_or_create(
            db,
            DuesRate,
            classification=classification,
            effective_date=effective_date,
            defaults={
                "monthly_amount": monthly_amount,
                "description": description,
                # end_date is NULL (currently active)
            },
        )
        if rate_created:
            created_count += 1

    # Create periods for the past 12 months
    periods_created = 0
    current_date = datetime.now()
    base_year = current_date.year
    base_month = current_date.month

    for i in range(12):
        # Calculate month/year going backwards
        month = ((base_month - i - 1) % 12) + 1
        year = base_year if (base_month - i) > 0 else base_year - 1

        # Calculate due date (5th of the month) and grace period (15th)
        due_date_val = date(year, month, 5)
        grace_period_end_val = date(year, month, 15)

        period_data = {
            "period_year": year,
            "period_month": month,
            "due_date": due_date_val,
            "grace_period_end": grace_period_end_val,
            "is_closed": True if i > 0 else False,  # Current month is open
            # period_name is a @property, not a database field
        }

        period, created = get_or_create(
            db,
            DuesPeriod,
            period_year=year,
            period_month=month,
            defaults=period_data,
        )
        if created:
            periods_created += 1

    total_created = created_count + periods_created  # rates + periods
    logger.info(
        f"  Created {total_created} dues setup records ({created_count} rates + {periods_created} periods)"
    )
    return total_created


def _seed_demo_dues_payments(db: Session) -> int:
    """
    Create dues payments totaling ~$500,000 for the current month.
    Distribute across members with varied payment methods.
    """
    # Get current period
    current_date = datetime.now()
    current_period = db.execute(
        select(DuesPeriod).where(
            DuesPeriod.year == current_date.year,
            DuesPeriod.month == current_date.month,
        )
    ).scalar_one_or_none()

    if not current_period:
        logger.warning("No current dues period found, skipping payments")
        return 0

    # Get default rate
    rate = db.execute(select(DuesRate).where(DuesRate.is_active)).scalars().first()

    if not rate:
        logger.warning("No active dues rate found, skipping payments")
        return 0

    # Get active members
    members = (
        db.execute(select(Member).where(Member.status == MemberStatus.ACTIVE))
        .scalars()
        .all()
    )

    if not members:
        logger.warning("No active members found, skipping payments")
        return 0

    target_amount = Decimal("500000.00")
    payment_amount = rate.monthly_amount
    num_payments = min(int(target_amount / payment_amount), len(members))

    logger.info(f"  Creating {num_payments} dues payments totaling ${target_amount}...")

    # Payment method distribution
    methods = [
        (DuesPaymentMethod.CHECK, 0.30),
        (DuesPaymentMethod.CASH, 0.10),
        (DuesPaymentMethod.CREDIT_CARD, 0.40),
        (DuesPaymentMethod.BANK_TRANSFER, 0.20),
    ]

    created_count = 0
    selected_members = random.sample(members, num_payments)

    for i, member in enumerate(selected_members):
        # Determine payment method
        rand_method = random.random()
        cum_prob = 0
        method = DuesPaymentMethod.CHECK
        for meth, prob in methods:
            cum_prob += prob
            if rand_method <= cum_prob:
                method = meth
                break

        payment_data = {
            "member_id": member.id,
            "period_id": current_period.id,
            "rate_id": rate.id,
            "amount_due": payment_amount,
            "amount_paid": payment_amount,
            "payment_date": current_date.date(),
            "payment_method": method,
            "payment_status": DuesPaymentStatus.PAID,
        }

        payment, created = get_or_create(
            db,
            DuesPayment,
            member_id=member.id,
            period_id=current_period.id,
            defaults=payment_data,
        )
        if created:
            created_count += 1

    total_collected = created_count * payment_amount
    logger.info(f"  Completed: {created_count} payments, ${total_collected} collected")
    return created_count


def _seed_demo_delinquent_dues(db: Session) -> int:
    """
    Create delinquent dues payments totaling ~$10,000.
    These are unpaid or partially paid for previous periods.
    """
    # Get a previous period (2 months ago)
    current_date = datetime.now()
    prev_month = ((current_date.month - 3) % 12) + 1
    prev_year = (
        current_date.year if (current_date.month - 3) > 0 else current_date.year - 1
    )

    prev_period = db.execute(
        select(DuesPeriod).where(
            DuesPeriod.year == prev_year,
            DuesPeriod.month == prev_month,
        )
    ).scalar_one_or_none()

    if not prev_period:
        logger.warning("No previous period found, skipping delinquent dues")
        return 0

    # Get default rate
    rate = db.execute(select(DuesRate).where(DuesRate.is_active)).scalars().first()

    if not rate:
        return 0

    # Get active members
    members = (
        db.execute(select(Member).where(Member.status == MemberStatus.ACTIVE))
        .scalars()
        .all()
    )

    target_amount = Decimal("10000.00")
    payment_amount = rate.monthly_amount
    num_delinquent = min(int(target_amount / payment_amount), 200)  # Cap at 200 members

    logger.info(
        f"  Creating {num_delinquent} delinquent dues records totaling ${target_amount}..."
    )

    created_count = 0
    selected_members = random.sample(members, num_delinquent)

    for member in selected_members:
        payment_data = {
            "member_id": member.id,
            "period_id": prev_period.id,
            "rate_id": rate.id,
            "amount_due": payment_amount,
            "amount_paid": Decimal("0.00"),
            "payment_status": DuesPaymentStatus.PENDING,
        }

        payment, created = get_or_create(
            db,
            DuesPayment,
            member_id=member.id,
            period_id=prev_period.id,
            defaults=payment_data,
        )
        if created:
            created_count += 1

    total_delinquent = created_count * payment_amount
    logger.info(
        f"  Completed: {created_count} delinquent records, ${total_delinquent} overdue"
    )
    return created_count


def _seed_demo_attachments(db: Session) -> int:
    """
    Create 10,000 file attachment records for members and students.
    Mix of documents, certifications, and photos.
    """
    # Get all members and students
    members = db.execute(select(Member)).scalars().all()
    students = db.execute(select(Student)).scalars().all()

    if not members and not students:
        logger.warning("No members or students found, skipping attachments")
        return 0

    total_attachments = 10000
    created_count = 0

    logger.info(f"  Creating {total_attachments} file attachments...")

    # Attachment type distribution (file_category values)
    types = [
        ("documents", 0.40),
        ("certifications", 0.30),
        ("photos", 0.20),
        ("general", 0.10),
    ]

    # File extensions by type
    extensions = {
        "documents": [".pdf", ".docx", ".doc"],
        "certifications": [".pdf", ".jpg"],
        "photos": [".jpg", ".png"],
        "general": [".pdf", ".txt", ".xlsx"],
    }

    for i in range(total_attachments):
        # Randomly choose member or student (70% members, 30% students)
        if random.random() < 0.7 and members:
            entity = random.choice(members)
            entity_type = "Member"
            entity_id = entity.id
        elif students:
            entity = random.choice(students)
            entity_type = "Student"
            entity_id = entity.id
        else:
            continue

        # Determine attachment type
        rand_type = random.random()
        cum_prob = 0
        att_type = "documents"
        for typ, prob in types:
            cum_prob += prob
            if rand_type <= cum_prob:
                att_type = typ
                break

        # Generate filename
        extension = random.choice(extensions[att_type])
        filename = f"{entity_type.lower()}_{entity_id}_doc_{i}{extension}"

        # Random file size (10KB to 5MB)
        file_size = random.randint(10240, 5242880)

        # Map extension to MIME type
        mime_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".jpg": "image/jpeg",
            ".png": "image/png",
            ".txt": "text/plain",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        mime_type = mime_types.get(extension, "application/octet-stream")

        attachment_data = {
            "record_type": entity_type.lower(),  # "member" or "student"
            "record_id": entity_id,
            "file_category": att_type,  # "documents", "certifications", etc.
            "file_name": filename,
            "file_path": f"/uploads/{entity_type.lower()}s/{entity_id}/{filename}",  # Required field
            "file_type": mime_type,  # MIME type (e.g., "application/pdf")
            "file_size": file_size,
            # created_at is auto-set by TimestampMixin
        }

        attachment, created = get_or_create(
            db,
            FileAttachment,
            filename=filename,
            entity_type=entity_type,
            entity_id=entity_id,
            defaults=attachment_data,
        )
        if created:
            created_count += 1

        # Log progress every 2000 attachments
        if (i + 1) % 2000 == 0:
            logger.info(f"    Created {i + 1}/{total_attachments} attachments...")

    logger.info(f"  Completed: {created_count} new attachments created")
    return created_count


def _seed_demo_grievances(db: Session) -> int:
    """
    Create 10 grievances in various states.
    Mix of open, settled, withdrawn, and arbitration cases.
    """
    # Get active members and employers
    members = (
        db.execute(select(Member).where(Member.status == MemberStatus.ACTIVE).limit(10))
        .scalars()
        .all()
    )
    employers = db.execute(select(Organization).limit(6)).scalars().all()

    if not members or not employers:
        logger.warning("No members or employers found, skipping grievances")
        return 0

    total_grievances = 10
    created_count = 0

    logger.info(f"  Creating {total_grievances} grievances...")

    # Grievance status distribution
    statuses = [
        (GrievanceStatus.OPEN, 3),  # 3 open
        (GrievanceStatus.INVESTIGATION, 2),  # 2 under investigation
        (GrievanceStatus.HEARING, 1),  # 1 at hearing
        (GrievanceStatus.SETTLED, 2),  # 2 settled
        (GrievanceStatus.WITHDRAWN, 1),  # 1 withdrawn
        (GrievanceStatus.ARBITRATION, 1),  # 1 arbitration
    ]

    # Contract articles commonly violated
    contract_articles = [
        "Article 3 - Union Security",
        "Article 7 - Hours of Work",
        "Article 8 - Overtime",
        "Article 11 - Wages",
        "Article 12 - Working Conditions",
        "Article 15 - Seniority",
    ]

    grievance_num = 1
    for status, count in statuses:
        for i in range(count):
            member = random.choice(members)
            employer = random.choice(employers)

            # Calculate dates based on status
            base_date = datetime.now() - timedelta(days=random.randint(30, 180))
            filed_date = base_date.date()
            incident_date = (base_date - timedelta(days=random.randint(1, 30))).date()

            grievance_data = {
                "grievance_number": f"GRV-2026-{grievance_num:03d}",
                "member_id": member.id,
                "employer_id": employer.id,
                "filed_date": filed_date,
                "incident_date": incident_date,
                "contract_article": random.choice(contract_articles),
                "violation_description": f"Alleged violation of contract terms by employer. {random.choice(['Improper termination', 'Wage discrepancy', 'Safety violation', 'Overtime dispute'])}.",
                "remedy_sought": random.choice(
                    [
                        "Reinstatement with back pay",
                        "Wage adjustment and compensation",
                        "Safety improvements and training",
                        "Policy clarification and compliance",
                    ]
                ),
                "current_step": GrievanceStep.STEP_1
                if status == GrievanceStatus.OPEN
                else random.choice(
                    [
                        GrievanceStep.STEP_2,
                        GrievanceStep.STEP_3,
                        GrievanceStep.ARBITRATION,
                    ]
                ),
                "status": status,
                "assigned_rep": random.choice(
                    [
                        "John Smith (Business Rep)",
                        "Sarah Johnson (Organizer)",
                        "Michael Brown (Officer)",
                    ]
                ),
            }

            # Add resolution details for settled cases
            if status in [GrievanceStatus.SETTLED, GrievanceStatus.WITHDRAWN]:
                grievance_data["resolution_date"] = (
                    base_date + timedelta(days=random.randint(30, 90))
                ).date()
                if status == GrievanceStatus.SETTLED:
                    grievance_data["settlement_amount"] = Decimal(
                        str(random.randint(500, 5000))
                    )
                    grievance_data["resolution"] = (
                        "Parties reached mutual agreement. Employer agreed to remedy."
                    )

            grievance, created = get_or_create(
                db,
                Grievance,
                grievance_number=grievance_data["grievance_number"],
                defaults=grievance_data,
            )
            if created:
                created_count += 1

            grievance_num += 1

    logger.info(f"  Completed: {created_count} new grievances created")
    return created_count


def _seed_demo_benevolence(db: Session) -> int:
    """
    Create 20 benevolence applications in various states.
    Mix of draft, submitted, approved, denied, and paid applications.
    """
    # Get active members
    members = (
        db.execute(select(Member).where(Member.status == MemberStatus.ACTIVE).limit(20))
        .scalars()
        .all()
    )

    if not members:
        logger.warning("No active members found, skipping benevolence applications")
        return 0

    total_applications = 20
    created_count = 0

    logger.info(f"  Creating {total_applications} benevolence applications...")

    # Status distribution
    statuses = [
        (BenevolenceStatus.DRAFT, 2),  # 2 drafts
        (BenevolenceStatus.SUBMITTED, 4),  # 4 submitted
        (BenevolenceStatus.UNDER_REVIEW, 3),  # 3 under review
        (BenevolenceStatus.APPROVED, 5),  # 5 approved
        (BenevolenceStatus.DENIED, 3),  # 3 denied
        (BenevolenceStatus.PAID, 3),  # 3 paid
    ]

    # Reason distribution
    reasons = [
        BenevolenceReason.MEDICAL,
        BenevolenceReason.DEATH_IN_FAMILY,
        BenevolenceReason.HARDSHIP,
        BenevolenceReason.DISASTER,
        BenevolenceReason.OTHER,
    ]

    app_num = 1
    member_index = 0

    for status, count in statuses:
        for i in range(count):
            member = members[member_index % len(members)]
            member_index += 1

            # Calculate dates based on status
            base_date = datetime.now() - timedelta(days=random.randint(30, 120))
            application_date = base_date.date()

            reason = random.choice(reasons)
            amount_requested = Decimal(str(random.randint(500, 5000)))

            application_data = {
                "member_id": member.id,
                "application_date": application_date,
                "reason": reason,
                "description": f"Request for financial assistance due to {reason.value.replace('_', ' ')}. {random.choice(['Unexpected medical expenses', 'Family emergency', 'Financial hardship', 'Recovery from disaster'])}.",
                "amount_requested": amount_requested,
                "status": status,
            }

            # Add approval/payment details for approved and paid applications
            if status in [
                BenevolenceStatus.APPROVED,
                BenevolenceStatus.PAID,
            ]:
                # Approved amount is typically 50-100% of requested
                approval_percentage = random.uniform(0.5, 1.0)
                application_data["approved_amount"] = Decimal(
                    str(int(amount_requested * approval_percentage))
                )

            if status == BenevolenceStatus.PAID:
                application_data["payment_date"] = (
                    base_date + timedelta(days=random.randint(14, 45))
                ).date()
                application_data["payment_method"] = random.choice(
                    ["Check", "Direct Deposit", "Wire Transfer"]
                )

            # Create unique key (member can have multiple applications)
            benevolence, created = get_or_create(
                db,
                BenevolenceApplication,
                member_id=member.id,
                application_date=application_date,
                defaults=application_data,
            )
            if created:
                created_count += 1

            app_num += 1

    logger.info(f"  Completed: {created_count} new benevolence applications created")
    return created_count


def _seed_demo_salting(db: Session) -> int:
    """
    Create 15 SALTing/organizing activities tied to existing members.
    Mix of activity types and outcomes at non-union employers.
    """
    # Get active members
    members = (
        db.execute(select(Member).where(Member.status == MemberStatus.ACTIVE).limit(10))
        .scalars()
        .all()
    )

    if not members:
        logger.warning("No active members found, skipping SALTing activities")
        return 0

    # Get non-union employers (OrganizationType.EMPLOYER)
    employers = (
        db.execute(
            select(Organization)
            .where(Organization.organization_type == OrganizationType.EMPLOYER)
            .limit(8)
        )
        .scalars()
        .all()
    )

    if not employers:
        logger.warning("No employers found, skipping SALTing activities")
        return 0

    total_activities = 15
    created_count = 0

    logger.info(f"  Creating {total_activities} SALTing activities...")

    # Activity type distribution with outcomes
    activities_config = [
        # Early outreach activities
        (SALTingActivityType.OUTREACH, SALTingOutcome.POSITIVE, 2, 0),
        (SALTingActivityType.SITE_VISIT, SALTingOutcome.NEUTRAL, 0, 0),
        (SALTingActivityType.LEAFLETING, SALTingOutcome.POSITIVE, 5, 0),
        # Deeper engagement
        (SALTingActivityType.ONE_ON_ONE, SALTingOutcome.POSITIVE, 8, 2),
        (SALTingActivityType.ONE_ON_ONE, SALTingOutcome.NEGATIVE, 3, 0),
        (SALTingActivityType.MEETING, SALTingOutcome.POSITIVE, 12, 4),
        # Advanced organizing
        (SALTingActivityType.INFORMATION_SESSION, SALTingOutcome.POSITIVE, 15, 8),
        (SALTingActivityType.CARD_SIGNING, SALTingOutcome.POSITIVE, 10, 10),
        (SALTingActivityType.PETITION_DRIVE, SALTingOutcome.POSITIVE, 8, 5),
        # Mixed outcomes
        (SALTingActivityType.OUTREACH, SALTingOutcome.NO_CONTACT, 0, 0),
        (SALTingActivityType.SITE_VISIT, SALTingOutcome.NEGATIVE, 2, 0),
        (SALTingActivityType.ONE_ON_ONE, SALTingOutcome.NEUTRAL, 4, 1),
        # Successful follow-ups
        (SALTingActivityType.MEETING, SALTingOutcome.POSITIVE, 18, 12),
        (SALTingActivityType.CARD_SIGNING, SALTingOutcome.POSITIVE, 15, 15),
        (SALTingActivityType.INFORMATION_SESSION, SALTingOutcome.POSITIVE, 20, 15),
    ]

    for idx, (activity_type, outcome, workers_contacted, cards_signed) in enumerate(
        activities_config
    ):
        member = members[idx % len(members)]
        employer = employers[idx % len(employers)]

        # Calculate activity date (spread over past 90 days)
        activity_date = (datetime.now() - timedelta(days=random.randint(1, 90))).date()

        # Build description based on activity type
        descriptions = {
            SALTingActivityType.OUTREACH: f"Initial contact with workers at {employer.name}. Distributed union information and contact cards.",
            SALTingActivityType.SITE_VISIT: f"Site visit to {employer.name} worksite. Observed working conditions and made initial assessments.",
            SALTingActivityType.LEAFLETING: f"Distributed informational leaflets to workers at {employer.name} during shift change.",
            SALTingActivityType.ONE_ON_ONE: f"One-on-one conversation with {employer.name} worker about union benefits and organizing campaign.",
            SALTingActivityType.MEETING: f"Organizing meeting with interested workers from {employer.name}. Discussed next steps and addressed concerns.",
            SALTingActivityType.INFORMATION_SESSION: f"Formal information session for {employer.name} workers. Covered union benefits, rights, and organizing process.",
            SALTingActivityType.CARD_SIGNING: f"Authorization card signing event for {employer.name} workers. Progress toward representation election.",
            SALTingActivityType.PETITION_DRIVE: f"Petition drive at {employer.name} for improved working conditions and safety standards.",
            SALTingActivityType.OTHER: f"Follow-up activity with {employer.name} workers. Maintained momentum and addressed questions.",
        }

        activity_data = {
            "member_id": member.id,
            "organization_id": employer.id,
            "activity_type": activity_type,
            "activity_date": activity_date,
            "outcome": outcome,
            "location": f"{employer.name} worksite",
            "workers_contacted": workers_contacted,
            "cards_signed": cards_signed,
            "description": descriptions.get(
                activity_type, f"SALTing activity at {employer.name}"
            ),
            "notes": f"Outcome: {outcome.value.replace('_', ' ').title()}. {'Strong interest from workers.' if outcome == SALTingOutcome.POSITIVE else 'Follow-up needed.' if outcome == SALTingOutcome.NEUTRAL else 'Encountered resistance.' if outcome == SALTingOutcome.NEGATIVE else 'Unable to make contact.'}",
        }

        # Create unique key (member can have multiple activities at same employer)
        salting, created = get_or_create(
            db,
            SALTingActivity,
            member_id=member.id,
            organization_id=employer.id,
            activity_date=activity_date,
            defaults=activity_data,
        )
        if created:
            created_count += 1

    logger.info(f"  Completed: {created_count} new SALTing activities created")
    return created_count


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
