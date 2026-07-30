from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    APP_NAME: str = "JobReach AI"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'jobreach.db'}"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    GMAIL_ENABLED: bool = False

    # Follow-up schedule (in days)
    FOLLOW_UP_1_DAYS: int = 3
    FOLLOW_UP_2_DAYS: int = 7
    FOLLOW_UP_3_DAYS: int = 12

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
    )


settings = Settings()