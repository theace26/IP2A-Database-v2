"""Seed data for Phase 2 Training System."""

import random
from datetime import date, time, timedelta
from sqlalchemy.orm import Session

from src.models.member import Member
from src.models.student import Student
from src.models.course import Course
from src.models.class_session import ClassSession
from src.models.enrollment import Enrollment
from src.models.attendance import Attendance
from src.models.grade import Grade
from src.models.certification import Certification
from src.db.enums import (
    StudentStatus,
    CourseType,
    CourseEnrollmentStatus,
    SessionAttendanceStatus,
    GradeType,
    CertificationType,
    CertificationStatus,
)


def seed_courses(db: Session) -> list[Course]:
    """Create default courses for the training program."""
    print("  Creating courses...")

    courses_data = [
        {
            "code": "ELEC101",
            "name": "Electrical Fundamentals",
            "description": "Basic electrical theory and safety",
            "course_type": CourseType.CORE,
            "credits": 3.0,
            "hours": 60,
            "is_required": True,
            "passing_grade": 70.0,
        },
        {
            "code": "SAFE100",
            "name": "OSHA 10-Hour Construction Safety",
            "description": "Required OSHA safety certification",
            "course_type": CourseType.CERTIFICATION,
            "credits": 1.0,
            "hours": 10,
            "is_required": True,
            "passing_grade": 80.0,
        },
        {
            "code": "MATH101",
            "name": "Trade Mathematics",
            "description": "Math for electrical work: fractions, decimals, geometry",
            "course_type": CourseType.CORE,
            "credits": 2.0,
            "hours": 40,
            "is_required": True,
            "passing_grade": 70.0,
            "prerequisites": None,
        },
        {
            "code": "CODE101",
            "name": "National Electrical Code",
            "description": "Introduction to NEC requirements",
            "course_type": CourseType.CORE,
            "credits": 3.0,
            "hours": 60,
            "is_required": True,
            "passing_grade": 75.0,
            "prerequisites": "ELEC101",
        },
        {
            "code": "TOOL100",
            "name": "Tools and Equipment",
            "description": "Proper use of electrical tools and equipment",
            "course_type": CourseType.CORE,
            "credits": 2.0,
            "hours": 40,
            "is_required": True,
            "passing_grade": 70.0,
        },
    ]

    courses = []
    for data in courses_data:
        course = Course(**data)
        db.add(course)
        courses.append(course)

    db.commit()
    print(f"    ✓ Created {len(courses)} courses")
    return courses


def seed_students(db: Session, num_students: int = 20) -> list[Student]:
    """Create students from existing members."""
    print(f"  Creating {num_students} students...")

    # Get random members to convert to students
    members = db.query(Member).limit(num_students).all()

    if len(members) < num_students:
        print(f"    ⚠ Only {len(members)} members available, creating that many students")

    students = []
    today = date.today()

    for idx, member in enumerate(members):
        # Check if member already has a student record
        existing = db.query(Student).filter(Student.member_id == member.id).first()
        if existing:
            continue

        # Vary statuses realistically
        if idx < 15:
            status = StudentStatus.ENROLLED
            enrollment_date = today - timedelta(days=random.randint(30, 180))
            expected_completion = enrollment_date + timedelta(days=365)
        elif idx < 18:
            status = StudentStatus.COMPLETED
            enrollment_date = today - timedelta(days=random.randint(365, 730))
            expected_completion = enrollment_date + timedelta(days=365)
            actual_completion = expected_completion - timedelta(days=random.randint(0, 30))
        elif idx < 19:
            status = StudentStatus.ON_LEAVE
            enrollment_date = today - timedelta(days=random.randint(60, 120))
            expected_completion = enrollment_date + timedelta(days=365)
        else:
            status = StudentStatus.APPLICANT
            enrollment_date = None
            expected_completion = None

        student = Student(
            member_id=member.id,
            student_number=f"S{idx + 1:06d}",
            status=status,
            application_date=today - timedelta(days=random.randint(30, 365)),
            enrollment_date=enrollment_date if status != StudentStatus.APPLICANT else None,
            expected_completion_date=expected_completion,
            actual_completion_date=actual_completion if status == StudentStatus.COMPLETED else None,
            cohort="2026-Spring" if idx < 10 else "2025-Fall",
            emergency_contact_name=f"Emergency Contact {idx + 1}",
            emergency_contact_phone=f"555-{random.randint(1000, 9999)}",
            emergency_contact_relationship=random.choice(["Spouse", "Parent", "Sibling"]),
            notes=f"Student converted from member ID {member.id}",
        )
        db.add(student)
        students.append(student)

    db.commit()
    print(f"    ✓ Created {len(students)} students")
    return students


def seed_enrollments_and_sessions(
    db: Session, students: list[Student], courses: list[Course]
) -> tuple[list[Enrollment], list[ClassSession]]:
    """Create enrollments and class sessions for students in courses."""
    print("  Creating enrollments and class sessions...")

    enrollments = []
    class_sessions = []
    today = date.today()

    # Create class sessions for each course
    for course in courses:
        # Each course has 8-12 sessions
        num_sessions = random.randint(8, 12)
        start_date = today - timedelta(days=90)

        for session_num in range(num_sessions):
            session_date = start_date + timedelta(days=session_num * 7)  # Weekly sessions
            session = ClassSession(
                course_id=course.id,
                session_date=session_date,
                start_time=time(18, 0),  # 6 PM
                end_time=time(21, 0),  # 9 PM
                location="IBEW Training Center",
                room=f"Room {random.choice(['A', 'B', 'C'])}{random.randint(1, 5)}",
                instructor_name=random.choice([
                    "John Smith",
                    "Mary Johnson",
                    "Bob Anderson",
                    "Sarah Williams",
                ]),
                topic=f"Session {session_num + 1}: {course.name}",
                is_cancelled=False,
            )
            db.add(session)
            class_sessions.append(session)

    db.commit()

    # Enroll students in courses
    for student in students:
        if student.status == StudentStatus.APPLICANT:
            continue  # Applicants aren't enrolled yet

        # Enroll in 2-4 courses
        num_courses = random.randint(2, 4)
        selected_courses = random.sample(courses, min(num_courses, len(courses)))

        for course in selected_courses:
            enrollment = Enrollment(
                student_id=student.id,
                course_id=course.id,
                cohort=student.cohort or "2026-Spring",
                enrollment_date=student.enrollment_date or today,
                status=CourseEnrollmentStatus.ENROLLED
                if student.status == StudentStatus.ENROLLED
                else CourseEnrollmentStatus.COMPLETED,
                final_grade=random.uniform(70, 100) if student.status == StudentStatus.COMPLETED else None,
                letter_grade=None,
            )
            db.add(enrollment)
            enrollments.append(enrollment)

    db.commit()
    print(f"    ✓ Created {len(enrollments)} enrollments and {len(class_sessions)} class sessions")
    return enrollments, class_sessions


def seed_attendance(
    db: Session, students: list[Student], class_sessions: list[ClassSession]
) -> list[Attendance]:
    """Create attendance records for students in class sessions."""
    print("  Creating attendance records...")

    attendances = []

    # Get all enrollments
    enrollments = db.query(Enrollment).all()

    for enrollment in enrollments:
        # Get class sessions for this course
        course_sessions = [s for s in class_sessions if s.course_id == enrollment.course_id]

        # Create attendance for most sessions (80-100%)
        num_to_attend = int(len(course_sessions) * random.uniform(0.8, 1.0))
        attended_sessions = random.sample(course_sessions, num_to_attend)

        for session in attended_sessions:
            # Weighted random status (mostly present)
            status_weights = [
                (SessionAttendanceStatus.PRESENT, 0.8),
                (SessionAttendanceStatus.ABSENT, 0.05),
                (SessionAttendanceStatus.EXCUSED, 0.05),
                (SessionAttendanceStatus.LATE, 0.07),
                (SessionAttendanceStatus.LEFT_EARLY, 0.03),
            ]
            status = random.choices(
                [s for s, _ in status_weights],
                weights=[w for _, w in status_weights],
            )[0]

            attendance = Attendance(
                student_id=enrollment.student_id,
                class_session_id=session.id,
                status=status,
                arrival_time=time(18, random.randint(0, 15)) if status == SessionAttendanceStatus.LATE else None,
                departure_time=time(20, random.randint(0, 30)) if status == SessionAttendanceStatus.LEFT_EARLY else None,
            )
            db.add(attendance)
            attendances.append(attendance)

    db.commit()
    print(f"    ✓ Created {len(attendances)} attendance records")
    return attendances


def seed_grades(db: Session, enrollments: list[Enrollment]) -> list[Grade]:
    """Create grades for enrolled students."""
    print("  Creating grades...")

    grades = []
    today = date.today()

    for enrollment in enrollments:
        # Create 3-6 grades per enrollment
        num_grades = random.randint(3, 6)

        for i in range(num_grades):
            grade_type = random.choice([
                GradeType.ASSIGNMENT,
                GradeType.QUIZ,
                GradeType.EXAM,
                GradeType.PROJECT,
            ])

            points_possible = 100.0
            points_earned = random.uniform(60, 100)

            grade = Grade(
                student_id=enrollment.student_id,
                course_id=enrollment.course_id,
                grade_type=grade_type,
                name=f"{grade_type.value.title()} {i + 1}",
                points_earned=points_earned,
                points_possible=points_possible,
                weight=1.0,
                grade_date=today - timedelta(days=random.randint(7, 90)),
                feedback=f"Good work on {grade_type.value}" if points_earned >= 80 else "Needs improvement",
                graded_by="Instructor",
            )
            db.add(grade)
            grades.append(grade)

    db.commit()
    print(f"    ✓ Created {len(grades)} grades")
    return grades


def seed_certifications(db: Session, students: list[Student]) -> list[Certification]:
    """Create certifications for students."""
    print("  Creating certifications...")

    certifications = []
    today = date.today()

    for student in students:
        if student.status in [StudentStatus.ENROLLED, StudentStatus.COMPLETED]:
            # All enrolled/completed students get OSHA 10
            cert = Certification(
                student_id=student.id,
                cert_type=CertificationType.OSHA_10,
                status=CertificationStatus.ACTIVE,
                issue_date=today - timedelta(days=random.randint(30, 180)),
                expiration_date=today + timedelta(days=random.randint(365, 730)),
                certificate_number=f"OSHA10-{random.randint(10000, 99999)}",
                issuing_organization="OSHA",
                verified_by="Training Coordinator",
                verification_date=today - timedelta(days=random.randint(20, 170)),
            )
            db.add(cert)
            certifications.append(cert)

            # Some also get First Aid/CPR
            if random.random() < 0.6:
                cert = Certification(
                    student_id=student.id,
                    cert_type=random.choice([CertificationType.FIRST_AID, CertificationType.CPR]),
                    status=CertificationStatus.ACTIVE,
                    issue_date=today - timedelta(days=random.randint(30, 365)),
                    expiration_date=today + timedelta(days=random.randint(365, 730)),
                    certificate_number=f"FA-{random.randint(10000, 99999)}",
                    issuing_organization="American Red Cross",
                    verified_by="Training Coordinator",
                    verification_date=today - timedelta(days=random.randint(20, 355)),
                )
                db.add(cert)
                certifications.append(cert)

    db.commit()
    print(f"    ✓ Created {len(certifications)} certifications")
    return certifications


def run_training_seed(db: Session, num_students: int = 20):
    """Run complete training system seed data generation."""
    print("\n🎓 Seeding Phase 2 Training System...")

    # Create courses
    courses = seed_courses(db)

    # Create students from members
    students = seed_students(db, num_students)

    # Create enrollments and class sessions
    enrollments, class_sessions = seed_enrollments_and_sessions(db, students, courses)

    # Create attendance records
    attendances = seed_attendance(db, students, class_sessions)

    # Create grades
    grades = seed_grades(db, enrollments)

    # Create certifications
    certifications = seed_certifications(db, students)

    print(f"\n✅ Phase 2 Training System seeded successfully!")
    print(f"   • {len(courses)} courses")
    print(f"   • {len(students)} students")
    print(f"   • {len(enrollments)} enrollments")
    print(f"   • {len(class_sessions)} class sessions")
    print(f"   • {len(attendances)} attendance records")
    print(f"   • {len(grades)} grades")
    print(f"   • {len(certifications)} certifications")


if __name__ == "__main__":
    from src.db.session import SessionLocal

    db = SessionLocal()
    try:
        run_training_seed(db, num_students=20)
    finally:
        db.close()
