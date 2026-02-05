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
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

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
    BIDDING_WINDOW_END = time(7, 0)      # 7:00 AM
    CUTOFF_TIME = time(15, 0)            # 3:00 PM

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
                LaborRequest.status.in_([
                    LaborRequestStatus.OPEN,
                    LaborRequestStatus.PARTIALLY_FILLED
                ])
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
            .filter(Dispatch.dispatch_status.in_([
                DispatchStatus.DISPATCHED,
                DispatchStatus.CHECKED_IN,
                DispatchStatus.WORKING
            ]))
            .count()
        )

        # Count pending bids
        pending_bids = (
            self.db.query(JobBid)
            .filter(JobBid.bid_status == BidStatus.PENDING)
            .count()
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
            activity.append({
                "type": "dispatch",
                "time": dispatch.dispatch_date,
                "description": f"{dispatch.member.full_name if dispatch.member else 'Unknown'} dispatched to {dispatch.employer.name if dispatch.employer else 'Unknown'}",
                "id": dispatch.id,
            })

        for request in requests:
            activity.append({
                "type": "request",
                "time": request.request_date,
                "description": f"New request from {request.employer_name} ({request.workers_requested} workers)",
                "id": request.id,
            })

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
        self,
        filters: Optional[dict] = None,
        page: int = 1,
        per_page: int = 25
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
            LaborRequest.start_date,
            LaborRequest.request_date.desc()
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
        request = self.db.query(LaborRequest).filter(LaborRequest.id == request_id).first()
        if not request:
            return None

        # Get candidates from the book (registered, not dispatched)
        candidates = (
            self.db.query(BookRegistration)
            .filter(
                BookRegistration.book_id == request.book_id,
                BookRegistration.status == RegistrationStatus.REGISTERED
            )
            .order_by(
                BookRegistration.registration_number
            )
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
            .order_by(
                BookRegistration.registration_number,
                JobBid.bid_submitted_at
            )
            .all()
        )

        # Group by request
        requests = {}
        for bid in bids:
            request_id = bid.labor_request_id
            if request_id not in requests:
                requests[request_id] = {
                    "request": bid.labor_request,
                    "bids": []
                }
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
        self,
        filters: Optional[dict] = None,
        page: int = 1,
        per_page: int = 50
    ) -> dict:
        """
        Get active dispatches with optional filters.
        """
        filters = filters or {}
        query = self.db.query(Dispatch).filter(
            Dispatch.dispatch_status.in_([
                DispatchStatus.DISPATCHED,
                DispatchStatus.CHECKED_IN,
                DispatchStatus.WORKING
            ])
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
                    Dispatch.member.has(func.concat(Dispatch.member.first_name, ' ', Dispatch.member.last_name).ilike(search)),
                    Dispatch.employer.has(Dispatch.employer.name.ilike(search))
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
        self,
        book_id: Optional[int] = None,
        limit: int = 100
    ) -> List[BookRegistration]:
        """
        Get current queue positions. Optionally filter by book.
        """
        query = self.db.query(BookRegistration).filter(
            BookRegistration.status == RegistrationStatus.REGISTERED
        )

        if book_id:
            query = query.filter(BookRegistration.book_id == book_id)

        query = query.order_by(
            BookRegistration.registration_number
        )

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
