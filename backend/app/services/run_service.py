import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.models.run import ProcessingStage, Run, RunStatus


def create_run(db: Session) -> Run:
    run = Run(
        status=RunStatus.PENDING,
        current_stage=ProcessingStage.INGEST,
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    return run


def get_run(db: Session, run_id: uuid.UUID) -> Run | None:
    return db.get(Run, run_id)


def mark_run_started(db: Session, run: Run) -> Run:
    run.status = RunStatus.RUNNING
    run.started_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(run)

    return run


def mark_run_failed(
    db: Session,
    run: Run,
    error_message: str,
) -> Run:
    run.status = RunStatus.FAILED
    run.error_message = error_message

    db.commit()
    db.refresh(run)

    return run


def mark_stage_complete(
    db: Session,
    run: Run,
    next_stage: ProcessingStage,
) -> Run:
    run.current_stage = next_stage

    db.commit()
    db.refresh(run)

    return run