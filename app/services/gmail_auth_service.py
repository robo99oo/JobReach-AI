from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build


SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CREDENTIALS_PATH = (
    PROJECT_ROOT / "data" / "google" / "credentials.json"
)

TOKEN_PATH = (
    PROJECT_ROOT / "data" / "google" / "token.json"
)


class GmailAuthenticationError(Exception):
    """Raised when Gmail authentication cannot be completed."""


class GmailAuthService:
    """Creates an authenticated Gmail API client."""

    @staticmethod
    def get_credentials() -> Credentials:
        credentials: Credentials | None = None

        if TOKEN_PATH.exists():
            try:
                credentials = Credentials.from_authorized_user_file(
                    str(TOKEN_PATH),
                    SCOPES,
                )
            except ValueError as exc:
                raise GmailAuthenticationError(
                    "The stored Gmail token is invalid."
                ) from exc

        if credentials and credentials.valid:
            return credentials

        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except Exception as exc:
                raise GmailAuthenticationError(
                    "The Gmail access token could not be refreshed."
                ) from exc

        else:
            if not CREDENTIALS_PATH.exists():
                raise GmailAuthenticationError(
                    f"Google OAuth credentials were not found at "
                    f"{CREDENTIALS_PATH}"
                )

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_PATH),
                    SCOPES,
                )

                credentials = flow.run_local_server(
                    port=0,
                    open_browser=True,
                )


            except Exception as exc:

                raise GmailAuthenticationError(

                    f"Google OAuth authorization failed: {type(exc).__name__}: {exc}"

                ) from exc

        TOKEN_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        TOKEN_PATH.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

        return credentials

    @classmethod
    def build_service(cls) -> Resource:
        credentials = cls.get_credentials()

        try:
            return build(
                "gmail",
                "v1",
                credentials=credentials,
                cache_discovery=False,
            )

        except Exception as exc:
            raise GmailAuthenticationError(
                "The Gmail API service could not be created."
            ) from exc