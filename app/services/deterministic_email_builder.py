import re

from app.models.campaign import Campaign
from app.models.master_profile import MasterProfile


class DeterministicEmailBuilderError(RuntimeError):
    """Raised when a safe deterministic email cannot be built."""


class DeterministicEmailBuilder:
    """
    Build a factual outreach email without relying on an LLM.

    Only approved Master Profile and Campaign fields are used.
    """

    @staticmethod
    def _split_values(
        value: str | None,
        *,
        limit: int,
    ) -> list[str]:
        """
        Split comma-, semicolon-, or newline-separated profile values.
        """

        if not value:
            return []

        parts = re.split(
            r"[,;\n|]+",
            value,
        )

        cleaned_parts: list[str] = []

        for part in parts:
            cleaned = re.sub(
                r"\s+",
                " ",
                part.strip(),
            )

            if cleaned and cleaned not in cleaned_parts:
                cleaned_parts.append(cleaned)

            if len(cleaned_parts) >= limit:
                break

        return cleaned_parts

    @staticmethod
    def _format_items(items: list[str]) -> str:
        """
        Format values as natural English.

        Examples:
        ["Python"] -> "Python"
        ["Python", "FastAPI"] -> "Python and FastAPI"
        ["Python", "FastAPI", "RAG"] -> "Python, FastAPI, and RAG"
        """

        if not items:
            return ""

        if len(items) == 1:
            return items[0]

        if len(items) == 2:
            return f"{items[0]} and {items[1]}"

        return (
            ", ".join(items[:-1])
            + f", and {items[-1]}"
        )

    @staticmethod
    def _normalise_availability(
        availability: str | None,
    ) -> str | None:
        if not availability:
            return None

        normalised = availability.strip().lower()

        immediate_values = {
            "immediate joiner",
            "immediately available",
            "available immediately",
            "immediate",
        }

        if normalised in immediate_values:
            return "I am available to join immediately."

        return (
            "My current availability is "
            f"{availability.strip()}."
        )

    @classmethod
    def build(
        cls,
        *,
        master_profile: MasterProfile,
        campaign: Campaign,
    ) -> tuple[str, str]:
        """
        Return a deterministic subject and body.
        """

        full_name = master_profile.full_name.strip()

        if not full_name:
            raise DeterministicEmailBuilderError(
                "Master Profile full name is required."
            )

        company_name = campaign.company_name.strip()

        if not company_name:
            raise DeterministicEmailBuilderError(
                "Campaign company name is required."
            )

        recipient_name = (
            campaign.contact_name.strip()
            if campaign.contact_name
            else None
        )

        greeting = (
            f"Hello {recipient_name},"
            if recipient_name
            else "Hello,"
        )

        target_role = (
            campaign.target_role.strip()
            if campaign.target_role
            else "AI and Generative AI"
        )

        skills = cls._split_values(
            master_profile.skills,
            limit=3,
        )

        projects = cls._split_values(
            master_profile.projects,
            limit=2,
        )

        formatted_skills = cls._format_items(skills)
        formatted_projects = cls._format_items(projects)

        if not formatted_skills:
            raise DeterministicEmailBuilderError(
                "At least one approved skill is required."
            )

        if not formatted_projects:
            raise DeterministicEmailBuilderError(
                "At least one approved project is required."
            )

        availability_sentence = cls._normalise_availability(
            master_profile.availability
        )

        portfolio_sentence = ""

        if master_profile.portfolio_url:
            portfolio_sentence = (
                "My portfolio provides additional examples of "
                f"this work: {master_profile.portfolio_url.strip()}."
            )

        availability_block = (
            f" {availability_sentence}"
            if availability_sentence
            else ""
        )

        portfolio_block = (
            f" {portfolio_sentence}"
            if portfolio_sentence
            else ""
        )

        subject = (
            f"Exploring {target_role} opportunities – "
            f"{full_name}"
        )

        body = f"""
{greeting}

I am {full_name}, reaching out to explore relevant {target_role} opportunities at {company_name}. My background includes practical work with {formatted_skills}, supported by projects such as {formatted_projects}. These projects allowed me to work on applied AI workflows, backend services, information retrieval, and automation using technologies already listed in my approved profile.

I am particularly interested in roles where I can continue building reliable AI applications and contribute through hands-on engineering, careful validation, and end-to-end implementation.{availability_block}{portfolio_block}

I would appreciate the opportunity to briefly introduce my work and learn whether there may be a relevant position to discuss. Would you be open to a short conversation at your convenience?

Best regards,
{full_name}
""".strip()

        body = re.sub(
            r"[ \t]+",
            " ",
            body,
        )

        return subject, body