from enum import Enum


class CampaignMode(str, Enum):
    """Defines how the outreach email will be generated."""

    WITH_JD = "WITH_JD"
    WITHOUT_JD = "WITHOUT_JD"


class CampaignStatus(str, Enum):
    """Overall lifecycle of an outreach campaign."""

    # Campaign exists but email generation has not started yet.
    PENDING_GEN = "PENDING_GEN"

    # Email subject and body were generated and validated successfully,
    # but a Gmail draft has not yet been created.
    GENERATED = "GENERATED"

    # Gmail draft exists and is ready for human review.
    DRAFT_READY = "DRAFT_READY"

    # Human approved the Gmail draft for sending.
    APPROVED = "APPROVED"

    # Initial outreach email was sent successfully.
    SENT = "SENT"

    # Recipient replied to the campaign email.
    REPLIED = "REPLIED"

    # Human rejected the generated draft.
    REJECTED = "REJECTED"

    # Gmail or the recipient's mail server reported a bounce.
    BOUNCED = "BOUNCED"

    # Campaign was stopped manually or automatically.
    STOPPED = "STOPPED"

    # Generation, validation, or another safety-critical step failed.
    DEAD_LETTER = "DEAD_LETTER"


class FollowUpStatus(str, Enum):
    """Lifecycle of an individual follow-up step."""

    # Follow-up exists but has not yet been generated.
    PENDING = "PENDING"

    # Follow-up Gmail draft exists and is ready for review.
    DRAFT_READY = "DRAFT_READY"

    # Human approved the follow-up draft.
    APPROVED = "APPROVED"

    # Follow-up email was sent successfully.
    SENT = "SENT"

    # Follow-up was cancelled because of a reply, rejection,
    # bounce, stop request, or another terminal campaign state.
    CANCELLED = "CANCELLED"


class TelemetryType(str, Enum):
    """Types of email engagement events recorded by the system."""

    OPEN = "OPEN"
    CLICK = "CLICK"