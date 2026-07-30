from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import FollowUpStatus


class FollowUpStep(Base):
    __tablename__ = "follow_up_steps"

    __table_args__ = (
        CheckConstraint(
            "step_number >= 1 AND step_number <= 3",
            name="ck_follow_up_step_number",
        ),
        UniqueConstraint(
            "campaign_id",
            "step_number",
            name="uq_campaign_follow_up_step",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey(
            "campaigns.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    step_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    subject: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    due_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    requires_approval: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    status: Mapped[FollowUpStatus] = mapped_column(
        Enum(FollowUpStatus),
        default=FollowUpStatus.PENDING,
        nullable=False,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    cancellation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    campaign = relationship(
        "Campaign",
        back_populates="follow_up_steps",
    )