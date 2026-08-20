from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.document import Document
from backend.app.models.run import (
    ProcessingStage,
    ReviewStatus,
    Run,
    RunStatus,
)
from backend.app.services.extraction import extract_text
from backend.app.agents.workflow import document_workflow


class OrchestrationError(Exception):
    pass


def _get_run(db: Session, run_id: UUID) -> Run:
    run = db.get(Run, run_id)

    if run is None:
        raise OrchestrationError(f"Run {run_id} was not found")

    return run


def _get_documents(
    db: Session,
    run_id: UUID,
) -> list[Document]:
    documents = (
        db.query(Document)
        .filter(Document.run_id == run_id)
        .order_by(Document.created_at.asc())
        .all()
    )

    if not documents:
        raise OrchestrationError(
            f"No documents found for run {run_id}"
        )

    return documents


def process_run(db: Session, run_id: UUID) -> Run:
    run = _get_run(db, run_id)

    if run.status not in {
        RunStatus.PENDING,
        RunStatus.FAILED,
    }:
        raise OrchestrationError(
            f"Run {run_id} cannot be processed from status "
            f"{run.status.value}"
        )

    documents = _get_documents(db, run_id)

    try:
        now = datetime.now(timezone.utc)

        run.status = RunStatus.RUNNING
        run.current_stage = ProcessingStage.EXTRACT
        run.started_at = now
        run.updated_at = now
        run.error_message = None

        db.commit()

        # ---------------------------------------------------------
        # Extraction stage
        # ---------------------------------------------------------
        for document in documents:
            extracted_text = extract_text(
                document.storage_reference,
                document.mime_type,
            )

            if not extracted_text.strip():
                raise OrchestrationError(
                    f"Document {document.id} extraction produced no text"
                )

            document.extracted_text = extracted_text

        run.current_stage = ProcessingStage.ANALYZE
        run.updated_at = datetime.now(timezone.utc)

        db.commit()

        # ---------------------------------------------------------
        # Analysis stage
        # ---------------------------------------------------------
        for document in documents:
            analysis_result = document_workflow.invoke(
                {
                    "run_id": str(run.id),
                    "document_id": str(document.id),
                    "text": document.extracted_text,
                    "status": "extracted",
                }
            )

            document.summary = analysis_result["summary"]
            document.word_count = analysis_result["word_count"]
            document.character_count = analysis_result["character_count"]
            document.sentence_count = analysis_result["sentence_count"]

        # ---------------------------------------------------------
        # Human review boundary
        # ---------------------------------------------------------
        run.status = RunStatus.PAUSED
        run.current_stage = ProcessingStage.REVIEW
        run.review_status = ReviewStatus.PENDING
        run.updated_at = datetime.now(timezone.utc)
        run.completed_at = None

        db.commit()

        db.refresh(run)

        return run

    except OrchestrationError:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        run = db.get(Run, run_id)

        if run is not None:
            run.status = RunStatus.FAILED
            run.error_message = str(exc)
            run.updated_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(run)

        raise OrchestrationError(str(exc)) from exc

def approve_run(db: Session, run_id: UUID) -> Run:
    run = _get_run(db, run_id)

    if (
        run.status != RunStatus.PAUSED
        or run.current_stage != ProcessingStage.REVIEW
    ):
        raise OrchestrationError(
            f"Run {run_id} is not awaiting review"
        )

    run.status = RunStatus.COMPLETED
    run.current_stage = ProcessingStage.COMPLETE
    run.review_status = ReviewStatus.APPROVED
    run.completed_at = datetime.now(timezone.utc)
    run.updated_at = datetime.now(timezone.utc)
    run.error_message = None

    db.commit()
    db.refresh(run)

    return run


def reject_run(db: Session, run_id: UUID) -> Run:
    run = _get_run(db, run_id)

    if (
        run.status != RunStatus.PAUSED
        or run.current_stage != ProcessingStage.REVIEW
    ):
        raise OrchestrationError(
            f"Run {run_id} is not awaiting review"
        )

    run.status = RunStatus.FAILED
    run.review_status = ReviewStatus.REJECTED
    run.current_stage = ProcessingStage.REVIEW
    run.completed_at = None
    run.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(run)

    return run