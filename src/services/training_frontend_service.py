"""
Training Frontend Service - Stats and queries for training pages.
Provides aggregated data for the training dashboard and lists.
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Tuple
from datetime import date
import logging

from src.models.student import Student
from src.models.member import Member
from src.models.course import Course
from src.models.enrollment import Enrollment
from src.db.enums import StudentStatus, CourseEnrollmentStatus

logger = logging.getLogger(__name__)


class TrainingFrontendService:
    """Service for training frontend pages."""

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # Dashboard Stats
    # ============================================================

    async def get_training_stats(self) -> dict:
        """
        Get all stats for the training dashboard.
        Returns counts and recent changes.
        """
        # Total students
        total_students = (
            self.db.execute(select(func.count(Student.id)))
        ).scalar() or 0

        # Active students (ENROLLED status)
        active_students = (
            self.db.execute(
                select(func.count(Student.id)).where(
                    Student.status == StudentStatus.ENROLLED
                )
            )
        ).scalar() or 0

        # Students enrolled this month
        first_of_month = date.today().replace(day=1)
        new_this_month = (
            self.db.execute(
                select(func.count(Student.id)).where(
                    Student.enrollment_date >= first_of_month
                )
            )
        ).scalar() or 0

        # Completed students (graduated)
        completed = (
            self.db.execute(
                select(func.count(Student.id)).where(
                    Student.status == StudentStatus.COMPLETED
                )
            )
        ).scalar() or 0

        # Total courses
        total_courses = (
            self.db.execute(select(func.count(Course.id)))
        ).scalar() or 0

        # Active courses
        active_courses = (
            self.db.execute(
                select(func.count(Course.id)).where(Course.is_active.is_(True))
            )
        ).scalar() or 0

        # Total enrollments
        total_enrollments = (
            self.db.execute(select(func.count(Enrollment.id)))
        ).scalar() or 0

        # Active enrollments (status = enrolled)
        active_enrollments = (
            self.db.execute(
                select(func.count(Enrollment.id)).where(
                    Enrollment.status == CourseEnrollmentStatus.ENROLLED
                )
            )
        ).scalar() or 0

        # Completion rate (completed / total finished)
        course_completed = (
            self.db.execute(
                select(func.count(Enrollment.id)).where(
                    Enrollment.status == CourseEnrollmentStatus.COMPLETED
                )
            )
        ).scalar() or 0

        total_finished = (
            self.db.execute(
                select(func.count(Enrollment.id)).where(
                    Enrollment.status.in_(
                        [
                            CourseEnrollmentStatus.COMPLETED,
                            CourseEnrollmentStatus.WITHDRAWN,
                            CourseEnrollmentStatus.FAILED,
                            CourseEnrollmentStatus.INCOMPLETE,
                        ]
                    )
                )
            )
        ).scalar() or 0

        completion_rate = round(
            (course_completed / total_finished * 100) if total_finished > 0 else 0, 1
        )

        return {
            "total_students": total_students,
            "active_students": active_students,
            "new_this_month": new_this_month,
            "completed": completed,
            "total_courses": total_courses,
            "active_courses": active_courses,
            "total_enrollments": total_enrollments,
            "active_enrollments": active_enrollments,
            "completion_rate": completion_rate,
        }

    # ============================================================
    # Student Queries
    # ============================================================

    async def get_recent_students(self, limit: int = 5) -> List[Student]:
        """Get recently enrolled students."""
        stmt = (
            select(Student)
            .options(selectinload(Student.member))
            .where(Student.enrollment_date.isnot(None))
            .order_by(Student.enrollment_date.desc())
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    async def search_students(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        cohort: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Student], int, int]:
        """
        Search and filter students with pagination.

        Returns:
            Tuple of (students, total_count, total_pages)
        """
        stmt = select(Student).options(selectinload(Student.member))

        # Search filter - need to join Member for name search
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            stmt = stmt.join(Student.member).where(
                or_(
                    Member.first_name.ilike(search_term),
                    Member.last_name.ilike(search_term),
                    Member.email.ilike(search_term),
                    Student.student_number.ilike(search_term),
                )
            )

        # Status filter
        if status and status != "all":
            try:
                status_enum = StudentStatus(status)
                stmt = stmt.where(Student.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter

        # Cohort filter
        if cohort and cohort != "all":
            stmt = stmt.where(Student.cohort == cohort)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (self.db.execute(count_stmt)).scalar() or 0

        # Apply sorting and pagination
        # Need to re-join for ordering if we haven't already
        if not query or not query.strip():
            stmt = stmt.join(Student.member)
        stmt = stmt.order_by(Member.last_name, Member.first_name)
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)

        result = self.db.execute(stmt)
        students = list(result.scalars().all())

        total_pages = (total + per_page - 1) // per_page if total > 0 else 1

        return students, total, total_pages

    async def get_student_by_id(self, student_id: int) -> Optional[Student]:
        """Get a single student with relationships loaded."""
        stmt = (
            select(Student)
            .options(
                selectinload(Student.member),
                selectinload(Student.enrollments).selectinload(Enrollment.course),
            )
            .where(Student.id == student_id)
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ============================================================
    # Course Queries
    # ============================================================

    async def get_courses_with_enrollment_counts(self) -> List[dict]:
        """Get all courses with their enrollment counts."""
        # Get courses
        courses_stmt = (
            select(Course).where(Course.is_active.is_(True)).order_by(Course.code)
        )
        courses_result = self.db.execute(courses_stmt)
        courses = list(courses_result.scalars().all())

        # Get enrollment counts per course
        counts_stmt = select(
            Enrollment.course_id,
            func.count(Enrollment.id).label("total"),
            func.count(Enrollment.id)
            .filter(Enrollment.status == CourseEnrollmentStatus.ENROLLED)
            .label("active"),
        ).group_by(Enrollment.course_id)
        counts_result = self.db.execute(counts_stmt)
        counts = {
            row.course_id: {"total": row.total, "active": row.active}
            for row in counts_result
        }

        # Combine
        result = []
        for course in courses:
            course_counts = counts.get(course.id, {"total": 0, "active": 0})
            result.append(
                {
                    "course": course,
                    "total_enrollments": course_counts["total"],
                    "active_enrollments": course_counts["active"],
                }
            )

        return result

    async def get_course_by_id(self, course_id: int) -> Optional[Course]:
        """Get a single course with relationships."""
        stmt = (
            select(Course)
            .options(selectinload(Course.enrollments).selectinload(Enrollment.student))
            .where(Course.id == course_id)
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ============================================================
    # Cohort Queries
    # ============================================================

    async def get_all_cohorts(self) -> List[str]:
        """Get all unique cohorts for filter dropdown."""
        stmt = (
            select(Student.cohort)
            .where(Student.cohort.isnot(None))
            .distinct()
            .order_by(Student.cohort.desc())
        )
        result = self.db.execute(stmt)
        return [row[0] for row in result.all()]

    # ============================================================
    # Status Helpers
    # ============================================================

    @staticmethod
    def get_status_badge_class(status: StudentStatus) -> str:
        """Get DaisyUI badge class for student status."""
        mapping = {
            StudentStatus.ENROLLED: "badge-success",
            StudentStatus.COMPLETED: "badge-info",
            StudentStatus.DROPPED: "badge-error",
            StudentStatus.DISMISSED: "badge-error",
            StudentStatus.ON_LEAVE: "badge-warning",
            StudentStatus.APPLICANT: "badge-ghost",
        }
        return mapping.get(status, "badge-ghost")

    @staticmethod
    def get_enrollment_badge_class(status: CourseEnrollmentStatus) -> str:
        """Get DaisyUI badge class for enrollment status."""
        mapping = {
            CourseEnrollmentStatus.ENROLLED: "badge-primary",
            CourseEnrollmentStatus.COMPLETED: "badge-success",
            CourseEnrollmentStatus.WITHDRAWN: "badge-warning",
            CourseEnrollmentStatus.FAILED: "badge-error",
            CourseEnrollmentStatus.INCOMPLETE: "badge-warning",
        }
        return mapping.get(status, "badge-ghost")


# Convenience function
async def get_training_service(db: Session) -> TrainingFrontendService:
    return TrainingFrontendService(db)
