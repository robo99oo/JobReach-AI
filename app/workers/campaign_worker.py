from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.enums import CampaignStatus
from app.services.email_generation_service import (
    EmailGenerationError,
    EmailGenerationService,
)
from app.services.gmail_service import (
    GmailService,
    GmailServiceError,
)


class CampaignWorkerError(RuntimeError):
    """Raised when campaign processing fails."""


class CampaignWorker:

    def __init__(self):
        self.email_service = EmailGenerationService()

    def process_campaign(
        self,
        db: Session,
        campaign: Campaign,
    ) -> Campaign:

        if campaign.status != CampaignStatus.PENDING_GEN:
            raise CampaignWorkerError(
                "Campaign is not ready for processing."
            )

        try:

            campaign = self.email_service.generate_for_campaign(
                db=db,
                campaign=campaign,
            )

            draft = GmailService.create_draft(
                recipient_email=campaign.recipient_email,
                subject=campaign.email_subject,
                body=campaign.email_body,
            )

            campaign.gmail_draft_id = draft["id"]
            campaign.gmail_message_id = draft["message"]["id"]
            campaign.gmail_thread_id = draft["message"]["threadId"]

            campaign.status = CampaignStatus.DRAFT_READY

            db.commit()
            db.refresh(campaign)

            return campaign

        except (
            EmailGenerationError,
            GmailServiceError,
        ) as exc:

            db.rollback()

            campaign.status = CampaignStatus.DEAD_LETTER
            campaign.stop_reason = str(exc)

            db.add(campaign)
            db.commit()

            raise CampaignWorkerError(str(exc)) from exc