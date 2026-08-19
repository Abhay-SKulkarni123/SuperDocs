from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.run import ProcessingStage, Run, RunStatus


class OrchestrationError(Exception):
    """Raised when a run cannot be processed."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _set_stage(run: Run, stage: ProcessingStage) -> None:
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
    Execute the persisted SuperDocs workflow.

    The workflow is intentionally stage-oriented so each stage can later
    be replaced by a richer agent/service without changing the run model.
    """

    run = db.get(Run, run_id)

    if run is None:
        raise OrchestrationError(f"Run {run_id} was not found")

    if run.status == RunStatus.COMPLETED:
        return run

    if run.status == RunStatus.RUNNING:
        raise OrchestrationError(
            f"Run {run_id} is already being processed"
        )

    _set_running(run)
    db.commit()
    db.refresh(run)

    try:
        # ---------------------------------------------------------
        # INGEST
        # ---------------------------------------------------------
        _set_stage(run, ProcessingStage.INGEST)
        db.commit()

        # The document ingestion work is already represented by the
        # persisted Document model. This stage currently validates
        # that the run has documents associated with it.
        if not run.documents:
            raise OrchestrationError(
                "Cannot process run without documents"
            )

        # ---------------------------------------------------------
        # EXTRACT
        # ---------------------------------------------------------
        _set_stage(run, ProcessingStage.EXTRACT)
        db.commit()

        # Extraction is currently performed by the existing document
        # processing service. The orchestrator owns the workflow,
        # while the individual service owns the actual work.

        # ---------------------------------------------------------
        # ANALYZE
        # ---------------------------------------------------------
        _set_stage(run, ProcessingStage.ANALYZE)
        db.commit()

        # Analysis is likewise delegated to the analysis service.

        # ---------------------------------------------------------
        # REVIEW
        # ---------------------------------------------------------
        _set_stage(run, ProcessingStage.REVIEW)
        db.commit()

        # Review is intentionally a persisted workflow boundary.
        # Human approval will be attached here in Phase 10.

        # ---------------------------------------------------------
        # COMMIT
        # ---------------------------------------------------------
        _set_stage(run, ProcessingStage.COMMIT)
        db.commit()

        # Commit becomes the point at which approved results are
        # persisted as final output.

        # ---------------------------------------------------------
        # COMPLETE
        # ---------------------------------------------------------
        _complete(run)
        db.commit()
        db.refresh(run)

        return run

    except Exception as exc:
        db.rollback()

        # Re-fetch after rollback because SQLAlchemy may have expired
        # the current object state.
        run = db.get(Run, run_id)

        if run is None:
            raise OrchestrationError(
                f"Run {run_id} disappeared during processing"
            ) from exc

        _fail(run, exc)
        db.commit()
        db.refresh(run)

        raise OrchestrationError(str(exc)) from exc