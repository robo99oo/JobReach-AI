from app.services.gmail_auth_service import (
    GmailAuthenticationError,
    GmailAuthService,
)


def main() -> None:
    try:
        GmailAuthService.build_service()
        print("JobReach AI successfully connected to Gmail.")
    except GmailAuthenticationError as exc:
        print(f"Gmail authentication failed: {exc}")


if __name__ == "__main__":
    main()