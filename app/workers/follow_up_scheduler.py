from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.campaign import Campaign
from app.models.enums import (
    CampaignStatus,
    FollowUpStatus,
)
from app.models.follow_up_step import FollowUpStep
from app.services.follow_up_generation_service import (
    FollowUpGenerationError,
    FollowUpGenerationService,
)


class FollowUpScheduler:
    """
    Finds due follow-ups and generates drafts for human approval.

    It does not send emails automatically.
    """

    def __init__(self) -> None:
        self.generation_service = FollowUpGenerationService()

    def process_due_follow_ups(
        self,
        db: Session,
    ) -> dict:
        now = datetime.utcnow()

        statement = (
            select(FollowUpStep)
            .options(joinedload(FollowUpStep.campaign))
            .join(Campaign)
            .where(
                FollowUpStep.status == FollowUpStatus.PENDING,
                FollowUpStep.due_at <= now,
                Campaign.status == CampaignStatus.SENT,
            )
            .order_by(FollowUpStep.due_at.asc())
        )

        due_follow_ups = list(
            db.scalars(statement).all()
        )

        generated_ids: list[int] = []
        failed_items: list[dict] = []

        for follow_up in due_follow_ups:
            try:
                self.generation_service.generate(
                    db=db,
                    campaign=follow_up.campaign,
                    follow_up=follow_up,
                )

                generated_ids.append(follow_up.id)

            except FollowUpGenerationError as exc:
                failed_items.append(
                    {
                        "follow_up_id": follow_up.id,
                        "error": str(exc),
                    }
                )

            except Exception as exc:
                db.rollback()

                failed_items.append(
                    {
                        "follow_up_id": follow_up.id,
                        "error": (
                            "Unexpected scheduler failure: "
                            f"{exc}"
                        ),
                    }
                )

        return {
            "checked_at": now.isoformat(),
            "due_count": len(due_follow_ups),
            "generated_count": len(generated_ids),
            "generated_follow_up_ids": generated_ids,
            "failed_count": len(failed_items),
            "failures": failed_items,
        }