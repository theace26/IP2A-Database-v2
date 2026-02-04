"""
Phase 7 Enums - Referral & Dispatch System

Created: February 4, 2026 (Week 20 Session A)
Based on: IBEW Local 46 Referral Procedures (Effective October 4, 2024)

These enums support the LaborPower replacement functionality.
"""
from enum import Enum


class BookClassification(str, Enum):
    """Job classifications for referral books."""
    INSIDE_WIREPERSON = "inside_wireperson"
    TRADESHOW = "tradeshow"
    SEATTLE_SCHOOL = "seattle_school"
    SOUND_COMM = "sound_comm"
    MARINE = "marine"
    STOCKPERSON = "stockperson"
    LIGHT_FIXTURE = "light_fixture"
    RESIDENTIAL = "residential"
    TECHNICIAN = "technician"
    UTILITY_WORKER = "utility_worker"
    TERO_APPRENTICE = "tero_apprentice"


class BookRegion(str, Enum):
    """Geographic regions for referral books.

    Each region has SEPARATE check mark tracking per Local 46 rules.
    Requests for one region don't generate check marks for other regions.
    """
    SEATTLE = "seattle"
    BREMERTON = "bremerton"
    PORT_ANGELES = "port_angeles"


class RegistrationStatus(str, Enum):
    """Status of a book registration."""
    REGISTERED = "registered"       # Active on the book, waiting for dispatch
    DISPATCHED = "dispatched"       # Currently dispatched to a job
    ROLLED_OFF = "rolled_off"       # Removed from book (check marks, quit, etc.)
    RESIGNED = "resigned"           # Member voluntarily left the book
    EXEMPT = "exempt"               # Exempt from check marks and re-sign


class RegistrationAction(str, Enum):
    """Actions that can occur on a registration.

    Used in RegistrationActivity for audit trail.
    """
    REGISTER = "register"                   # Initial registration
    RE_SIGN = "re_sign"                     # 30-day re-sign
    RE_REGISTER = "re_register"             # Re-register after being rolled off
    CHECK_MARK = "check_mark"               # Check mark recorded
    CHECK_MARK_LOST = "check_mark_lost"     # Lost a check mark opportunity
    CHECK_MARK_RESTORED = "check_mark_restored"  # Dispatcher restored check mark
    ROLL_OFF = "roll_off"                   # Rolled off the book
    DISPATCH = "dispatch"                   # Dispatched to a job
    RESIGN = "resign"                       # Member voluntarily resigned
    RESTORE = "restore"                     # Position restored (short call end)
    EXEMPT_START = "exempt_start"           # Exempt status granted
    EXEMPT_END = "exempt_end"               # Exempt status revoked
    POSITION_CHANGE = "position_change"     # Queue position changed
    INTERNET_BID = "internet_bid"           # Submitted internet bid
    BID_ACCEPT = "bid_accept"               # Bid was accepted
    BID_REJECT = "bid_reject"               # Bid was rejected
    MANUAL_EDIT = "manual_edit"             # Manual dispatcher edit


class ExemptReason(str, Enum):
    """Reasons for exempt status (no re-sign or check marks required).

    Per Local 46 rules, exempt status can last up to 6 months
    unless extended by Business Manager.
    """
    MILITARY = "military"
    UNION_BUSINESS = "union_business"
    SALTING = "salting"
    MEDICAL = "medical"
    JURY_DUTY = "jury_duty"
    UNDER_SCALE = "under_scale"
    TRAVELING = "traveling"
    OTHER = "other"


class RolloffReason(str, Enum):
    """Reasons for being rolled off the book."""
    CHECK_MARKS = "check_marks"             # 3rd check mark
    QUIT = "quit"                           # Quit job (rolls off ALL books)
    DISCHARGED = "discharged"               # Fired (rolls off ALL books)
    FAILED_RE_SIGN = "failed_re_sign"       # Missed 30-day re-sign deadline
    NINETY_DAY_RULE = "90_day_rule"         # 90-day inactivity
    BID_REJECT_QUIT = "bid_reject_quit"     # Rejected after accepting bid (= quit)
    EXPIRED = "expired"                     # Max days on book exceeded
    MANUAL = "manual"                       # Dispatcher manual removal


class NoCheckMarkReason(str, Enum):
    """Reasons a labor request doesn't generate check marks.

    Per Local 46 rules, certain requests are exempt from check marks.
    """
    SPECIALTY = "specialty"                 # Specialty skills not in CBA
    MOU_JOBSITE = "mou_jobsite"             # MOU jobsite
    EARLY_START = "early_start"             # Start time before 6:00 AM
    UNDER_SCALE = "under_scale"             # Under scale work recovery
    VARIOUS_LOCATION = "various_location"   # Various location requests
    SHORT_CALL = "short_call"               # Short call request
    EMPLOYER_REJECTION = "employer_rejection"  # Rejected by employer


class LaborRequestStatus(str, Enum):
    """Status of a labor request from an employer."""
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BidStatus(str, Enum):
    """Status of a job bid (internet/email bidding)."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class DispatchMethod(str, Enum):
    """How the dispatch was made."""
    MORNING_REFERRAL = "morning_referral"   # Normal hall dispatch
    INTERNET_BID = "internet_bid"           # Online bidding (5:30 PM - 7:00 AM)
    EMAIL_BID = "email_bid"                 # Email bidding
    IN_PERSON = "in_person"                 # In-person request
    BY_NAME = "by_name"                     # Foreperson by name
    EMERGENCY = "emergency"                 # Emergency call-out


class DispatchStatus(str, Enum):
    """Status of a dispatch."""
    DISPATCHED = "dispatched"               # Assigned, not yet started
    CHECKED_IN = "checked_in"               # Checked in with employer
    WORKING = "working"                     # Currently working
    COMPLETED = "completed"                 # Job completed normally
    TERMINATED = "terminated"               # Terminated (RIF, quit, fired)
    REJECTED = "rejected"                   # Rejected the dispatch
    NO_SHOW = "no_show"                     # Failed to show up


class TermReason(str, Enum):
    """Employment termination reasons."""
    RIF = "rif"                             # Reduction in Force (layoff)
    QUIT = "quit"                           # Voluntary quit
    FIRED = "fired"                         # Discharged by employer
    LAID_OFF = "laid_off"                   # Laid off (end of work)
    SHORT_CALL_END = "short_call_end"       # Short call period ended
    CONTRACT_END = "contract_end"           # Contract completion
    NINETY_DAY_RULE = "90_day_rule"         # 90-day rule termination
    TURNAROUND = "turnaround"               # Turnaround
    UNDER_SCALE = "under_scale"             # Under scale termination


class JobClass(str, Enum):
    """Job classifications for dispatch.

    These map to the contract codes from LaborPower analysis.
    """
    JRY_WIRE = "JRY WIRE"                   # Journeyman Wireman
    SOUND = "SOUND"                         # Sound & Communication
    RESIDENTIAL = "RESIDENTIAL"
    MARINE = "MARINE"
    STOCKPERSON = "STOCKPERSON"
    LIGHT_FIXTURE = "LIGHT_FIXTURE"
    TRADESHOW = "TRADESHOW"
    TECHNICIAN = "TECHNICIAN"
    UTILITY_WORKER = "UTILITY_WORKER"


class MemberType(str, Enum):
    """IBEW membership card types."""
    A = "A"                                 # Journeyman Inside Wireman
    BA = "BA"                               # BA card
    CE = "CE"                               # Construction Electrician
    CW = "CW"                               # Construction Wireman
    APPRENTICE = "APP"                      # Apprentice


class ReferralStatus(str, Enum):
    """Member's overall referral availability."""
    AVAILABLE = "available"                 # Available for dispatch
    WORKING = "working"                     # Currently employed
    DISPATCHED = "dispatched"               # Dispatched, not yet started
    EXEMPT = "exempt"                       # Exempt status
    SUSPENDED = "suspended"                 # Bidding suspended


class ActivityCode(str, Enum):
    """Transaction activity codes (LaborPower compatibility)."""
    PAYMENT = "X"
    VOID = "V"
    DCO = "D"                               # Dues Check-Off
    NEW_MEMBER = "N"
    ADJUSTMENT = "A"


class PaymentSource(str, Enum):
    """Payment sources for transactions."""
    DCO = "dco"                             # Dues Check-Off
    WEB = "web"                             # Web payment
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "cc"
    MAIL = "mail"
    STRIPE_CARD = "stripe_card"
    STRIPE_ACH = "stripe_ach"


class DispatchType(str, Enum):
    """Type of dispatch."""
    NORMAL = "normal"                       # Regular dispatch
    SHORT_CALL = "short_call"               # Short call (<=10 business days)
    EMERGENCY = "emergency"                 # Emergency dispatch


class AgreementType(str, Enum):
    """Agreement types for special dispatch categories."""
    STANDARD = "standard"
    PLA = "pla"                             # Project Labor Agreement
    CWA = "cwa"                             # Community Workforce Agreement
    TERO = "tero"                           # Tribal Employment Rights Ordinance
