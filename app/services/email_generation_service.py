import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.enums import CampaignStatus
from app.models.master_profile import MasterProfile
from app.services.email_validator import (
    EmailValidationError,
    validate_generated_email,
)
from app.services.ollama_service import OllamaService
from app.services.prompt_builder import PromptBuilder


class EmailGenerationError(RuntimeError):
    """Raised when an outreach draft cannot be generated safely."""


class EmailGenerationService:
    def __init__(self) -> None:
        self.ollama_service = OllamaService()

    @staticmethod
    def _parse_generated_output(output: str) -> tuple[str, str]:
        subject_match = re.search(
            r"Subject:\s*(.+?)(?:\n|$)",
            output,
            flags=re.IGNORECASE,
        )

        body_match = re.search(
            r"Body:\s*(.+)",
            output,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if not subject_match or not body_match:
            raise EmailGenerationError(
                "Ollama response did not contain the required "
                "'Subject:' and 'Body:' sections."
            )

        subject = subject_match.group(1).strip()
        body = body_match.group(1).strip()

        if not subject:
            raise EmailGenerationError("Generated subject is empty.")

        if not body:
            raise EmailGenerationError("Generated email body is empty.")

        return subject, body

    def generate_for_campaign(
        self,
        db: Session,
        campaign: Campaign,
    ) -> Campaign:
        master_profile = db.scalar(
            select(MasterProfile)
            .where(MasterProfile.is_approved.is_(True))
            .order_by(MasterProfile.id.desc())
        )

        if not master_profile:
            raise EmailGenerationError(
                "No approved Master Profile exists."
            )

        prompt = PromptBuilder.build(
            master_profile=master_profile,
            campaign=campaign,
        )

        try:
            generated_output = self.ollama_service.generate(prompt)
            subject, body = self._parse_generated_output(generated_output)

            validate_generated_email(
                generated_text=body,
                resume_text=master_profile.resume_text,
            )

            campaign.email_subject = subject
            campaign.email_body = body
            campaign.status = CampaignStatus.DRAFT_READY

            db.commit()
            db.refresh(campaign)

            return campaign

        except (EmailValidationError, EmailGenerationError) as exc:
            db.rollback()

            campaign.status = CampaignStatus.DEAD_LETTER
            campaign.stop_reason = str(exc)

            db.add(campaign)
            db.commit()
            db.refresh(campaign)

            raise EmailGenerationError(str(exc)) from exc

        except Exception as exc:
            db.rollback()

            campaign.status = CampaignStatus.DEAD_LETTER
            campaign.stop_reason = (
                f"Unexpected generation failure: {exc}"
            )

            db.add(campaign)
            db.commit()
            db.refresh(campaign)

            raise EmailGenerationError(
                "Email generation failed unexpectedly."
            ) from exc