from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import FollowUpStatus


class FollowUpResponse(BaseModel):
    id: int
    campaign_id: int
    step_number: int
    subject: str | None
    body: str |None
    due_at: datetime
    requires_approval: bool
    status: FollowUpStatus
    sent_at: datetime | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)