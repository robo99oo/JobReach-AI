from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def build_engine():
    engine_options: dict = {
        "pool_pre_ping": True,
    }

    if settings.DATABASE_URL.startswith("sqlite"):
        engine_options["connect_args"] = {
            "check_same_thread": False,
        }

    return create_engine(
        settings.DATABASE_URL,
        **engine_options,
    )


engine = build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()