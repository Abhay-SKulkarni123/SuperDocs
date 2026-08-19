from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.models.document import Document
from backend.app.models.run import ProcessingStage, Run, RunStatus
from backend.app.services.processing import ProcessingError, process_run


def test_process_run_extracts_document(tmp_path: Path) -> None:
    document_path = tmp_path / "document.txt"
    document_path.write_text(
        "SuperDocs processing pipeline.",
        encoding="utf-8",
    )

    with SessionLocal() as db:
        run = Run()
        db.add(run)
        db.flush()

        document = Document(
            run_id=run.id,
            filename="document.txt",
            mime_type="text/plain",
            storage_reference=str(document_path),
            checksum="processing-test-checksum",
        )
        db.add(document)
        db.commit()

        text = process_run(db, run.id)

        assert text == "SuperDocs processing pipeline."

        db.refresh(run)

        assert run.status == RunStatus.COMPLETED
        assert run.current_stage == ProcessingStage.COMPLETE
        assert run.started_at is not None
        assert run.completed_at is not None
        assert run.error_message is None

        db.delete(document)
        db.delete(run)
        db.commit()


def test_process_run_requires_document() -> None:
    with SessionLocal() as db:
        run = Run()
        db.add(run)
        db.commit()

        run_id = run.id

        with pytest.raises(
            ProcessingError,
            match="No document found for run",
        ):
            process_run(db, run_id)

        db.delete(run)
        db.commit()


def test_process_run_requires_existing_run() -> None:
    with SessionLocal() as db:
        with pytest.raises(
            ProcessingError,
            match="Run not found",
        ):
            process_run(db, uuid4())