from email.utils import parseaddr

from app.services.gmail_service import (
    GmailService,
    GmailServiceError,
)


class BounceDetectionError(Exception):
    """Raised when bounce detection fails."""


class BounceDetectionService:
    """Detect delivery-failure messages inside a Gmail thread."""

    BOUNCE_SENDERS = {
        "mailer-daemon@googlemail.com",
        "mailer-daemon@gmail.com",
        "postmaster@google.com",
    }

    BOUNCE_SUBJECT_KEYWORDS = (
        "delivery status notification",
        "delivery failed",
        "undeliverable",
        "mail delivery subsystem",
        "address not found",
        "message not delivered",
    )

    @staticmethod
    def _extract_header(
        headers: list[dict],
        name: str,
    ) -> str:
        for header in headers:
            if header.get("name", "").lower() == name.lower():
                return header.get("value", "")

        return ""

    @classmethod
    def has_bounce(
        cls,
        *,
        thread_id: str,
    ) -> bool:
        try:
            thread = GmailService.get_thread(thread_id)

        except GmailServiceError as exc:
            raise BounceDetectionError(str(exc)) from exc

        messages = thread.get("messages", [])

        for message in messages[1:]:
            headers = (
                message.get("payload", {})
                .get("headers", [])
            )

            from_header = cls._extract_header(
                headers,
                "From",
            )

            subject_header = cls._extract_header(
                headers,
                "Subject",
            )

            sender_email = parseaddr(from_header)[1].strip().lower()
            normalized_subject = subject_header.strip().lower()

            if sender_email in cls.BOUNCE_SENDERS:
                return True

            if any(
                keyword in normalized_subject
                for keyword in cls.BOUNCE_SUBJECT_KEYWORDS
            ):
                return True

        return False