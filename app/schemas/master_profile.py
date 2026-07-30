from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class MasterProfileCreate(BaseModel):
    full_name: str
    resume_text: str
    skills: str = ""
    projects: str = ""
    portfolio_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    availability: str | None = None
    preferred_roles: str = ""
    is_approved: bool = False


class MasterProfileUpdate(BaseModel):
    full_name: str | None = None
    resume_text: str | None = None
    skills: str | None = None
    projects: str | None = None
    portfolio_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    availability: str | None = None
    preferred_roles: str | None = None
    is_approved: bool | None = None


class MasterProfileResponse(BaseModel):
    id: int
    full_name: str
    resume_text: str
    skills: str
    projects: str
    portfolio_url: str | None
    github_url: str | None
    availability: str | None
    preferred_roles: str
    is_approved: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)