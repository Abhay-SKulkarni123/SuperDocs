from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.agents.extraction import run_extraction
from backend.app.models.document import Document
from backend.app.models.run import ProcessingStage, Run, RunStatus
from backend.app.services.extraction import DocumentExtractionError


class ProcessingError(Exception):
    pass


def process_run(db: Session, run_id: UUID) -> str:
    run = db.get(Run, run_id)

    if run is None:
        raise ProcessingError("Run not found")

    document = db.scalar(
        select(Document)
        .where(Document.run_id == run_id)
        .order_by(Document.created_at.asc())
    )

    if document is None:
        raise ProcessingError("No document found for run")

    now = datetime.now(timezone.utc)

    run.status = RunStatus.RUNNING
    run.current_stage = ProcessingStage.EXTRACT
    run.started_at = run.started_at or now
    run.updated_at = now

    try:
        text = run_extraction(
            file_path=document.storage_reference,
            mime_type=document.mime_type,
        )
    except DocumentExtractionError as exc:
        run.status = RunStatus.FAILED
        run.error_message = str(exc)
        run.updated_at = datetime.now(timezone.utc)

        db.commit()

        raise ProcessingError(str(exc)) from exc

    run.status = RunStatus.COMPLETED
    run.current_stage = ProcessingStage.COMPLETE
    run.error_message = None
    run.completed_at = datetime.now(timezone.utc)
    run.updated_at = datetime.now(timezone.utc)

    db.commit()

    return text