from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.campaign import Campaign
from app.models.enums import (
    CampaignStatus,
    FollowUpStatus,
)
from app.models.follow_up_step import FollowUpStep
from app.schemas.campaign import (
    CampaignCreate,
    CampaignGenerationResponse,
    CampaignResponse,
)
from app.schemas.follow_up import FollowUpResponse
from app.services.bounce_detection_service import (
    BounceDetectionError,
    BounceDetectionService,
)
from app.services.email_generation_service import (
    EmailGenerationError,
    EmailGenerationService,
)
from app.services.gmail_service import (
    GmailService,
    GmailServiceError,
)
from app.services.reply_detection_service import (
    ReplyDetectionError,
    ReplyDetectionService,
)
from app.workers.campaign_worker import (
    CampaignWorker,
    CampaignWorkerError,
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
) -> Campaign:
    """
    Create a campaign and its three scheduled follow-up steps.
    """

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
        recipient_email=str(
            campaign_data.recipient_email
        ).strip().lower(),
        mode=campaign_data.mode,
        job_description=(
            campaign_data.job_description.strip()
            if campaign_data.job_description
            else None
        ),
        target_role=(
            campaign_data.target_role.strip()
            if campaign_data.target_role
            else None
        ),
        status=CampaignStatus.PENDING_GEN,
    )

    db.add(campaign)

    try:
        # Assign the campaign ID without committing yet.
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

        # Store the campaign and all follow-ups atomically.
        db.commit()
        db.refresh(campaign)

        return campaign

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A campaign already exists for this recipient "
                "email address."
            ),
        ) from exc

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Campaign and follow-up creation failed: "
                f"{exc}"
            ),
        ) from exc


@router.get(
    "",
    response_model=list[CampaignResponse],
)
def list_campaigns(
    db: Session = Depends(get_db),
) -> list[Campaign]:
    """
    Return all campaigns, newest first.
    """

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
) -> Campaign:
    """
    Generate and validate email content without creating a Gmail draft.

    Successful transition:
    PENDING_GEN or DEAD_LETTER -> GENERATED
    """

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
                "Email generation is only allowed for campaigns "
                "in PENDING_GEN or DEAD_LETTER status."
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
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{campaign_id}/process",
    response_model=CampaignResponse,
)
def process_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
) -> Campaign:
    """
    Run the complete generation and Gmail-draft workflow.

    Workflow:
    PENDING_GEN
        -> generate email
        -> validate email
        -> create Gmail draft
        -> save Gmail identifiers
        -> DRAFT_READY
    """

    campaign = db.get(Campaign, campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found.",
        )

    if campaign.status != CampaignStatus.PENDING_GEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Complete campaign processing is only allowed "
                "when the campaign status is PENDING_GEN."
            ),
        )

    worker = CampaignWorker()

    try:
        return worker.process_campaign(
            db=db,
            campaign=campaign,
        )

    except CampaignWorkerError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{campaign_id}/approve",
    response_model=CampaignResponse,
)
def approve_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
) -> Campaign:
    """
    Approve a Gmail draft after human review.

    Successful transition:
    DRAFT_READY -> APPROVED

    This endpoint does not send the email.
    """

    campaign = db.get(Campaign, campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found.",
        )

    if campaign.status != CampaignStatus.DRAFT_READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Only campaigns in DRAFT_READY status "
                "can be approved."
            ),
        )

    if not campaign.gmail_draft_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The campaign does not have a Gmail draft ID.",
        )

    if not campaign.gmail_message_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The campaign does not have a Gmail message ID.",
        )

    campaign.status = CampaignStatus.APPROVED
    campaign.stop_reason = None

    try:
        db.commit()
        db.refresh(campaign)

        return campaign

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Campaign approval failed: {exc}",
        ) from exc


@router.post(
    "/{campaign_id}/send",
    response_model=CampaignResponse,
)
def send_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
) -> Campaign:
    """
    Send an approved Gmail draft.

    Successful transition:
    APPROVED -> SENT
    """

    campaign = db.get(Campaign, campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found.",
        )

    if campaign.status != CampaignStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Only campaigns in APPROVED status "
                "can be sent."
            ),
        )

    if not campaign.gmail_draft_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The campaign does not have a Gmail draft ID.",
        )

    try:
        sent_message = GmailService.send_draft(
            draft_id=campaign.gmail_draft_id,
        )

        returned_message_id = sent_message.get("id")
        returned_thread_id = sent_message.get("threadId")

        if returned_message_id:
            campaign.gmail_message_id = returned_message_id

        if returned_thread_id:
            campaign.gmail_thread_id = returned_thread_id

        campaign.status = CampaignStatus.SENT
        campaign.sent_at = datetime.utcnow()
        campaign.stop_reason = None

        db.commit()
        db.refresh(campaign)

        return campaign

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
            detail=f"Campaign sending failed: {exc}",
        ) from exc


@router.post(
    "/{campaign_id}/check-reply",
    response_model=CampaignResponse,
)
def check_campaign_reply(
    campaign_id: int,
    db: Session = Depends(get_db),
) -> Campaign:
    """
    Check whether the recipient replied to a sent campaign.

    Successful transition:
    SENT -> REPLIED

    When a reply is found, unsent follow-ups are cancelled.
    """

    campaign = db.get(Campaign, campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found.",
        )

    if campaign.status not in {
        CampaignStatus.SENT,
        CampaignStatus.REPLIED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Reply detection is only allowed for campaigns "
                "in SENT or REPLIED status."
            ),
        )

    if not campaign.gmail_thread_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The campaign does not have a Gmail thread ID.",
        )

    # Idempotent: an already-replied campaign needs no new Gmail check.
    if campaign.status == CampaignStatus.REPLIED:
        return campaign

    try:
        has_reply = ReplyDetectionService.has_reply(
            thread_id=campaign.gmail_thread_id,
            sender_email="kshiti392000@gmail.com",
        )

        if not has_reply:
            return campaign

        now = datetime.utcnow()

        campaign.status = CampaignStatus.REPLIED
        campaign.replied_at = now
        campaign.stop_reason = "Recipient replied."

        statement = select(FollowUpStep).where(
            FollowUpStep.campaign_id == campaign.id,
            FollowUpStep.status.in_(
                [
                    FollowUpStatus.PENDING,
                    FollowUpStatus.DRAFT_READY,
                    FollowUpStatus.APPROVED,
                ]
            ),
        )

        follow_ups = list(db.scalars(statement).all())

        for follow_up in follow_ups:
            follow_up.status = FollowUpStatus.CANCELLED
            follow_up.cancelled_at = now
            follow_up.cancellation_reason = (
                "Cancelled because the recipient replied."
            )

        db.commit()
        db.refresh(campaign)

        return campaign

    except ReplyDetectionError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reply detection failed: {exc}",
        ) from exc


@router.post(
    "/{campaign_id}/check-bounce",
    response_model=CampaignResponse,
)
def check_campaign_bounce(
    campaign_id: int,
    db: Session = Depends(get_db),
) -> Campaign:
    """
    Check whether Gmail received a delivery-failure notification.

    Successful transition:
    SENT -> BOUNCED

    When a bounce is detected, unsent follow-ups are cancelled.
    """

    campaign = db.get(Campaign, campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found.",
        )

    if campaign.status not in {
        CampaignStatus.SENT,
        CampaignStatus.BOUNCED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Bounce detection is only allowed for campaigns "
                "in SENT or BOUNCED status."
            ),
        )

    if not campaign.gmail_thread_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The campaign does not have a Gmail thread ID.",
        )

    # Idempotent: an already-bounced campaign needs no new Gmail check.
    if campaign.status == CampaignStatus.BOUNCED:
        return campaign

    try:
        has_bounce = BounceDetectionService.has_bounce(
            thread_id=campaign.gmail_thread_id,
        )

        if not has_bounce:
            return campaign

        now = datetime.utcnow()

        campaign.status = CampaignStatus.BOUNCED
        campaign.stop_reason = "Email delivery failed."

        statement = select(FollowUpStep).where(
            FollowUpStep.campaign_id == campaign.id,
            FollowUpStep.status.in_(
                [
                    FollowUpStatus.PENDING,
                    FollowUpStatus.DRAFT_READY,
                    FollowUpStatus.APPROVED,
                ]
            ),
        )

        follow_ups = list(db.scalars(statement).all())

        for follow_up in follow_ups:
            follow_up.status = FollowUpStatus.CANCELLED
            follow_up.cancelled_at = now
            follow_up.cancellation_reason = (
                "Cancelled because the original email bounced."
            )

        db.commit()
        db.refresh(campaign)

        return campaign

    except BounceDetectionError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bounce detection failed: {exc}",
        ) from exc


@router.get(
    "/{campaign_id}/follow-ups",
    response_model=list[FollowUpResponse],
)
def list_campaign_follow_ups(
    campaign_id: int,
    db: Session = Depends(get_db),
) -> list[FollowUpStep]:
    """
    Return the three follow-up steps belonging to a campaign.
    """

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
) -> Campaign:
    """
    Return one campaign by its database ID.
    """

    campaign = db.get(Campaign, campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found.",
        )

    return campaign