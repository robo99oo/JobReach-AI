from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator

from app.models.enums import CampaignMode, CampaignStatus


class CampaignCreate(BaseModel):
    company_name: str
    contact_name: str | None = None
    contact_title: str | None = None
    recipient_email: EmailStr
    mode: CampaignMode
    job_description: str | None = None
    target_role: str | None = None

    @model_validator(mode="after")
    def validate_mode_requirements(self):
        if self.mode == CampaignMode.WITH_JD and not self.job_description:
            raise ValueError(
                "job_description is required when mode is WITH_JD"
            )
        return self


class CampaignResponse(BaseModel):
    id: int
    company_name: str
    contact_name: str | None
    contact_title: str | None
    recipient_email: str
    mode: CampaignMode
    status: CampaignStatus
    job_description: str | None
    target_role: str | None
    email_subject: str | None
    email_body: str | None
    gmail_thread_id: str | None
    stop_reason: str | None
    created_at: datetime
    updated_at: datetime
    sent_at: datetime | None
    replied_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class CampaignGenerationResponse(BaseModel):
    id: int
    status: CampaignStatus
    email_subject: str | None
    email_body: str | None
    stop_reason: str | None

    model_config = ConfigDict(from_attributes=True)