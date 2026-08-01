from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    APP_NAME: str = "JobReach AI"
    APP_VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str = (
        f"sqlite:///{BASE_DIR / 'jobreach.db'}"
    )

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    # Gmail
    GMAIL_ENABLED: bool = False

    # Follow-up schedule
    FOLLOW_UP_1_DAYS: int = 3
    FOLLOW_UP_2_DAYS: int = 7
    FOLLOW_UP_3_DAYS: int = 12

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()