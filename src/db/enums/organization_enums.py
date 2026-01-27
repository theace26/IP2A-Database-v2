"""Organization and Member related enums."""

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
