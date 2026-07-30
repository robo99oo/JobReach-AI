from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class MasterProfile(Base):
    __tablename__ = "master_profiles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    resume_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    skills: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    projects: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    portfolio_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    github_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    availability: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    preferred_roles: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )