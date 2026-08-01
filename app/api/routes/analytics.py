from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.campaign import Campaign
from app.models.enums import (
    CampaignStatus,
    FollowUpStatus,
)
from app.models.follow_up_step import FollowUpStep


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/dashboard")
def get_dashboard_analytics(
    db: Session = Depends(get_db),
) -> dict:
    """
    Return campaign and follow-up analytics for the dashboard.
    """

    total_campaigns = db.scalar(
        select(func.count(Campaign.id))
    ) or 0

    campaign_status_rows = db.execute(
        select(
            Campaign.status,
            func.count(Campaign.id),
        ).group_by(Campaign.status)
    ).all()

    campaign_counts = {
        status_value: count
        for status_value, count in campaign_status_rows
    }

    follow_up_status_rows = db.execute(
        select(
            FollowUpStep.status,
            func.count(FollowUpStep.id),
        ).group_by(FollowUpStep.status)
    ).all()

    follow_up_counts = {
        status_value: count
        for status_value, count in follow_up_status_rows
    }

    sent_count = campaign_counts.get(
        CampaignStatus.SENT,
        0,
    )

    replied_count = campaign_counts.get(
        CampaignStatus.REPLIED,
        0,
    )

    bounced_count = campaign_counts.get(
        CampaignStatus.BOUNCED,
        0,
    )

    delivered_or_processed_count = (
        sent_count
        + replied_count
        + bounced_count
    )

    reply_rate = (
        round(
            replied_count / delivered_or_processed_count * 100,
            2,
        )
        if delivered_or_processed_count
        else 0.0
    )

    bounce_rate = (
        round(
            bounced_count / delivered_or_processed_count * 100,
            2,
        )
        if delivered_or_processed_count
        else 0.0
    )

    return {
        "total_campaigns": total_campaigns,
        "campaigns": {
            "pending_generation": campaign_counts.get(
                CampaignStatus.PENDING_GEN,
                0,
            ),
            "generated": campaign_counts.get(
                CampaignStatus.GENERATED,
                0,
            ),
            "draft_ready": campaign_counts.get(
                CampaignStatus.DRAFT_READY,
                0,
            ),
            "approved": campaign_counts.get(
                CampaignStatus.APPROVED,
                0,
            ),
            "sent": sent_count,
            "replied": replied_count,
            "rejected": campaign_counts.get(
                CampaignStatus.REJECTED,
                0,
            ),
            "bounced": bounced_count,
            "stopped": campaign_counts.get(
                CampaignStatus.STOPPED,
                0,
            ),
            "dead_letter": campaign_counts.get(
                CampaignStatus.DEAD_LETTER,
                0,
            ),
        },
        "follow_ups": {
            "pending": follow_up_counts.get(
                FollowUpStatus.PENDING,
                0,
            ),
            "draft_ready": follow_up_counts.get(
                FollowUpStatus.DRAFT_READY,
                0,
            ),
            "approved": follow_up_counts.get(
                FollowUpStatus.APPROVED,
                0,
            ),
            "sent": follow_up_counts.get(
                FollowUpStatus.SENT,
                0,
            ),
            "cancelled": follow_up_counts.get(
                FollowUpStatus.CANCELLED,
                0,
            ),
        },
        "rates": {
            "reply_rate_percentage": reply_rate,
            "bounce_rate_percentage": bounce_rate,
        },
    }