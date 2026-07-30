from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import CampaignMode, CampaignStatus


class Campaign(Base):
    __tablename__ = "campaigns"

    __table_args__ = (
        UniqueConstraint(
            "recipient_email",
            name="uq_campaign_recipient_email",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    company_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    contact_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    contact_title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    recipient_email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        index=True,
    )

    mode: Mapped[CampaignMode] = mapped_column(
        Enum(CampaignMode),
        nullable=False,
    )

    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus),
        nullable=False,
        default=CampaignStatus.PENDING_GEN,
    )

    job_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    target_role: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    email_subject: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    email_body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    gmail_thread_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    gmail_message_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    stop_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    replied_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    follow_up_steps = relationship(
        "FollowUpStep",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )

    telemetry_events = relationship(
        "TelemetryEvent",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )