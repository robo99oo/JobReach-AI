import base64
from email.message import EmailMessage

from googleapiclient.errors import HttpError

from app.services.gmail_auth_service import GmailAuthService


class GmailServiceError(Exception):
    """Raised when a Gmail operation fails."""


class GmailService:
    """Handles Gmail draft, send, thread, and follow-up operations."""

    @staticmethod
    def create_draft(
        recipient_email: str,
        subject: str,
        body: str,
    ) -> dict:
        """
        Create a Gmail draft using the authenticated Gmail account.
        """

        if not recipient_email.strip():
            raise GmailServiceError(
                "Recipient email is required."
            )

        if not subject.strip():
            raise GmailServiceError(
                "Email subject is required."
            )

        if not body.strip():
            raise GmailServiceError(
                "Email body is required."
            )

        message = EmailMessage()
        message["To"] = recipient_email.strip()
        message["Subject"] = subject.strip()
        message.set_content(body.strip())

        encoded_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode("utf-8")

        draft_body = {
            "message": {
                "raw": encoded_message,
            }
        }

        try:
            service = GmailAuthService.build_service()

            draft = (
                service.users()
                .drafts()
                .create(
                    userId="me",
                    body=draft_body,
                )
                .execute()
            )

            return draft

        except HttpError as exc:
            raise GmailServiceError(
                f"Gmail API failed to create the draft: {exc}"
            ) from exc

        except Exception as exc:
            raise GmailServiceError(
                f"Unexpected Gmail draft creation failure: {exc}"
            ) from exc

    @staticmethod
    def send_draft(
        draft_id: str,
    ) -> dict:
        """
        Send an existing Gmail draft by its draft ID.
        """

        if not draft_id.strip():
            raise GmailServiceError(
                "Gmail draft ID is required."
            )

        try:
            service = GmailAuthService.build_service()

            sent_message = (
                service.users()
                .drafts()
                .send(
                    userId="me",
                    body={
                        "id": draft_id.strip(),
                    },
                )
                .execute()
            )

            return sent_message

        except HttpError as exc:
            raise GmailServiceError(
                f"Gmail API failed to send the draft: {exc}"
            ) from exc

        except Exception as exc:
            raise GmailServiceError(
                f"Unexpected Gmail send failure: {exc}"
            ) from exc

    @staticmethod
    def get_thread(
        thread_id: str,
    ) -> dict:
        """
        Retrieve a Gmail conversation thread with all messages.
        """

        if not thread_id.strip():
            raise GmailServiceError(
                "Gmail thread ID is required."
            )

        try:
            service = GmailAuthService.build_service()

            thread = (
                service.users()
                .threads()
                .get(
                    userId="me",
                    id=thread_id.strip(),
                    format="full",
                )
                .execute()
            )

            return thread

        except HttpError as exc:
            raise GmailServiceError(
                f"Gmail API failed to retrieve the thread: {exc}"
            ) from exc

        except Exception as exc:
            raise GmailServiceError(
                f"Unexpected Gmail thread retrieval failure: {exc}"
            ) from exc

    @staticmethod
    def send_thread_message(
        recipient_email: str,
        subject: str,
        body: str,
        thread_id: str,
    ) -> dict:
        """
        Send a follow-up message inside an existing Gmail thread.
        """

        if not recipient_email.strip():
            raise GmailServiceError(
                "Recipient email is required."
            )

        if not subject.strip():
            raise GmailServiceError(
                "Email subject is required."
            )

        if not body.strip():
            raise GmailServiceError(
                "Email body is required."
            )

        if not thread_id.strip():
            raise GmailServiceError(
                "Gmail thread ID is required."
            )

        normalized_subject = subject.strip()

        if not normalized_subject.lower().startswith("re:"):
            normalized_subject = f"Re: {normalized_subject}"

        message = EmailMessage()
        message["To"] = recipient_email.strip()
        message["Subject"] = normalized_subject
        message.set_content(body.strip())

        encoded_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode("utf-8")

        request_body = {
            "raw": encoded_message,
            "threadId": thread_id.strip(),
        }

        try:
            service = GmailAuthService.build_service()

            sent_message = (
                service.users()
                .messages()
                .send(
                    userId="me",
                    body=request_body,
                )
                .execute()
            )

            return sent_message

        except HttpError as exc:
            raise GmailServiceError(
                f"Gmail API failed to send the follow-up: {exc}"
            ) from exc

        except Exception as exc:
            raise GmailServiceError(
                f"Unexpected Gmail follow-up send failure: {exc}"
            ) from exc