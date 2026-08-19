from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.agents.analyzer import AnalyzerAgent
from backend.app.agents.extraction import run_extraction
from backend.app.models.run import ProcessingStage, Run, RunStatus


class OrchestrationError(Exception):
    """Raised when a run cannot be processed."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _set_stage(
    run: Run,
    stage: ProcessingStage,
) -> None:
    run.current_stage = stage
    run.updated_at = _utcnow()


def _set_running(run: Run) -> None:
    run.status = RunStatus.RUNNING

    if run.started_at is None:
        run.started_at = _utcnow()

    run.updated_at = _utcnow()


def _complete(run: Run) -> None:
    run.status = RunStatus.COMPLETED
    run.current_stage = ProcessingStage.COMPLETE
    run.completed_at = _utcnow()
    run.updated_at = _utcnow()


def _fail(run: Run, error: Exception) -> None:
    run.status = RunStatus.FAILED
    run.error_message = str(error)
    run.updated_at = _utcnow()


def process_run(db: Session, run_id: UUID) -> Run:
    """
    Execute the complete persisted SuperDocs workflow.

    Workflow:

        INGEST
          ↓
        EXTRACT
          ↓
        ANALYZE
          ↓
        REVIEW
          ↓
        COMMIT
          ↓
        COMPLETE

    The orchestrator owns workflow state and delegates actual work
    to specialized agents/services.
    """

    run = db.get(Run, run_id)

    if run is None:
        raise OrchestrationError(
            f"Run {run_id} was not found"
        )

    if run.status == RunStatus.COMPLETED:
        return run

    if run.status == RunStatus.RUNNING:
        raise OrchestrationError(
            f"Run {run_id} is already being processed"
        )

    if not run.documents:
        raise OrchestrationError(
            "Cannot process run without documents"
        )

    document = run.documents[0]

    try:
        # =========================================================
        # START
        # =========================================================

        _set_running(run)
        db.commit()

        # =========================================================
        # INGEST
        # =========================================================

        _set_stage(run, ProcessingStage.INGEST)
        db.commit()

        # The document has already been persisted by the ingestion
        # layer. At this point we validate that the workflow has a
        # document to process.

        # =========================================================
        # EXTRACT
        # =========================================================

        _set_stage(run, ProcessingStage.EXTRACT)
        db.commit()

        extracted_text = run_extraction(
            document.storage_reference,
            document.mime_type,
        )

        document.extracted_text = extracted_text

        db.commit()

        # =========================================================
        # ANALYZE
        # =========================================================

        _set_stage(run, ProcessingStage.ANALYZE)
        db.commit()

        analyzer = AnalyzerAgent()
        analysis = analyzer.analyze(extracted_text)

        document.summary = analysis.summary
        document.word_count = analysis.word_count
        document.character_count = analysis.character_count
        document.sentence_count = analysis.sentence_count

        db.commit()

        # =========================================================
        # REVIEW
        # =========================================================

        _set_stage(run, ProcessingStage.REVIEW)
        db.commit()

        # Review is currently an explicit workflow boundary.
        #
        # Phase 10 can introduce human approval / review decisions
        # without changing extraction or analysis.

        # =========================================================
        # COMMIT
        # =========================================================

        _set_stage(run, ProcessingStage.COMMIT)
        db.commit()

        # The extracted content and analysis results are already
        # persisted on the Document record. COMMIT represents the
        # final workflow persistence boundary.

        # =========================================================
        # COMPLETE
        # =========================================================

        _complete(run)
        db.commit()

        db.refresh(document)
        db.refresh(run)

        return run

    except OrchestrationError:
        db.rollback()

        run = db.get(Run, run_id)

        if run is not None:
            _fail(run, OrchestrationError("Run orchestration failed"))
            db.commit()

        raise

    except Exception as exc:
        db.rollback()

        run = db.get(Run, run_id)

        if run is None:
            raise OrchestrationError(
                f"Run {run_id} disappeared during processing"
            ) from exc

        _fail(run, exc)
        db.commit()
        db.refresh(run)

        raise OrchestrationError(str(exc)) from exc