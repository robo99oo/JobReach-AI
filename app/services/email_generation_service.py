import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.enums import CampaignStatus
from app.models.master_profile import MasterProfile
from app.services.deterministic_email_builder import (
    DeterministicEmailBuilder,
    DeterministicEmailBuilderError,
)
from app.services.email_validator import (
    EmailValidationError,
    validate_generated_email,
)
from app.services.ollama_service import OllamaService
from app.services.prompt_builder import PromptBuilder


class EmailGenerationError(RuntimeError):
    """Raised when an outreach draft cannot be generated safely."""


class EmailGenerationService:
    MAX_GENERATION_ATTEMPTS = 3

    def __init__(self) -> None:
        self.ollama_service = OllamaService()

    @staticmethod
    def _parse_generated_output(
        output: str,
    ) -> tuple[str, str]:
        """
        Parse the subject and body from inconsistent Ollama output.

        Supported formats:
        - <SUBJECT> and <BODY> tags
        - Subject: and Body:
        - Company-name tags
        - Plain text with subject on the first line
        """

        cleaned_output = output.strip().strip('"').strip("'")

        if not cleaned_output:
            raise EmailGenerationError(
                "Ollama returned an empty response."
            )

        cleaned_output = re.sub(
            r"<\s*previously\s+counted\s+words\s*:[^>]+>",
            "",
            cleaned_output,
            flags=re.IGNORECASE,
        ).strip()

        subject: str | None = None
        body: str | None = None

        subject_match = re.search(
            r"<\s*subject\s*>\s*(.*?)\s*"
            r"<\s*/\s*subject\s*>",
            cleaned_output,
            flags=re.IGNORECASE | re.DOTALL,
        )

        body_match = re.search(
            r"<\s*body\s*>\s*(.*?)\s*"
            r"<\s*/\s*body\s*>",
            cleaned_output,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if subject_match:
            subject = subject_match.group(1).strip()

        if body_match:
            body = body_match.group(1).strip()

        if subject is None:
            legacy_subject_match = re.search(
                r"(?:\*\*)?subject(?:\*\*)?"
                r"\s*:\s*(.+?)(?:\n|$)",
                cleaned_output,
                flags=re.IGNORECASE,
            )

            if legacy_subject_match:
                subject = legacy_subject_match.group(1).strip()

        if body is None:
            legacy_body_match = re.search(
                r"(?:\*\*)?body(?:\*\*)?"
                r"\s*:\s*(.+)",
                cleaned_output,
                flags=re.IGNORECASE | re.DOTALL,
            )

            if legacy_body_match:
                body = legacy_body_match.group(1).strip()

        if subject is None:
            arbitrary_tag_match = re.search(
                r"<\s*([^>/]+?)\s*>\s*(.*?)\s*"
                r"<\s*/\s*\1\s*>",
                cleaned_output,
                flags=re.IGNORECASE | re.DOTALL,
            )

            if arbitrary_tag_match:
                tag_name = arbitrary_tag_match.group(1).strip().lower()
                tagged_content = arbitrary_tag_match.group(2).strip()

                ignored_tags = {
                    "subject",
                    "body",
                    "previously counted words",
                }

                if tag_name not in ignored_tags:
                    if body:
                        subject = tagged_content
                    else:
                        tagged_lines = [
                            line.strip()
                            for line in tagged_content.splitlines()
                            if line.strip()
                        ]

                        if len(tagged_lines) >= 2:
                            subject = tagged_lines[0]
                            body = "\n".join(
                                tagged_lines[1:]
                            ).strip()

        if subject is None or body is None:
            normalized_output = re.sub(
                r"<[^>]+>",
                "",
                cleaned_output,
            ).strip()

            paragraphs = re.split(
                r"\n\s*\n",
                normalized_output,
                maxsplit=1,
            )

            if len(paragraphs) == 2:
                if subject is None:
                    subject = paragraphs[0].strip()

                if body is None:
                    body = paragraphs[1].strip()

            else:
                lines = [
                    line.strip()
                    for line in normalized_output.splitlines()
                    if line.strip()
                ]

                if len(lines) >= 2:
                    if subject is None:
                        subject = lines[0]

                    if body is None:
                        body = "\n".join(lines[1:]).strip()

        if not subject:
            raise EmailGenerationError(
                "Generated email subject is missing."
            )

        if not body:
            raise EmailGenerationError(
                "Generated email body is missing."
            )

        subject = subject.splitlines()[0].strip()

        body = re.sub(
            r"<\s*previously\s+counted\s+words\s*:[^>]+>",
            "",
            body,
            flags=re.IGNORECASE,
        ).strip()

        return subject, body

    @staticmethod
    def _build_retry_prompt(
        original_prompt: str,
        previous_output: str,
        validation_error: str,
    ) -> str:
        """
        Build a corrective prompt using the exact failed output.
        """

        return f"""
{original_prompt}

==============================
PREVIOUS ATTEMPT FAILED
==============================

Previous output:

{previous_output}

Validation failure:

{validation_error}

Rewrite the email completely.

MANDATORY REPAIR RULES:

- Use only facts supplied in the Master Profile and Campaign.
- The BODY must contain between 120 and 130 words.
- Count only words inside the BODY tags.
- If the previous body was too short, expand it using supported
  factual details from the Master Profile.
- If the previous body was too long, remove repetition.
- Mention no more than three supported skills or named projects.
- Do not invent projects, achievements, metrics, technologies,
  experience, responsibilities, vacancies, hiring requirements,
  company initiatives, products, or company needs.
- For WITHOUT_JD mode, do not mention a vacancy, opening, posting,
  hiring requirement, "this role", or the recipient's team needs.
- Include a polite request for a short conversation.
- Include the candidate's professional sign-off inside the BODY.
- The opening subject tag must literally be <SUBJECT>.
- Do not replace SUBJECT with the company name.
- The opening body tag must literally be <BODY>.
- Do not add word-count notes.
- Do not add additional tags.
- Do not use markdown or code fences.
- Return no explanation before or after the email.

Return exactly:

<SUBJECT>
One concise subject line
</SUBJECT>

<BODY>
A complete factual email body containing 120 to 130 words
</BODY>
""".strip()

    @staticmethod
    def _validate_email(
        *,
        body: str,
        master_profile: MasterProfile,
        campaign: Campaign,
    ) -> None:
        validate_generated_email(
            generated_text=body,
            resume_text=master_profile.resume_text,
            is_without_jd=(
                campaign.mode.value == "WITHOUT_JD"
            ),
        )

    @staticmethod
    def _save_generated_email(
        *,
        db: Session,
        campaign: Campaign,
        subject: str,
        body: str,
        stop_reason: str | None = None,
    ) -> Campaign:
        campaign.email_subject = subject
        campaign.email_body = body
        campaign.status = CampaignStatus.GENERATED
        campaign.stop_reason = stop_reason

        db.add(campaign)
        db.commit()
        db.refresh(campaign)

        return campaign

    def generate_for_campaign(
        self,
        db: Session,
        campaign: Campaign,
    ) -> Campaign:
        """
        Generate and validate an outreach email.

        Workflow:
        1. Try Ollama up to three times.
        2. Validate every generated body.
        3. Use the deterministic builder if all LLM attempts fail.
        4. Move to DEAD_LETTER only if both methods fail.
        """

        master_profile = db.scalar(
            select(MasterProfile)
            .where(MasterProfile.is_approved.is_(True))
            .order_by(MasterProfile.id.desc())
        )

        if not master_profile:
            raise EmailGenerationError(
                "No approved Master Profile exists."
            )

        original_prompt = PromptBuilder.build(
            master_profile=master_profile,
            campaign=campaign,
        )

        current_prompt = original_prompt
        previous_output = ""
        last_error: Exception | None = None

        for attempt in range(
            1,
            self.MAX_GENERATION_ATTEMPTS + 1,
        ):
            try:
                generated_output = self.ollama_service.generate(
                    current_prompt
                )

                previous_output = generated_output

                print("\n========== RAW OLLAMA OUTPUT ==========")
                print(repr(generated_output))
                print("=======================================\n")

                subject, body = self._parse_generated_output(
                    generated_output
                )

                self._validate_email(
                    body=body,
                    master_profile=master_profile,
                    campaign=campaign,
                )

                return self._save_generated_email(
                    db=db,
                    campaign=campaign,
                    subject=subject,
                    body=body,
                )

            except (
                EmailValidationError,
                EmailGenerationError,
            ) as exc:
                last_error = exc

                if attempt < self.MAX_GENERATION_ATTEMPTS:
                    current_prompt = self._build_retry_prompt(
                        original_prompt=original_prompt,
                        previous_output=previous_output,
                        validation_error=str(exc),
                    )
                    continue

                break

            except Exception as exc:
                db.rollback()
                last_error = exc
                break

        # --------------------------------------------------
        # Deterministic fallback after all Ollama attempts fail
        # --------------------------------------------------
        try:
            subject, body = DeterministicEmailBuilder.build(
                master_profile=master_profile,
                campaign=campaign,
            )

            self._validate_email(
                body=body,
                master_profile=master_profile,
                campaign=campaign,
            )

            return self._save_generated_email(
                db=db,
                campaign=campaign,
                subject=subject,
                body=body,
                stop_reason=(
                    "Ollama generation failed validation. "
                    "Deterministic fallback used."
                ),
            )

        except (
            DeterministicEmailBuilderError,
            EmailValidationError,
        ) as fallback_error:
            db.rollback()

            final_error = (
                f"Ollama failure: {last_error}. "
                f"Deterministic fallback failure: {fallback_error}"
            )

        except Exception as fallback_error:
            db.rollback()

            final_error = (
                f"Ollama failure: {last_error}. "
                f"Unexpected deterministic fallback failure: "
                f"{fallback_error}"
            )

        campaign.status = CampaignStatus.DEAD_LETTER
        campaign.stop_reason = (
            "Email generation failed after "
            f"{self.MAX_GENERATION_ATTEMPTS} Ollama attempts "
            f"and deterministic fallback. {final_error}"
        )

        db.add(campaign)
        db.commit()
        db.refresh(campaign)

        raise EmailGenerationError(
            campaign.stop_reason
        ) from last_error