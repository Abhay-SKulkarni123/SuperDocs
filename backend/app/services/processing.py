from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.agents.extraction import run_extraction
from backend.app.models.document import Document
from backend.app.models.run import ProcessingStage, Run, RunStatus


class ProcessingError(Exception):
    pass


def process_run(db: Session, run_id: UUID) -> str:
    run = db.get(Run, run_id)

    if run is None:
        raise ProcessingError("Run not found")

    document = (
        db.query(Document)
        .filter(Document.run_id == run_id)
        .order_by(Document.created_at.asc())
        .first()
    )

    if document is None:
        raise ProcessingError(f"No document found for run {run_id}")

    try:
        started_at = datetime.now(timezone.utc)

        run.status = RunStatus.RUNNING
        run.current_stage = ProcessingStage.EXTRACT
        run.started_at = started_at

        db.commit()

        extracted_text = run_extraction(
            document.storage_reference,
            document.mime_type,
        )

        document.extracted_text = extracted_text

        run.status = RunStatus.COMPLETED
        run.current_stage = ProcessingStage.COMPLETE
        run.completed_at = datetime.now(timezone.utc)

        db.commit()

        db.refresh(document)
        db.refresh(run)

        return extracted_text

    except ProcessingError:
        raise

    except Exception as exc:
        db.rollback()

        run = db.get(Run, run_id)

        if run is not None:
            run.status = RunStatus.FAILED
            run.error_message = str(exc)
            db.commit()

        raise ProcessingError(str(exc)) from exc