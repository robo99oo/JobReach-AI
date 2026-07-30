from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import TelemetryType


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

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

    event_type: Mapped[TelemetryType] = mapped_column(
        Enum(TelemetryType),
        nullable=False,
    )

    tracking_token: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    target_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    campaign = relationship(
        "Campaign",
        back_populates="telemetry_events",
    )