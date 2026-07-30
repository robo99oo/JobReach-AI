from enum import Enum


class CampaignMode(str, Enum):
    WITH_JD = "WITH_JD"
    WITHOUT_JD = "WITHOUT_JD"


class CampaignStatus(str, Enum):
    PENDING_GEN = "PENDING_GEN"
    DRAFT_READY = "DRAFT_READY"
    APPROVED = "APPROVED"
    SENT = "SENT"
    REPLIED = "REPLIED"
    REJECTED = "REJECTED"
    BOUNCED = "BOUNCED"
    STOPPED = "STOPPED"
    DEAD_LETTER = "DEAD_LETTER"


class FollowUpStatus(str, Enum):
    PENDING = "PENDING"
    DRAFT_READY = "DRAFT_READY"
    APPROVED = "APPROVED"
    SENT = "SENT"
    CANCELLED = "CANCELLED"


class TelemetryType(str, Enum):
    OPEN = "OPEN"
    CLICK = "CLICK"