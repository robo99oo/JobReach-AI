from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.workers.follow_up_scheduler import FollowUpScheduler


router = APIRouter(
    prefix="/scheduler",
    tags=["Scheduler"],
)


@router.post("/run-due-follow-ups")
def run_due_follow_ups(
    db: Session = Depends(get_db),
) -> dict:
    """
    Find due pending follow-ups and generate drafts for review.
    """

    scheduler = FollowUpScheduler()

    return scheduler.process_due_follow_ups(db)