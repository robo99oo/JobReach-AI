import re

from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.enums import (
    CampaignStatus,
    FollowUpStatus,
)
from app.models.follow_up_step import FollowUpStep
from app.services.ollama_service import OllamaService


class FollowUpGenerationError(Exception):
    """Raised when follow-up generation fails."""


class FollowUpGenerationService:
    MAX_GENERATION_ATTEMPTS = 3

    def __init__(self) -> None:
        self.ollama = OllamaService()

    @staticmethod
    def _parse_output(output: str) -> tuple[str, str]:
        """
        Parse tagged, malformed-tagged, or plain-text Ollama output.
        """

        cleaned_output = output.strip()

        if not cleaned_output:
            raise FollowUpGenerationError(
                "Ollama returned an empty follow-up."
            )

        subject_match = re.search(
            r"<\s*subject\s*>\s*(.*?)\s*<\s*/\s*subject\s*>",
            cleaned_output,
            flags=re.IGNORECASE | re.DOTALL,
        )

        body_match = re.search(
            r"<\s*body\s*>\s*(.*?)\s*<\s*/\s*body\s*>",
            cleaned_output,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if subject_match and body_match:
            subject = subject_match.group(1).strip()
            body = body_match.group(1).strip()

        else:
            normalized_output = re.sub(
                r"<\s*/?\s*subject\s*>",
                "",
                cleaned_output,
                flags=re.IGNORECASE,
            ).strip()

            normalized_output = re.sub(
                r"<\s*/?\s*body\s*>",
                "",
                normalized_output,
                flags=re.IGNORECASE,
            ).strip()

            sections = re.split(
                r"\n\s*\n",
                normalized_output,
                maxsplit=1,
            )

            if len(sections) < 2:
                raise FollowUpGenerationError(
                    "Ollama output did not contain both "
                    "a subject and body."
                )

            subject = sections[0].strip()
            body = sections[1].strip()

        if not subject:
            raise FollowUpGenerationError(
                "Generated follow-up subject is empty."
            )

        if not body:
            raise FollowUpGenerationError(
                "Generated follow-up body is empty."
            )

        forbidden_placeholders = [
            "[recipient's name]",
            "[recipient name]",
            "[name]",
            "<recipient>",
            "dear [recipient's name]",
            "dear [recipient name]",
        ]

        normalized_body = body.lower()

        if any(
            placeholder in normalized_body
            for placeholder in forbidden_placeholders
        ):
            raise FollowUpGenerationError(
                "Generated follow-up contains an unresolved placeholder."
            )

        return subject, body

    @staticmethod
    def _validate_body(body: str) -> None:
        word_count = len(body.split())

        if not 70 <= word_count <= 120:
            raise FollowUpGenerationError(
                f"Follow-up contains {word_count} words. "
                "It must contain between 70 and 120 words."
            )

    @staticmethod
    def _build_prompt(
        campaign: Campaign,
        follow_up: FollowUpStep,
        validation_error: str | None = None,
    ) -> str:
        retry_section = ""

        if validation_error:
            retry_section = f"""
The previous attempt failed validation.

Failure reason:
{validation_error}

Generate the follow-up again from scratch.
"""

        recipient_name = (
            campaign.contact_name.strip()
            if campaign.contact_name
            else "Hiring Manager"
        )

        return f"""
You are writing a professional follow-up email.

RECIPIENT NAME:

{recipient_name}

ORIGINAL SUBJECT:

{campaign.email_subject}

ORIGINAL EMAIL:

{campaign.email_body}

FOLLOW-UP STEP:

{follow_up.step_number}

STRICT RULES:

- Use only information from the original email.
- Never invent achievements, metrics, skills, responsibilities,
  company initiatives, vacancies, job requirements, or experience.
- State politely that this is a follow-up.
- Ask whether the recipient had an opportunity to review the earlier email.
- Keep the BODY between 70 and 120 words.
- Address the recipient using the supplied recipient name.
- If the recipient name is unavailable, use "Hello".
- Never use placeholders such as [Recipient's Name], [Name], or <recipient>.
- Do not use bullet points.
- Do not use markdown.
- Do not include explanations.
- Keep the tone concise, respectful, and non-pushy.
- Put the sign-off inside the BODY section.
- Do not add extra sections.

{retry_section}

Return only this structure:

<SUBJECT>
One concise follow-up subject line
</SUBJECT>

<BODY>
Complete follow-up email body containing 70 to 120 words
</BODY>
""".strip()

    def generate(
        self,
        db: Session,
        campaign: Campaign,
        follow_up: FollowUpStep,
    ) -> FollowUpStep:
        if campaign.status != CampaignStatus.SENT:
            raise FollowUpGenerationError(
                "Campaign must be SENT before generating follow-ups."
            )

        if follow_up.status != FollowUpStatus.PENDING:
            raise FollowUpGenerationError(
                "Only PENDING follow-ups can be generated."
            )

        last_error: Exception | None = None
        validation_error: str | None = None

        for attempt in range(
            1,
            self.MAX_GENERATION_ATTEMPTS + 1,
        ):
            try:
                prompt = self._build_prompt(
                    campaign=campaign,
                    follow_up=follow_up,
                    validation_error=validation_error,
                )

                output = self.ollama.generate(prompt)

                print(
                    "\n========== RAW FOLLOW-UP OLLAMA OUTPUT =========="
                )
                print(repr(output))
                print(
                    "=================================================\n"
                )

                subject, body = self._parse_output(output)
                self._validate_body(body)

                follow_up.subject = subject
                follow_up.body = body
                follow_up.status = FollowUpStatus.DRAFT_READY
                follow_up.cancellation_reason = None

                db.add(follow_up)
                db.commit()
                db.refresh(follow_up)

                return follow_up

            except FollowUpGenerationError as exc:
                last_error = exc
                validation_error = str(exc)

                if attempt < self.MAX_GENERATION_ATTEMPTS:
                    continue

                break

            except Exception as exc:
                db.rollback()

                raise FollowUpGenerationError(
                    f"Unexpected follow-up generation failure: {exc}"
                ) from exc

        db.rollback()

        final_error = (
            str(last_error)
            if last_error
            else "Follow-up generation failed."
        )

        raise FollowUpGenerationError(
            f"Follow-up generation failed after "
            f"{self.MAX_GENERATION_ATTEMPTS} attempts: "
            f"{final_error}"
        ) from last_error