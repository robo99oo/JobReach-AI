from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.master_profile import MasterProfile
from app.schemas.master_profile import (
    MasterProfileCreate,
    MasterProfileResponse,
    MasterProfileUpdate,
)

router = APIRouter(
    prefix="/master-profile",
    tags=["Master Profile"],
)


@router.post(
    "",
    response_model=MasterProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_master_profile(
    profile_data: MasterProfileCreate,
    db: Session = Depends(get_db),
):
    existing_profile = db.scalar(select(MasterProfile))

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A master profile already exists.",
        )

    profile = MasterProfile(
        full_name=profile_data.full_name,
        resume_text=profile_data.resume_text,
        skills=profile_data.skills,
        projects=profile_data.projects,
        portfolio_url=(
            str(profile_data.portfolio_url)
            if profile_data.portfolio_url
            else None
        ),
        github_url=(
            str(profile_data.github_url)
            if profile_data.github_url
            else None
        ),
        availability=profile_data.availability,
        preferred_roles=profile_data.preferred_roles,
        is_approved=profile_data.is_approved,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


@router.get(
    "",
    response_model=MasterProfileResponse,
)
def get_master_profile(
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(MasterProfile))

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found.",
        )

    return profile


@router.patch(
    "",
    response_model=MasterProfileResponse,
)
def update_master_profile(
    profile_data: MasterProfileUpdate,
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(MasterProfile))

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found.",
        )

    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field in {"portfolio_url", "github_url"} and value is not None:
            value = str(value)

        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile