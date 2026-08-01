from apscheduler.schedulers.background import BackgroundScheduler

from app.db.database import SessionLocal
from app.workers.follow_up_scheduler import FollowUpScheduler


scheduler = BackgroundScheduler()


def run_due_follow_up_job() -> None:
    """
    Run one scheduler cycle using a fresh database session.
    """

    db = SessionLocal()

    print()
    print("=" * 60)
    print("JOBREACH AI - FOLLOW-UP SCHEDULER")
    print("=" * 60)

    try:
        worker = FollowUpScheduler()
        result = worker.process_due_follow_ups(db)

        print(f"Checked At        : {result['checked_at']}")
        print(f"Due Follow-ups    : {result['due_count']}")
        print(f"Generated Drafts  : {result['generated_count']}")
        print(f"Failed            : {result['failed_count']}")

        if result["generated_follow_up_ids"]:
            print(
                "Generated IDs     : "
                f"{result['generated_follow_up_ids']}"
            )

        if result["failures"]:
            print("Failures:")

            for failure in result["failures"]:
                print(
                    f"- Follow-up {failure['follow_up_id']}: "
                    f"{failure['error']}"
                )

        print("=" * 60)

    except Exception as exc:
        db.rollback()

        print(
            "Scheduler crashed  : "
            f"{exc}"
        )
        print("=" * 60)

    finally:
        db.close()


def start_background_scheduler() -> None:
    """
    Start the scheduler if it is not already running.
    """

    if scheduler.running:
        return

    scheduler.add_job(
        run_due_follow_up_job,
        trigger="interval",
        minutes=15,
        id="due-follow-up-generation",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()

    print()
    print("Background follow-up scheduler started.")
    print("Scheduler interval: every 15 minutes.")

def stop_background_scheduler() -> None:
    """
    Stop the scheduler during application shutdown.
    """

    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("Background follow-up scheduler stopped.")