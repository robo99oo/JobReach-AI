from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.enums import (
    CampaignStatus,
    FollowUpStatus,
)
from app.models.follow_up_step import FollowUpStep
from app.schemas.follow_up import FollowUpResponse
from app.services.follow_up_generation_service import (
    FollowUpGenerationError,
    FollowUpGenerationService,
)
from app.services.gmail_service import (
    GmailService,
    GmailServiceError,
)


router = APIRouter(
    prefix="/follow-ups",
    tags=["Follow Ups"],
)


@router.post(
    "/{follow_up_id}/generate",
    response_model=FollowUpResponse,
)
def generate_follow_up(
    follow_up_id: int,
    db: Session = Depends(get_db),
) -> FollowUpStep:
    """
    Generate a pending follow-up draft.

    Successful transition:
    PENDING -> DRAFT_READY
    """

    follow_up = db.get(FollowUpStep, follow_up_id)

    if not follow_up:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow-up not found.",
        )

    service = FollowUpGenerationService()

    try:
        return service.generate(
            db=db,
            campaign=follow_up.campaign,
            follow_up=follow_up,
        )

    except FollowUpGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{follow_up_id}/approve",
    response_model=FollowUpResponse,
)
def approve_follow_up(
    follow_up_id: int,
    db: Session = Depends(get_db),
) -> FollowUpStep:
    """
    Approve a generated follow-up after human review.

    Successful transition:
    DRAFT_READY -> APPROVED
    """

    follow_up = db.get(FollowUpStep, follow_up_id)

    if not follow_up:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow-up not found.",
        )

    if follow_up.status != FollowUpStatus.DRAFT_READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Only follow-ups in DRAFT_READY status "
                "can be approved."
            ),
        )

    if not follow_up.subject:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The follow-up subject is missing.",
        )

    if not follow_up.body:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The follow-up body is missing.",
        )

    follow_up.status = FollowUpStatus.APPROVED
    follow_up.cancellation_reason = None

    try:
        db.commit()
        db.refresh(follow_up)

        return follow_up

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Follow-up approval failed: {exc}",
        ) from exc


@router.post(
    "/{follow_up_id}/send",
    response_model=FollowUpResponse,
)
def send_follow_up(
    follow_up_id: int,
    db: Session = Depends(get_db),
) -> FollowUpStep:
    """
    Send an approved follow-up in the original Gmail thread.

    Successful transition:
    APPROVED -> SENT
    """

    follow_up = db.get(FollowUpStep, follow_up_id)

    if not follow_up:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow-up not found.",
        )

    campaign = follow_up.campaign

    if campaign.status != CampaignStatus.SENT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Follow-ups can only be sent while the campaign "
                "status is SENT."
            ),
        )

    if follow_up.status != FollowUpStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Only follow-ups in APPROVED status can be sent."
            ),
        )

    if not campaign.gmail_thread_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The campaign does not have a Gmail thread ID.",
        )

    if not follow_up.subject:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The approved follow-up subject is missing.",
        )

    if not follow_up.body:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The approved follow-up body is missing.",
        )

    try:
        GmailService.send_thread_message(
            recipient_email=campaign.recipient_email,
            subject=follow_up.subject,
            body=follow_up.body,
            thread_id=campaign.gmail_thread_id,
        )

        follow_up.status = FollowUpStatus.SENT
        follow_up.sent_at = datetime.utcnow()
        follow_up.cancellation_reason = None

        db.commit()
        db.refresh(follow_up)

        return follow_up

    except GmailServiceError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Follow-up sending failed: {exc}",
        ) from exc