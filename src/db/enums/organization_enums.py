"""Organization and Member related enums for Phase 1 union operations."""

import enum


class OrganizationType(str, enum.Enum):
    """Type of organization."""

    EMPLOYER = "employer"
    UNION = "union"
    TRAINING_PARTNER = "training_partner"
    JATC = "jatc"


class MemberStatus(str, enum.Enum):
    """Member status within the union."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    RETIRED = "retired"
    DECEASED = "deceased"


class MemberClassification(str, enum.Enum):
    """Member classification for dues and benefits."""

    APPRENTICE_1ST_YEAR = "apprentice_1"
    APPRENTICE_2ND_YEAR = "apprentice_2"
    APPRENTICE_3RD_YEAR = "apprentice_3"
    APPRENTICE_4TH_YEAR = "apprentice_4"
    APPRENTICE_5TH_YEAR = "apprentice_5"
    JOURNEYMAN = "journeyman"
    FOREMAN = "foreman"
    RETIREE = "retiree"
    HONORARY = "honorary"


class SaltingScore(int, enum.Enum):
    """Employer salting receptiveness score (1-5)."""

    HOSTILE = 1
    RESISTANT = 2
    NEUTRAL = 3
    RECEPTIVE = 4
    SUPPORTIVE = 5


class AuditAction(str, enum.Enum):
    """Type of audit action."""

    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


# --- Phase 2: Union Operations Enums ---


class SALTingActivityType(str, enum.Enum):
    """Type of SALTing/organizing activity."""

    OUTREACH = "outreach"
    SITE_VISIT = "site_visit"
    LEAFLETING = "leafleting"
    ONE_ON_ONE = "one_on_one"
    MEETING = "meeting"
    PETITION_DRIVE = "petition_drive"
    CARD_SIGNING = "card_signing"
    INFORMATION_SESSION = "information_session"
    OTHER = "other"


class SALTingOutcome(str, enum.Enum):
    """Outcome of a SALTing activity."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    NO_CONTACT = "no_contact"


class BenevolenceReason(str, enum.Enum):
    """Reason for benevolence fund application."""

    MEDICAL = "medical"
    DEATH_IN_FAMILY = "death_in_family"
    HARDSHIP = "hardship"
    DISASTER = "disaster"
    OTHER = "other"


class BenevolenceStatus(str, enum.Enum):
    """Status of a benevolence application."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"


class BenevolenceReviewLevel(str, enum.Enum):
    """Review level in benevolence approval workflow."""

    VP = "vp"
    ADMIN = "admin"
    MANAGER = "manager"
    PRESIDENT = "president"


class BenevolenceReviewDecision(str, enum.Enum):
    """Decision made by a reviewer."""

    APPROVED = "approved"
    DENIED = "denied"
    NEEDS_INFO = "needs_info"
    DEFERRED = "deferred"


class GrievanceStep(str, enum.Enum):
    """Current step in grievance process."""

    STEP_1 = "step_1"
    STEP_2 = "step_2"
    STEP_3 = "step_3"
    ARBITRATION = "arbitration"


class GrievanceStatus(str, enum.Enum):
    """Status of a grievance."""

    OPEN = "open"
    INVESTIGATION = "investigation"
    HEARING = "hearing"
    SETTLED = "settled"
    WITHDRAWN = "withdrawn"
    ARBITRATION = "arbitration"
    CLOSED = "closed"


class GrievanceStepOutcome(str, enum.Enum):
    """Outcome of a grievance step meeting."""

    DENIED = "denied"
    SETTLED = "settled"
    ADVANCED = "advanced"
