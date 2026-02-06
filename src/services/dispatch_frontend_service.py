"""
Frontend service for Dispatch Workflow UI.

Created: February 4, 2026 (Week 27)
Phase 7 - Referral & Dispatch System

Wraps LaborRequestService, JobBidService, DispatchService,
QueueService, and EnforcementService for Jinja2 template rendering.

Handles time-sensitive business rules:
- Bidding window: 5:30 PM – 7:00 AM
- 3 PM cutoff for next morning dispatch
- Morning referral processing order
"""

from typing import Optional, List
from datetime import datetime, date, time, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from src.models.labor_request import LaborRequest
from src.models.dispatch import Dispatch
from src.models.job_bid import JobBid
from src.models.book_registration import BookRegistration
from src.db.enums import (
    LaborRequestStatus,
    DispatchStatus,
    BidStatus,
    RegistrationStatus,
)


class DispatchFrontendService:
    """
    Provides template-ready data for dispatch workflow pages.

    Handles time-sensitive business rules:
    - Bidding window: 5:30 PM – 7:00 AM
    - 3 PM cutoff for next morning dispatch
    - Morning referral processing order
    """

    BIDDING_WINDOW_START = time(17, 30)  # 5:30 PM
    BIDDING_WINDOW_END = time(7, 0)  # 7:00 AM
    CUTOFF_TIME = time(15, 0)  # 3:00 PM

    def __init__(self, db: Session):
        self.db = db

    # --- Dashboard Methods ---

    def get_dashboard_stats(self) -> dict:
        """
        Get key metrics for the dispatch dashboard.
        Returns dict with: pending_requests, todays_dispatches,
        active_dispatches, queue_size, active_suspensions, etc.
        """
        # Count pending/open requests
        pending_requests = (
            self.db.query(LaborRequest)
            .filter(
                LaborRequest.status.in_(
                    [LaborRequestStatus.OPEN, LaborRequestStatus.PARTIALLY_FILLED]
                )
            )
            .count()
        )

        # Count today's dispatches
        today = date.today()
        todays_dispatches = (
            self.db.query(Dispatch)
            .filter(func.date(Dispatch.dispatch_date) == today)
            .count()
        )

        # Count active dispatches
        active_dispatches = (
            self.db.query(Dispatch)
            .filter(
                Dispatch.dispatch_status.in_(
                    [
                        DispatchStatus.DISPATCHED,
                        DispatchStatus.CHECKED_IN,
                        DispatchStatus.WORKING,
                    ]
                )
            )
            .count()
        )

        # Count pending bids
        pending_bids = (
            self.db.query(JobBid).filter(JobBid.bid_status == BidStatus.PENDING).count()
        )

        return {
            "pending_requests": pending_requests,
            "todays_dispatches": todays_dispatches,
            "active_dispatches": active_dispatches,
            "pending_bids": pending_bids,
        }

    def get_todays_activity(self) -> List[dict]:
        """
        Get today's dispatch activity timeline.
        Returns list of events: dispatches, returns, requests received.
        """
        today = date.today()

        # Get today's dispatches
        dispatches = (
            self.db.query(Dispatch)
            .filter(func.date(Dispatch.dispatch_date) == today)
            .order_by(Dispatch.dispatch_date.desc())
            .limit(20)
            .all()
        )

        # Get today's requests
        requests = (
            self.db.query(LaborRequest)
            .filter(func.date(LaborRequest.request_date) == today)
            .order_by(LaborRequest.request_date.desc())
            .limit(10)
            .all()
        )

        # Combine and sort by time
        activity = []

        for dispatch in dispatches:
            activity.append(
                {
                    "type": "dispatch",
                    "time": dispatch.dispatch_date,
                    "description": f"{dispatch.member.full_name if dispatch.member else 'Unknown'} dispatched to {dispatch.employer.name if dispatch.employer else 'Unknown'}",
                    "id": dispatch.id,
                }
            )

        for request in requests:
            activity.append(
                {
                    "type": "request",
                    "time": request.request_date,
                    "description": f"New request from {request.employer_name} ({request.workers_requested} workers)",
                    "id": request.id,
                }
            )

        # Sort by time descending
        activity.sort(key=lambda x: x["time"], reverse=True)

        return activity[:15]  # Return top 15 events

    def is_bidding_window_open(self) -> bool:
        """
        Check if the bidding window is currently open.
        Window: 5:30 PM – 7:00 AM next day.
        """
        now = datetime.now().time()
        return now >= self.BIDDING_WINDOW_START or now < self.BIDDING_WINDOW_END

    def is_past_cutoff(self) -> bool:
        """
        Check if we're past the 3 PM cutoff for next morning dispatch.
        """
        return datetime.now().time() >= self.CUTOFF_TIME

    def get_time_context(self) -> dict:
        """
        Get current time context for UI display.
        Returns: bidding_open, past_cutoff, current_time, next_event.
        """
        bidding_open = self.is_bidding_window_open()
        past_cutoff = self.is_past_cutoff()

        return {
            "bidding_open": bidding_open,
            "past_cutoff": past_cutoff,
            "current_time": datetime.now(),
            "next_event": self._get_next_event(),
            "bidding_badge": self.bidding_window_badge(bidding_open),
        }

    # --- Labor Request Methods ---

    def get_requests(
        self, filters: Optional[dict] = None, page: int = 1, per_page: int = 25
    ) -> dict:
        """
        Get paginated labor requests with optional filters.
        Filters: status, employer, date_range, agreement_type, urgency.
        """
        filters = filters or {}
        query = self.db.query(LaborRequest)

        # Apply filters
        if filters.get("status"):
            try:
                status = LaborRequestStatus(filters["status"])
                query = query.filter(LaborRequest.status == status)
            except ValueError:
                pass

        if filters.get("employer_id"):
            query = query.filter(LaborRequest.employer_id == filters["employer_id"])

        if filters.get("book_id"):
            query = query.filter(LaborRequest.book_id == filters["book_id"])

        if filters.get("search"):
            search = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    LaborRequest.employer_name.ilike(search),
                    LaborRequest.request_number.ilike(search),
                )
            )

        # Order by urgency, then date
        query = query.order_by(
            LaborRequest.start_date, LaborRequest.request_date.desc()
        )

        # Paginate
        total = query.count()
        offset = (page - 1) * per_page
        requests = query.offset(offset).limit(per_page).all()

        return {
            "items": requests,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }

    def get_request_detail(self, request_id: int) -> Optional[dict]:
        """
        Get single labor request with employer info, candidates, and bids.
        Includes matching candidates from relevant books based on
        agreement type filtering (Rule 4) and check mark requirements (Rule 11).
        """
        request = (
            self.db.query(LaborRequest).filter(LaborRequest.id == request_id).first()
        )
        if not request:
            return None

        # Get candidates from the book (registered, not dispatched)
        candidates = (
            self.db.query(BookRegistration)
            .filter(
                BookRegistration.book_id == request.book_id,
                BookRegistration.status == RegistrationStatus.REGISTERED,
            )
            .order_by(BookRegistration.registration_number)
            .limit(50)
            .all()
        )

        # Get bids for this request
        bids = (
            self.db.query(JobBid)
            .filter(JobBid.labor_request_id == request_id)
            .order_by(JobBid.bid_submitted_at)
            .all()
        )

        # Get dispatch history for this request
        dispatches = (
            self.db.query(Dispatch)
            .filter(Dispatch.labor_request_id == request_id)
            .order_by(Dispatch.dispatch_date.desc())
            .all()
        )

        return {
            "request": request,
            "candidates": candidates,
            "bids": bids,
            "dispatches": dispatches,
        }

    # --- Bid Methods ---

    def get_pending_bids(self) -> List[dict]:
        """
        Get all pending bids for morning referral processing.
        Ordered by book position (Rule 2: morning referral order).
        """
        # Get all pending bids with registration and request info
        bids = (
            self.db.query(JobBid)
            .filter(JobBid.bid_status == BidStatus.PENDING)
            .join(JobBid.registration)
            .join(JobBid.labor_request)
            .order_by(BookRegistration.registration_number, JobBid.bid_submitted_at)
            .all()
        )

        # Group by request
        requests = {}
        for bid in bids:
            request_id = bid.labor_request_id
            if request_id not in requests:
                requests[request_id] = {"request": bid.labor_request, "bids": []}
            requests[request_id]["bids"].append(bid)

        return list(requests.values())

    def get_bids_for_request(self, request_id: int) -> List[JobBid]:
        """
        Get all bids for a specific labor request.
        """
        return (
            self.db.query(JobBid)
            .filter(JobBid.labor_request_id == request_id)
            .order_by(JobBid.bid_submitted_at)
            .all()
        )

    # --- Dispatch Methods ---

    def get_active_dispatches(
        self, filters: Optional[dict] = None, page: int = 1, per_page: int = 50
    ) -> dict:
        """
        Get active dispatches with optional filters.
        """
        filters = filters or {}
        query = self.db.query(Dispatch).filter(
            Dispatch.dispatch_status.in_(
                [
                    DispatchStatus.DISPATCHED,
                    DispatchStatus.CHECKED_IN,
                    DispatchStatus.WORKING,
                ]
            )
        )

        # Apply filters
        if filters.get("status"):
            try:
                status = DispatchStatus(filters["status"])
                query = query.filter(Dispatch.dispatch_status == status)
            except ValueError:
                pass

        if filters.get("book_id"):
            query = query.filter(Dispatch.book_id == filters["book_id"])

        if filters.get("employer_id"):
            query = query.filter(Dispatch.employer_id == filters["employer_id"])

        if filters.get("search"):
            search = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Dispatch.member.has(
                        func.concat(
                            Dispatch.member.first_name, " ", Dispatch.member.last_name
                        ).ilike(search)
                    ),
                    Dispatch.employer.has(Dispatch.employer.name.ilike(search)),
                )
            )

        # Order by dispatch date
        query = query.order_by(Dispatch.dispatch_date.desc())

        # Paginate
        total = query.count()
        offset = (page - 1) * per_page
        dispatches = query.offset(offset).limit(per_page).all()

        return {
            "items": dispatches,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }

    def get_dispatch_detail(self, dispatch_id: int) -> Optional[Dispatch]:
        """
        Get single dispatch detail with member, employer, and history.
        """
        return self.db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()

    # --- Queue Methods ---

    def get_queue(
        self, book_id: Optional[int] = None, limit: int = 100
    ) -> List[BookRegistration]:
        """
        Get current queue positions. Optionally filter by book.
        """
        query = self.db.query(BookRegistration).filter(
            BookRegistration.status == RegistrationStatus.REGISTERED
        )

        if book_id:
            query = query.filter(BookRegistration.book_id == book_id)

        query = query.order_by(BookRegistration.registration_number)

        return query.limit(limit).all()

    # --- Enforcement Methods ---

    def get_enforcement_summary(self) -> dict:
        """
        Get enforcement dashboard data.
        Returns: active_suspensions, recent_violations, blackout_members.
        """
        # For now, return placeholder data
        # In production, this would query suspension and blackout tables
        return {
            "active_suspensions": 0,
            "recent_violations": 0,
            "blackout_members": 0,
        }

    def get_suspensions(self, status: str = "active") -> List[dict]:
        """
        Get suspension records.
        """
        # Placeholder - would query suspension table
        return []

    def get_violations(self, filters: Optional[dict] = None) -> List[dict]:
        """
        Get violation records.
        """
        # Placeholder - would query violation table
        return []

    # --- Badge & Formatting Helpers ---

    @staticmethod
    def request_status_badge(status: str) -> dict:
        """DaisyUI badge for request status."""
        badges = {
            "open": {"class": "badge-info", "label": "Open"},
            "partially_filled": {"class": "badge-warning", "label": "Partial"},
            "filled": {"class": "badge-success", "label": "Filled"},
            "cancelled": {"class": "badge-error", "label": "Cancelled"},
            "expired": {"class": "badge-ghost", "label": "Expired"},
        }
        return badges.get(status, {"class": "badge-ghost", "label": status})

    @staticmethod
    def dispatch_status_badge(status: str) -> dict:
        """DaisyUI badge for dispatch status."""
        badges = {
            "dispatched": {"class": "badge-info", "label": "Dispatched"},
            "checked_in": {"class": "badge-accent", "label": "Checked In"},
            "working": {"class": "badge-success", "label": "Working"},
            "completed": {"class": "badge-info", "label": "Completed"},
            "terminated": {"class": "badge-error", "label": "Terminated"},
            "rejected": {"class": "badge-error", "label": "Rejected"},
            "no_show": {"class": "badge-error", "label": "No Show"},
        }
        return badges.get(status, {"class": "badge-ghost", "label": status})

    @staticmethod
    def bid_status_badge(status: str) -> dict:
        """DaisyUI badge for bid status."""
        badges = {
            "pending": {"class": "badge-warning", "label": "Pending"},
            "accepted": {"class": "badge-success", "label": "Accepted"},
            "rejected": {"class": "badge-error", "label": "Rejected"},
            "withdrawn": {"class": "badge-ghost", "label": "Withdrawn"},
            "expired": {"class": "badge-ghost", "label": "Expired"},
        }
        return badges.get(status, {"class": "badge-ghost", "label": status})

    @staticmethod
    def bidding_window_badge(is_open: bool) -> dict:
        """DaisyUI badge for bidding window status."""
        if is_open:
            return {"class": "badge-success", "label": "Bidding Open"}
        return {"class": "badge-ghost", "label": "Bidding Closed"}

    @staticmethod
    def format_time_ago(dt: datetime) -> str:
        """Format datetime as 'X minutes ago', '2 hours ago', etc."""
        now = datetime.now()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=now.tzinfo)

        delta = now - dt

        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"

        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours} hour{'s' if hours != 1 else ''} ago"

        minutes = (delta.seconds // 60) % 60
        if minutes > 0:
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"

        return "Just now"

    # --- Exemption Methods (Week 32) ---

    def get_exemption_stats(self) -> dict:
        """Returns exemption statistics.

        Returns: {
            'total_active': int,
            'by_type': {reason: count},
            'expiring_soon': int (within 7 days),
        }
        """
        today = date.today()
        seven_days = today + timedelta(days=7)

        # Get all exempt registrations
        exempt_registrations = (
            self.db.query(BookRegistration)
            .filter(BookRegistration.is_exempt.is_(True))
            .all()
        )

        total_active = len(exempt_registrations)

        # Count by type
        by_type = {}
        expiring_soon = 0
        for reg in exempt_registrations:
            reason = reg.exempt_reason.value if reg.exempt_reason else "unknown"
            by_type[reason] = by_type.get(reason, 0) + 1

            # Check if expiring within 7 days
            if reg.exempt_end_date and reg.exempt_end_date <= seven_days:
                expiring_soon += 1

        return {
            "total_active": total_active,
            "by_type": by_type,
            "expiring_soon": expiring_soon,
        }

    def get_exemptions(
        self, filters: Optional[dict] = None, page: int = 1, per_page: int = 25
    ) -> dict:
        """Get paginated exempt registrations with optional filters."""
        from src.db.enums import ExemptReason

        filters = filters or {}
        query = self.db.query(BookRegistration).filter(
            BookRegistration.is_exempt.is_(True)
        )

        # Apply filters
        if filters.get("exempt_reason"):
            try:
                reason = ExemptReason(filters["exempt_reason"])
                query = query.filter(BookRegistration.exempt_reason == reason)
            except ValueError:
                pass

        if filters.get("search"):
            search = f"%{filters['search']}%"
            query = query.join(BookRegistration.member).filter(
                or_(
                    BookRegistration.member.has(
                        func.concat(
                            BookRegistration.member.property.mapper.class_.first_name,
                            " ",
                            BookRegistration.member.property.mapper.class_.last_name,
                        ).ilike(search)
                    ),
                )
            )

        if filters.get("status") == "expiring":
            seven_days = date.today() + timedelta(days=7)
            query = query.filter(BookRegistration.exempt_end_date <= seven_days)

        # Order by start date descending
        query = query.order_by(BookRegistration.exempt_start_date.desc())

        # Paginate
        total = query.count()
        offset = (page - 1) * per_page
        registrations = query.offset(offset).limit(per_page).all()

        return {
            "items": registrations,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }

    def get_exemption_detail(self, registration_id: int) -> Optional[BookRegistration]:
        """Get a single exempt registration by ID."""
        return (
            self.db.query(BookRegistration)
            .filter(
                BookRegistration.id == registration_id,
                BookRegistration.is_exempt.is_(True),
            )
            .first()
        )

    @staticmethod
    def format_exemption_badge(exempt_reason: str) -> dict:
        """Returns DaisyUI badge styling for exemption type."""
        badges = {
            "military": {"class": "badge-info", "label": "Military"},
            "union_business": {"class": "badge-primary", "label": "Union Business"},
            "salting": {"class": "badge-warning", "label": "Salting"},
            "medical": {"class": "badge-error", "label": "Medical"},
            "jury_duty": {"class": "badge-secondary", "label": "Jury Duty"},
            "under_scale": {"class": "badge-accent", "label": "Under Scale"},
            "traveling": {"class": "badge-ghost", "label": "Traveling"},
            "other": {"class": "badge-ghost", "label": "Other"},
        }
        return badges.get(
            exempt_reason, {"class": "badge-ghost", "label": exempt_reason}
        )

    # --- Check Mark Methods (Week 32) ---

    def get_member_checkmark_summary(self, member_id: int) -> list:
        """Returns check marks per book for a member.

        Each entry: {
            'book_id': int,
            'book_name': str,
            'count': int,
            'max_allowed': 2,
            'at_limit': bool,
            'history': [{date, reason, dispatch_id}],
        }
        """
        registrations = (
            self.db.query(BookRegistration)
            .filter(
                BookRegistration.member_id == member_id,
                BookRegistration.status == RegistrationStatus.REGISTERED,
            )
            .all()
        )

        result = []
        for reg in registrations:
            result.append(
                {
                    "book_id": reg.book_id,
                    "book_name": reg.book.name if reg.book else "Unknown",
                    "count": reg.check_marks,
                    "max_allowed": 2,
                    "at_limit": reg.check_marks >= 2,
                    "registration_id": reg.id,
                    # History would come from registration_activities - simplified for now
                    "history": [],
                }
            )

        return result

    def get_checkmark_stats(self) -> dict:
        """Get check mark statistics across all registrations."""
        registrations = (
            self.db.query(BookRegistration)
            .filter(BookRegistration.status == RegistrationStatus.REGISTERED)
            .all()
        )

        total_with_marks = 0
        at_limit = 0

        for reg in registrations:
            if reg.check_marks > 0:
                total_with_marks += 1
            if reg.check_marks >= 2:
                at_limit += 1

        return {
            "total_with_marks": total_with_marks,
            "at_limit": at_limit,
        }

    # --- Report Categories (Week 32) ---

    def get_report_categories(self) -> list:
        """Returns report categories with availability status.

        Each category: {
            'name': str,
            'icon': str (Heroicon name),
            'priority': str,
            'description': str,
            'reports': [{'name', 'available', 'url'}],
            'total': int,
            'available_count': int,
        }
        """
        return [
            {
                "name": "Out-of-Work Lists",
                "icon": "clipboard-list",
                "priority": "P0",
                "description": "Daily operational lists for dispatch staff",
                "reports": [
                    {
                        "name": "Out-of-Work List (by Book)",
                        "available": True,
                        "url": "/api/v1/reports/referral/out-of-work/book/{book_id}",
                        "needs_book_selector": True,
                        "formats": ["pdf", "xlsx"],
                    },
                    {
                        "name": "Out-of-Work List (All Books)",
                        "available": True,
                        "url": "/api/v1/reports/referral/out-of-work/all-books",
                        "needs_book_selector": False,
                        "formats": ["pdf", "xlsx"],
                    },
                    {
                        "name": "Out-of-Work Summary",
                        "available": True,
                        "url": "/api/v1/reports/referral/out-of-work/summary",
                        "needs_book_selector": False,
                        "formats": ["pdf"],
                    },
                    {
                        "name": "Active Registrations by Member",
                        "available": True,
                        "url": "/api/v1/reports/referral/member/{member_id}/registrations",
                        "needs_member_selector": True,
                        "formats": ["pdf"],
                    },
                ],
                "total": 4,
                "available_count": 4,
            },
            {
                "name": "Dispatch Operations",
                "icon": "truck",
                "priority": "P0",
                "description": "Dispatch logs, history, and active dispatches",
                "reports": [
                    {
                        "name": "Daily Dispatch Log",
                        "available": True,
                        "url": "/api/v1/reports/referral/dispatch-log",
                        "needs_date_range": True,
                        "formats": ["pdf", "xlsx"],
                    },
                    {
                        "name": "Dispatch History by Member",
                        "available": True,
                        "url": "/api/v1/reports/referral/member/{member_id}/dispatch-history",
                        "needs_member_selector": True,
                        "formats": ["pdf"],
                    },
                    {
                        "name": "Morning Referral Sheet",
                        "available": True,
                        "url": "/api/v1/reports/referral/morning-referral",
                        "needs_date_selector": False,
                        "formats": ["pdf"],
                        "is_critical": True,
                    },
                    {
                        "name": "Active Dispatches",
                        "available": True,
                        "url": "/api/v1/reports/referral/active-dispatches",
                        "needs_date_selector": False,
                        "formats": ["pdf", "xlsx"],
                    },
                    {
                        "name": "Labor Request Status",
                        "available": True,
                        "url": "/api/v1/reports/referral/labor-requests",
                        "needs_date_range": True,
                        "needs_status_filter": True,
                        "formats": ["pdf", "xlsx"],
                    },
                ],
                "total": 5,
                "available_count": 5,
            },
            {
                "name": "Registration Reports",
                "icon": "user-plus",
                "priority": "P0/P1",
                "description": "Registration activity and re-sign deadlines",
                "reports": [
                    {
                        "name": "Registration History",
                        "available": True,
                        "url": "/api/v1/reports/referral/registrations/history",
                        "needs_book_selector": True,
                        "needs_date_range": True,
                        "formats": ["xlsx"],
                    },
                    {
                        "name": "Re-Sign Due List",
                        "available": True,
                        "url": "/api/v1/reports/referral/re-sign-due",
                        "is_critical": True,
                        "formats": ["pdf"],
                    },
                    {"name": "New Registrations", "available": False, "url": None},
                    {"name": "Resigned/Rolled Off", "available": False, "url": None},
                ],
                "total": 4,
                "available_count": 2,
            },
            {
                "name": "Employer Reports",
                "icon": "office-building",
                "priority": "P0/P1",
                "description": "Employer workforce and dispatch history",
                "reports": [
                    {
                        "name": "Employer Active List",
                        "available": True,
                        "url": "/api/v1/reports/referral/employers/active",
                        "formats": ["pdf", "xlsx"],
                    },
                    {
                        "name": "Employer Dispatch History",
                        "available": True,
                        "url": "/api/v1/reports/referral/employers/{employer_id}/dispatch-history",
                        "needs_employer_selector": True,
                        "needs_date_range": True,
                        "formats": ["pdf", "xlsx"],
                    },
                    {"name": "Contract Code Summary", "available": False, "url": None},
                ],
                "total": 3,
                "available_count": 2,
            },
            {
                "name": "Check Marks & Enforcement",
                "icon": "shield-check",
                "priority": "P1",
                "description": "Check mark tracking and violations",
                "reports": [
                    {
                        "name": "Check Mark Report",
                        "available": True,
                        "url": "/api/v1/reports/referral/check-marks",
                        "needs_book_selector": True,
                        "formats": ["pdf"],
                    },
                    {"name": "Suspension List", "available": False, "url": None},
                    {"name": "Blackout Periods", "available": False, "url": None},
                    {"name": "Violation History", "available": False, "url": None},
                ],
                "total": 4,
                "available_count": 1,
            },
            {
                "name": "Member Activity",
                "icon": "user",
                "priority": "P1",
                "description": "Individual member dispatch and referral activity",
                "reports": [
                    {
                        "name": "Member Dispatch Summary",
                        "available": False,
                        "url": None,
                    },
                    {"name": "Member Earnings", "available": False, "url": None},
                    {"name": "Member Queue History", "available": False, "url": None},
                    {"name": "Member Referral Card", "available": False, "url": None},
                    {
                        "name": "Member Compliance Status",
                        "available": False,
                        "url": None,
                    },
                ],
                "total": 5,
                "available_count": 0,
            },
            {
                "name": "Analytics & Trends",
                "icon": "chart-bar",
                "priority": "P2",
                "description": "Trend analysis and utilization metrics",
                "reports": [
                    {"name": "Dispatch Volume Trends", "available": False, "url": None},
                    {"name": "Book Utilization", "available": False, "url": None},
                    {"name": "Employer Utilization", "available": False, "url": None},
                    {"name": "Average Wait Times", "available": False, "url": None},
                    {"name": "Check Mark Trends", "available": False, "url": None},
                ],
                "total": 5,
                "available_count": 0,
            },
            {
                "name": "Projections & Ad-Hoc",
                "icon": "calculator",
                "priority": "P3",
                "description": "Forecasting and custom queries",
                "reports": [
                    {"name": "Queue Wait Projections", "available": False, "url": None},
                    {"name": "Dispatch Forecast", "available": False, "url": None},
                    {"name": "Custom Report Builder", "available": False, "url": None},
                ],
                "total": 3,
                "available_count": 0,
            },
        ]

    # --- Private Helpers ---

    def _get_next_event(self) -> dict:
        """Calculate next time-sensitive event (cutoff or window open/close)."""
        now = datetime.now().time()

        if now < self.CUTOFF_TIME:
            return {"event": "3 PM Cutoff", "time": "3:00 PM"}
        elif now < self.BIDDING_WINDOW_START:
            return {"event": "Bidding Opens", "time": "5:30 PM"}
        else:
            return {"event": "Morning Referral", "time": "7:00 AM"}
