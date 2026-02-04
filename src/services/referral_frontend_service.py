"""
Frontend service for Referral Books & Registration UI.

Created: February 4, 2026 (Week 26)
Phase 7 - Referral & Dispatch System

Wraps backend ReferralBookService and BookRegistrationService
calls and formats data for Jinja2 template rendering.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from src.services import referral_book_service
from src.services import book_registration_service
from src.services import queue_service
from src.models.referral_book import ReferralBook
from src.models.book_registration import BookRegistration
from src.models.member import Member
from src.db.enums import (
    RegistrationStatus,
    ExemptReason,
    RolloffReason,
    BookClassification,
    BookRegion,
)


class ReferralFrontendService:
    """
    Provides template-ready data for referral book and registration pages.

    Follows the same pattern as DuesFrontendService:
    - Wraps backend service calls
    - Formats data for template rendering
    - Provides badge/status helper methods
    - Handles pagination formatting
    """

    # Registration status badge colors
    STATUS_BADGE_COLORS = {
        RegistrationStatus.REGISTERED: "badge-success",
        RegistrationStatus.DISPATCHED: "badge-info",
        RegistrationStatus.RESIGNED: "badge-warning",
        RegistrationStatus.ROLLED_OFF: "badge-error",
        RegistrationStatus.EXEMPT: "badge-accent",
    }

    # Exempt reason badge colors
    EXEMPT_REASON_COLORS = {
        ExemptReason.MILITARY: "badge-primary",
        ExemptReason.MEDICAL: "badge-warning",
        ExemptReason.UNION_BUSINESS: "badge-info",
        ExemptReason.SALTING: "badge-accent",
        ExemptReason.JURY_DUTY: "badge-secondary",
        ExemptReason.UNDER_SCALE: "badge-warning",
        ExemptReason.TRAVELING: "badge-info",
        ExemptReason.OTHER: "badge-ghost",
    }

    # Rolloff reason badge colors
    ROLLOFF_REASON_COLORS = {
        RolloffReason.CHECK_MARKS: "badge-error",
        RolloffReason.QUIT: "badge-warning",
        RolloffReason.DISCHARGED: "badge-error",
        RolloffReason.FAILED_RE_SIGN: "badge-warning",
        RolloffReason.NINETY_DAY_RULE: "badge-info",
        RolloffReason.BID_REJECT_QUIT: "badge-error",
        RolloffReason.EXPIRED: "badge-ghost",
        RolloffReason.MANUAL: "badge-warning",
    }

    def __init__(self, db: Session):
        self.db = db

    # --- Badge & Formatting Helpers ---

    @staticmethod
    def registration_status_badge(status: RegistrationStatus) -> dict:
        """Returns DaisyUI badge class and label for registration status."""
        badge_class = ReferralFrontendService.STATUS_BADGE_COLORS.get(
            status, "badge-ghost"
        )
        return {"class": badge_class, "label": status.value.replace("_", " ").title()}

    @staticmethod
    def exempt_reason_badge(reason: ExemptReason) -> dict:
        """Returns DaisyUI badge class and label for exempt reason."""
        badge_class = ReferralFrontendService.EXEMPT_REASON_COLORS.get(
            reason, "badge-ghost"
        )
        return {"class": badge_class, "label": reason.value.replace("_", " ").title()}

    @staticmethod
    def rolloff_reason_badge(reason: RolloffReason) -> dict:
        """Returns DaisyUI badge class and label for rolloff reason."""
        badge_class = ReferralFrontendService.ROLLOFF_REASON_COLORS.get(
            reason, "badge-ghost"
        )
        return {"class": badge_class, "label": reason.value.replace("_", " ").title()}

    @staticmethod
    def book_active_badge(is_active: bool) -> dict:
        """Returns badge for book active status."""
        if is_active:
            return {"class": "badge-success", "label": "Active"}
        return {"class": "badge-ghost", "label": "Inactive"}

    # --- Book Methods ---

    def get_books_overview(
        self,
        classification: Optional[BookClassification] = None,
        region: Optional[BookRegion] = None,
        active_only: bool = True,
    ) -> List[dict]:
        """
        Get all books with summary stats for the landing/list page.
        Returns list of dicts with book info + registration counts.
        """
        # Get books summary from backend service
        books_summary = referral_book_service.get_all_books_summary(self.db)

        # Apply filters if provided
        if classification:
            books_summary = [
                b for b in books_summary
                if b.get("classification") == classification
            ]

        if region:
            books_summary = [
                b for b in books_summary
                if b.get("region") == region
            ]

        if active_only:
            books_summary = [
                b for b in books_summary
                if b.get("is_active", True)
            ]

        return books_summary

    def get_book_detail(self, book_id: int) -> Optional[dict]:
        """
        Get single book with full detail including registered members.
        """
        book = referral_book_service.get_by_id(self.db, book_id)
        if not book:
            return None

        # Get stats
        stats = referral_book_service.get_book_stats(self.db, book_id)

        # Get queue (registered members)
        queue = queue_service.get_queue_snapshot(
            self.db, book_id, include_exempt=True, limit=None
        )

        # Build detail dict
        detail = {
            "book": book,
            "stats": stats,
            "queue": queue,
            "queue_count": len(queue),
        }

        return detail

    def get_book_stats(self, book_id: int) -> Optional[dict]:
        """
        Get statistics for a single book (for HTMX partial refresh).
        """
        stats = referral_book_service.get_book_stats(self.db, book_id)
        if not stats:
            return None

        return {
            "total_registered": stats.total_registered,
            "active_count": stats.active_count,
            "dispatched_count": stats.dispatched_count,
            "with_check_mark": stats.with_check_mark,
            "without_check_mark": stats.without_check_mark,
            "exempt_count": stats.exempt_count,
        }

    def get_landing_stats(self) -> dict:
        """
        Get overall referral system stats for landing page.
        """
        # Count active books
        active_books = self.db.query(func.count(ReferralBook.id)).filter(
            ReferralBook.is_active == True
        ).scalar() or 0

        # Count total registered members (across all books)
        total_registered = self.db.query(func.count(BookRegistration.id)).filter(
            BookRegistration.status == RegistrationStatus.REGISTERED
        ).scalar() or 0

        # Count dispatched today (would need dispatch table for actual count)
        # For now, just count all dispatched
        dispatched_count = self.db.query(func.count(BookRegistration.id)).filter(
            BookRegistration.status == RegistrationStatus.DISPATCHED
        ).scalar() or 0

        # Count members with check marks
        with_check_marks = self.db.query(func.count(BookRegistration.id)).filter(
            and_(
                BookRegistration.status == RegistrationStatus.REGISTERED,
                BookRegistration.has_check_mark == True,
            )
        ).scalar() or 0

        return {
            "active_books": active_books,
            "total_registered": total_registered,
            "dispatched_count": dispatched_count,
            "with_check_marks": with_check_marks,
        }

    # --- Registration Methods ---

    def get_registrations(
        self,
        filters: Optional[dict] = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        """
        Get paginated registration list with optional filters.
        Filters may include: book_id, member_id, status, search.
        """
        filters = filters or {}

        # Build query
        query = (
            self.db.query(BookRegistration)
            .join(Member, BookRegistration.member_id == Member.id)
            .join(ReferralBook, BookRegistration.book_id == ReferralBook.id)
        )

        # Apply filters
        if filters.get("book_id"):
            query = query.filter(BookRegistration.book_id == filters["book_id"])

        if filters.get("member_id"):
            query = query.filter(BookRegistration.member_id == filters["member_id"])

        if filters.get("status"):
            try:
                status = RegistrationStatus(filters["status"])
                query = query.filter(BookRegistration.status == status)
            except (ValueError, KeyError):
                pass

        if filters.get("search"):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                (Member.first_name + " " + Member.last_name).ilike(search_term)
                | Member.card_number.ilike(search_term)
            )

        # Get total count
        total = query.count()

        # Paginate
        offset = (page - 1) * per_page
        registrations = (
            query.order_by(
                ReferralBook.name,
                BookRegistration.registration_number
            )
            .offset(offset)
            .limit(per_page)
            .all()
        )

        # Calculate pagination
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages

        return {
            "registrations": registrations,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
        }

    def get_registration_detail(self, registration_id: int) -> Optional[dict]:
        """
        Get single registration with member info and history.
        """
        registration = book_registration_service.get_by_id(self.db, registration_id)
        if not registration:
            return None

        # Get member
        member = self.db.query(Member).filter(Member.id == registration.member_id).first()

        # Get book
        book = referral_book_service.get_by_id(self.db, registration.book_id)

        # Get member's queue status
        queue_status = queue_service.get_member_queue_status(self.db, registration.member_id)

        # Get member's all registrations (history)
        all_registrations = book_registration_service.get_member_registrations(
            self.db, registration.member_id, active_only=False
        )

        return {
            "registration": registration,
            "member": member,
            "book": book,
            "queue_status": queue_status,
            "history": all_registrations,
        }

    def register_member(self, data: dict) -> dict:
        """
        Register a member on a book. Wraps service call with
        error handling suitable for HTMX response.
        """
        try:
            registration = book_registration_service.register_member(
                db=self.db,
                member_id=int(data["member_id"]),
                book_id=int(data["book_id"]),
                performed_by_id=int(data["performed_by_id"]),
                registration_method=data.get("registration_method", "in_person"),
                notes=data.get("notes"),
            )
            return {"success": True, "registration": registration}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def re_sign_member(self, registration_id: int, performed_by_id: int) -> dict:
        """
        Re-sign a member's registration. Returns success/error for HTMX.
        """
        try:
            registration = book_registration_service.re_sign_member(
                db=self.db,
                registration_id=registration_id,
                performed_by_id=performed_by_id,
            )
            return {"success": True, "registration": registration}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def resign_member(
        self,
        registration_id: int,
        performed_by_id: int,
        reason: Optional[str] = None,
    ) -> dict:
        """
        Resign a member from a book. Returns success/error for HTMX.
        """
        try:
            registration = book_registration_service.resign_member(
                db=self.db,
                registration_id=registration_id,
                performed_by_id=performed_by_id,
                reason=reason,
            )
            return {"success": True, "registration": registration}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def get_active_books_for_dropdown(self) -> List[dict]:
        """Get active books formatted for dropdown select options."""
        books = referral_book_service.get_all_active(self.db)
        return [
            {"id": book.id, "name": book.name, "code": book.code}
            for book in books
        ]

    def search_members(self, search_term: str, limit: int = 10) -> List[dict]:
        """
        Search members by name or card number for typeahead.
        Returns list of dicts with id, name, card_number.
        """
        if not search_term or len(search_term) < 2:
            return []

        search_pattern = f"%{search_term}%"
        members = (
            self.db.query(Member)
            .filter(
                (Member.first_name + " " + Member.last_name).ilike(search_pattern)
                | Member.card_number.ilike(search_pattern)
            )
            .limit(limit)
            .all()
        )

        return [
            {
                "id": m.id,
                "name": f"{m.first_name} {m.last_name}",
                "card_number": m.card_number,
            }
            for m in members
        ]
