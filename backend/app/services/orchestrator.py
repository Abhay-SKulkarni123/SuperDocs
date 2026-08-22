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

import json


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

    if run.current_stage in {
        ProcessingStage.REVIEW,
        ProcessingStage.COMMIT,
        ProcessingStage.COMPLETE,
    }:
        raise OrchestrationError(
            f"Run {run_id} has already reached "
            f"{run.current_stage.value}"
        )

    # Atomically claim the run.
    #
    # Only one concurrent worker can change PENDING/FAILED -> RUNNING.
    # The UPDATE includes the current status in its WHERE clause, so
    # another worker that already claimed the run updates zero rows.
    claim_query = (
        db.query(Run)
        .filter(
            Run.id == run_id,
            Run.status.in_(
                [
                    RunStatus.PENDING,
                    RunStatus.FAILED,
                ]
            ),
        )
        .update(
            {
                Run.status: RunStatus.RUNNING,
                Run.started_at: run.started_at
                or datetime.now(timezone.utc),
                Run.updated_at: datetime.now(timezone.utc),
                Run.error_message: None,
            },
            synchronize_session=False,
        )
    )

    if claim_query != 1:
        db.rollback()

        current_run = db.get(Run, run_id)

        if current_run is None:
            raise OrchestrationError(
                f"Run {run_id} was not found"
            )

        raise OrchestrationError(
            f"Run {run_id} cannot be processed from status "
            f"{current_run.status.value}"
        )

    db.commit()

    run = db.get(Run, run_id)

    if run is None:
        raise OrchestrationError(
            f"Run {run_id} was not found"
        )

    if run.current_stage in {
        ProcessingStage.REVIEW,
        ProcessingStage.COMMIT,
        ProcessingStage.COMPLETE,
    }:
        raise OrchestrationError(
            f"Run {run_id} has already reached "
            f"{run.current_stage.value}"
        )

    documents = _get_documents(db, run_id)

    try:
        # ---------------------------------------------------------
        # Extraction stage
        # ---------------------------------------------------------
        if run.current_stage in {
            ProcessingStage.INGEST,
            ProcessingStage.EXTRACT,
        }:
            run.current_stage = ProcessingStage.EXTRACT
            run.updated_at = datetime.now(timezone.utc)

            db.commit()

        for document in documents:
            metadata = {}

            if document.metadata_json:
                try:
                    metadata = json.loads(document.metadata_json)
                except json.JSONDecodeError:
                    metadata = {}

            if metadata.get("extraction_completed") is True:
                continue

            # The upload layer may have populated extracted_text for
            # immediately available text documents. Reset it here because
            # orchestration extraction must be the authoritative checkpoint.
            document.extracted_text = None
            db.commit()

            extracted_text = extract_text(
                document.storage_reference,
                document.mime_type,
            )

            if not extracted_text.strip():
                raise OrchestrationError(
                    f"Document {document.id} extraction produced no text"
                )

            document.extracted_text = extracted_text

            metadata["extraction_completed"] = True
            document.metadata_json = json.dumps(metadata)

            db.commit()


        # Only advance the RUN after every document has
        # successfully completed extraction.
        run.current_stage = ProcessingStage.ANALYZE
        run.updated_at = datetime.now(timezone.utc)
        db.commit()
        # ---------------------------------------------------------
        # Analysis stage
        # ---------------------------------------------------------
        if run.current_stage == ProcessingStage.ANALYZE:
            for document in documents:
                # Resume support:
                # skip documents that were already analyzed.
                if (
                    document.summary is not None
                    and document.word_count is not None
                    and document.character_count is not None
                    and document.sentence_count is not None
                ):
                    continue

                if not document.extracted_text:
                    raise OrchestrationError(
                        f"Document {document.id} has no extracted text"
                    )

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
                document.character_count = analysis_result[
                    "character_count"
                ]
                document.sentence_count = analysis_result[
                    "sentence_count"
                ]

                # Persist each document immediately.
                db.commit()

            # All analysis is complete.
            run.current_stage = ProcessingStage.REVIEW
            run.status = RunStatus.PAUSED
            run.review_status = ReviewStatus.PENDING
            run.updated_at = datetime.now(timezone.utc)
            run.completed_at = None

            db.commit()
            db.refresh(run)

            return run

        # Defensive fallback.
        raise OrchestrationError(
            f"Run {run_id} reached unexpected stage "
            f"{run.current_stage.value}"
        )

    except OrchestrationError:
        db.rollback()

        # The last committed checkpoint remains persisted.
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