import uuid

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.session import SessionLocal
from backend.app.models.document import Document
from backend.app.models.run import (
    ProcessingStage,
    ReviewStatus,
    Run,
    RunStatus,
)

client = TestClient(app)


def _create_review_run() -> uuid.UUID:
    with SessionLocal() as db:
        run = Run()
        db.add(run)
        db.flush()

        document = Document(
            run_id=run.id,
            filename="review.txt",
            mime_type="text/plain",
            storage_reference="review.txt",
            checksum=str(uuid.uuid4()),
            extracted_text="SuperDocs review test document.",
            summary="SuperDocs review test document",
            word_count=4,
            character_count=32,
            sentence_count=1,
        )

        db.add(document)

        run.status = RunStatus.PAUSED
        run.current_stage = ProcessingStage.REVIEW
        run.review_status = ReviewStatus.PENDING

        db.commit()

        return run.id


def test_approve_run() -> None:
    run_id = _create_review_run()

    response = client.post(f"/runs/{run_id}/approve")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == RunStatus.COMPLETED.value
    assert data["current_stage"] == ProcessingStage.COMPLETE.value
    assert data["review_status"] == ReviewStatus.APPROVED.value


def test_reject_run() -> None:
    run_id = _create_review_run()

    response = client.post(f"/runs/{run_id}/reject")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == RunStatus.FAILED.value
    assert data["review_status"] == ReviewStatus.REJECTED.value
    assert data["current_stage"] == ProcessingStage.REVIEW.value


def test_approve_missing_run_returns_404() -> None:
    run_id = uuid.uuid4()

    response = client.post(f"/runs/{run_id}/approve")

    assert response.status_code == 404


def test_reject_missing_run_returns_404() -> None:
    run_id = uuid.uuid4()

    response = client.post(f"/runs/{run_id}/reject")

    assert response.status_code == 404