"""Seed students data - creates students linked to members."""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from faker import Faker

from src.models.student import Student
from src.models.member import Member
from src.db.enums import StudentStatus, MemberStatus, MemberClassification
from .base_seed import add_records

fake = Faker()


def seed_students(db: Session, count: int = 500):
    """
    Seed students linked to member records.

    Students are linked to Members. This function creates new members
    for students who need them (apprentice classifications).
    """
    students = []

    # Get existing members without student records that could be students
    # (apprentices are typically students)
    existing_members = (
        db.query(Member)
        .filter(Member.student == None)  # noqa: E711
        .filter(Member.deleted_at == None)  # noqa: E711
        .filter(Member.classification.in_([
            MemberClassification.APPRENTICE_1ST_YEAR,
            MemberClassification.APPRENTICE_2ND_YEAR,
            MemberClassification.APPRENTICE_3RD_YEAR,
            MemberClassification.APPRENTICE_4TH_YEAR,
            MemberClassification.APPRENTICE_5TH_YEAR,
        ]))
        .limit(count)
        .all()
    )

    # Use existing apprentice members first
    members_to_use = list(existing_members)

    # If we need more, create new members
    members_needed = count - len(members_to_use)
    if members_needed > 0:
        new_members = []
        apprentice_classifications = [
            MemberClassification.APPRENTICE_1ST_YEAR,
            MemberClassification.APPRENTICE_2ND_YEAR,
            MemberClassification.APPRENTICE_3RD_YEAR,
            MemberClassification.APPRENTICE_4TH_YEAR,
            MemberClassification.APPRENTICE_5TH_YEAR,
        ]

        for i in range(members_needed):
            member_number = f"S{fake.random_int(min=100000, max=999999)}"
            classification = fake.random_element(apprentice_classifications)

            member = Member(
                member_number=member_number,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                phone=fake.phone_number()[:50],
                address=fake.street_address(),
                city=fake.city(),
                state=fake.state_abbr(),
                zip_code=fake.zipcode(),
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=35),
                status=MemberStatus.ACTIVE,
                classification=classification,
            )
            new_members.append(member)

        if new_members:
            add_records(db, new_members)
            db.flush()  # Ensure IDs are assigned
            members_to_use.extend(new_members)

    # Create student records
    statuses = [
        StudentStatus.APPLICANT,
        StudentStatus.ENROLLED,
        StudentStatus.ENROLLED,
        StudentStatus.ENROLLED,  # Weight toward enrolled
        StudentStatus.ON_LEAVE,
        StudentStatus.COMPLETED,
        StudentStatus.DROPPED,
    ]

    cohorts = [
        "2024-Fall",
        "2024-Spring",
        "2025-Fall",
        "2025-Spring",
        "2026-Spring",
    ]

    for i, member in enumerate(members_to_use[:count]):
        application_date = fake.date_between(start_date="-2y", end_date="today")
        status = fake.random_element(statuses)

        # Set dates based on status
        enrollment_date = None
        expected_completion = None
        actual_completion = None

        if status in [StudentStatus.ENROLLED, StudentStatus.ON_LEAVE, StudentStatus.COMPLETED]:
            enrollment_date = application_date + timedelta(days=fake.random_int(min=7, max=60))
            expected_completion = enrollment_date + timedelta(days=365 * 5)  # 5 year program

            if status == StudentStatus.COMPLETED:
                actual_completion = enrollment_date + timedelta(
                    days=fake.random_int(min=365*4, max=365*6)
                )

        student = Student(
            member_id=member.id,
            student_number=f"STU{100000 + i}",
            status=status,
            application_date=application_date,
            enrollment_date=enrollment_date,
            expected_completion_date=expected_completion,
            actual_completion_date=actual_completion,
            cohort=fake.random_element(cohorts) if enrollment_date else None,
            emergency_contact_name=fake.name() if fake.boolean(chance_of_getting_true=70) else None,
            emergency_contact_phone=fake.phone_number()[:20] if fake.boolean(chance_of_getting_true=70) else None,
            emergency_contact_relationship=fake.random_element(["Parent", "Spouse", "Sibling", "Friend"]) if fake.boolean(chance_of_getting_true=70) else None,
            notes=fake.sentence() if fake.boolean(chance_of_getting_true=20) else None,
        )
        students.append(student)

    if students:
        add_records(db, students)

    print(f"Seeded {len(students)} students.")
    return students
