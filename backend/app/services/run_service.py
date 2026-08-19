import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models.run import ProcessingStage, Run, RunStatus


def create_run(db: Session) -> Run:
    now = datetime.now(timezone.utc)

    run = Run(
        status=RunStatus.PENDING,
        current_stage=ProcessingStage.INGEST,
        created_at=now,
        updated_at=now,
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    return run


def get_run(db: Session, run_id: uuid.UUID) -> Run | None:
    statement = select(Run).where(Run.id == run_id)
    return db.scalar(statement)