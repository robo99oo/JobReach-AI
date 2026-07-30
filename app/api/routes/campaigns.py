from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.campaign import Campaign
from app.models.enums import CampaignStatus
from app.models.follow_up_step import FollowUpStep
from app.schemas.campaign import (
    CampaignCreate,
    CampaignGenerationResponse,
    CampaignResponse,
)
from app.schemas.follow_up import FollowUpResponse
from app.services.email_generation_service import (
    EmailGenerationError,
    EmailGenerationService,
)


router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"],
)


@router.post(
    "",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_campaign(
    campaign_data: CampaignCreate,
    db: Session = Depends(get_db),
):
    campaign = Campaign(
        company_name=campaign_data.company_name.strip(),
        contact_name=(
            campaign_data.contact_name.strip()
            if campaign_data.contact_name
            else None
        ),
        contact_title=(
            campaign_data.contact_title.strip()
            if campaign_data.contact_title
            else None
        ),
        recipient_email=str(campaign_data.recipient_email).lower(),
        mode=campaign_data.mode,
        job_description=campaign_data.job_description,
        target_role=campaign_data.target_role,
    )

    db.add(campaign)

    try:
        db.flush()

        now = datetime.utcnow()

        follow_up_delays = [
            settings.FOLLOW_UP_1_DAYS,
            settings.FOLLOW_UP_2_DAYS,
            settings.FOLLOW_UP_3_DAYS,
        ]

        for step_number, delay_days in enumerate(
            follow_up_delays,
            start=1,
        ):
            follow_up = FollowUpStep(
                campaign_id=campaign.id,
                step_number=step_number,
                due_at=now + timedelta(days=delay_days),
                requires_approval=True,
            )

            db.add(follow_up)

        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A campaign already exists for this email address.",
        )

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Campaign and follow-up creation failed: {exc}",
        )

    db.refresh(campaign)
    return campaign


@router.get(
    "",
    response_model=list[CampaignResponse],
)
def list_campaigns(
    db: Session = Depends(get_db),
):
    statement = select(Campaign).order_by(
        Campaign.created_at.desc()
    )

    return list(db.scalars(statement).all())


@router.post(
    "/{campaign_id}/generate",
    response_model=CampaignGenerationResponse,
)
def generate_campaign_email(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    campaign = db.get(Campaign, campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found.",
        )

    if campaign.status not in {
        CampaignStatus.PENDING_GEN,
        CampaignStatus.DEAD_LETTER,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Email generation is only allowed for campaigns in "
                "PENDING_GEN or DEAD_LETTER status."
            ),
        )

    service = EmailGenerationService()

    try:
        return service.generate_for_campaign(
            db=db,
            campaign=campaign,
        )

    except EmailGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/{campaign_id}/follow-ups",
    response_model=list[FollowUpResponse],
)
def list_campaign_follow_ups(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    campaign = db.get(Campaign, campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found.",
        )

    statement = (
        select(FollowUpStep)
        .where(FollowUpStep.campaign_id == campaign_id)
        .order_by(FollowUpStep.step_number)
    )

    return list(db.scalars(statement).all())


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    campaign = db.get(Campaign, campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found.",
        )

    return campaign