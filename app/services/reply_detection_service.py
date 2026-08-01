from email.utils import parseaddr

from app.services.gmail_service import (
    GmailService,
    GmailServiceError,
)


class ReplyDetectionError(Exception):
    """Raised when reply detection fails."""


class ReplyDetectionService:
    """Detect whether a recipient replied in a Gmail thread."""

    @staticmethod
    def _extract_header(
        headers: list[dict],
        name: str,
    ) -> str:
        for header in headers:
            if header.get("name", "").lower() == name.lower():
                return header.get("value", "")

        return ""

    @staticmethod
    def has_reply(
        *,
        thread_id: str,
        sender_email: str,
    ) -> bool:
        try:
            thread = GmailService.get_thread(thread_id)

        except GmailServiceError as exc:
            raise ReplyDetectionError(str(exc)) from exc

        messages = thread.get("messages", [])

        if len(messages) <= 1:
            return False

        normalized_sender = sender_email.strip().lower()

        for message in messages[1:]:
            headers = (
                message.get("payload", {})
                .get("headers", [])
            )

            from_header = ReplyDetectionService._extract_header(
                headers,
                "From",
            )

            message_sender = parseaddr(from_header)[1].strip().lower()

            if message_sender and message_sender != normalized_sender:
                return True

        return False