import io
import uuid
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import SessionLocal
from backend.app.models.document import Document
import threading
from concurrent.futures import ThreadPoolExecutor

from backend.app.models.run import Run, RunStatus

client = TestClient(app)


def test_run_orchestration_end_to_end() -> None:
    # 1. Create a run
    create_response = client.post("/runs")

    assert create_response.status_code == 201

    run = create_response.json()
    run_id = run["id"]

    assert run["status"] == "pending"
    assert run["current_stage"] == "ingest"

    # 2. Upload a document to the run
    document_content = (
        b"SuperDocs processes documents. "
        b"The system extracts useful information."
    )

    upload_response = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "document.txt",
                io.BytesIO(document_content),
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 201

    document = upload_response.json()

    assert document["run_id"] == run_id
    assert document["filename"] == "document.txt"
    assert document["mime_type"] == "text/plain"

    # 3. Start processing
    process_response = client.post(
        f"/runs/{run_id}/process"
    )

    assert process_response.status_code == 200

    processed_run = process_response.json()

    assert processed_run["id"] == run_id
    assert processed_run["status"] == "paused"
    assert processed_run["current_stage"] == "review"

    # 4. Verify the run reached the review boundary
    get_response = client.get(f"/runs/{run_id}")

    assert get_response.status_code == 200

    current_run = get_response.json()

    assert current_run["status"] == "paused"
    assert current_run["current_stage"] == "review"

    # 5. Approve the run
    approve_response = client.post(
        f"/runs/{run_id}/approve"
    )

    assert approve_response.status_code == 200

    completed_run = approve_response.json()

    assert completed_run["id"] == run_id
    assert completed_run["status"] == "completed"
    assert completed_run["current_stage"] == "complete"

def test_run_orchestration_processes_multiple_documents() -> None:
    create_response = client.post("/runs")

    assert create_response.status_code == 201

    run = create_response.json()
    run_id = run["id"]

    first_document = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "first.txt",
                io.BytesIO(
                    b"First SuperDocs document. "
                    b"It contains the first set of information."
                ),
                "text/plain",
            )
        },
    )

    second_document = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "second.txt",
                io.BytesIO(
                    b"Second SuperDocs document. "
                    b"It contains the second set of information."
                ),
                "text/plain",
            )
        },
    )

    assert first_document.status_code == 201
    assert second_document.status_code == 201

    process_response = client.post(
        f"/runs/{run_id}/process"
    )

    assert process_response.status_code == 200

    processed_run = process_response.json()

    assert processed_run["id"] == run_id
    assert processed_run["status"] == "paused"
    assert processed_run["current_stage"] == "review"

    with SessionLocal() as db:
        documents = (
            db.query(Document)
            .filter(Document.run_id == uuid.UUID(run_id))
            .order_by(Document.created_at.asc())
            .all()
        )

        assert len(documents) == 2

        for document in documents:
            assert document.extracted_text is not None
            assert document.summary is not None
            assert document.word_count is not None
            assert document.character_count is not None
            assert document.sentence_count is not None

def test_run_orchestration_isolates_documents_between_runs() -> None:
    # Create two independent runs.
    first_run_response = client.post("/runs")
    second_run_response = client.post("/runs")

    assert first_run_response.status_code == 201
    assert second_run_response.status_code == 201

    first_run_id = first_run_response.json()["id"]
    second_run_id = second_run_response.json()["id"]

    # Upload a document to each run.
    first_document_response = client.post(
        f"/runs/{first_run_id}/documents",
        files={
            "file": (
                "first.txt",
                io.BytesIO(
                    b"First run document. "
                    b"This belongs only to the first run."
                ),
                "text/plain",
            )
        },
    )

    second_document_response = client.post(
        f"/runs/{second_run_id}/documents",
        files={
            "file": (
                "second.txt",
                io.BytesIO(
                    b"Second run document. "
                    b"This belongs only to the second run."
                ),
                "text/plain",
            )
        },
    )

    assert first_document_response.status_code == 201
    assert second_document_response.status_code == 201

    # Process only the first run.
    process_response = client.post(
        f"/runs/{first_run_id}/process"
    )

    assert process_response.status_code == 200

    processed_first_run = process_response.json()

    assert processed_first_run["id"] == first_run_id
    assert processed_first_run["status"] == "paused"
    assert processed_first_run["current_stage"] == "review"

    # The second run must remain untouched.
    second_run_response = client.get(
        f"/runs/{second_run_id}"
    )

    assert second_run_response.status_code == 200

    second_run = second_run_response.json()

    assert second_run["status"] == "pending"
    assert second_run["current_stage"] == "ingest"

    # Verify persisted document state is isolated.
    with SessionLocal() as db:
        first_documents = (
            db.query(Document)
            .filter(
                Document.run_id == uuid.UUID(first_run_id)
            )
            .all()
        )

        second_documents = (
            db.query(Document)
            .filter(
                Document.run_id == uuid.UUID(second_run_id)
            )
            .all()
        )

        assert len(first_documents) == 1
        assert len(second_documents) == 1

        first_document = first_documents[0]
        second_document = second_documents[0]

        assert first_document.extracted_text is not None
        assert first_document.summary is not None
        assert first_document.word_count is not None

        assert second_document.extracted_text == (
            "Second run document. This belongs only to the second run."
        )
        assert second_document.summary is None
        assert second_document.word_count is None
        assert second_document.character_count is None
        assert second_document.sentence_count is None


def test_run_review_actions_are_isolated() -> None:
    # Create two independent runs.
    first_run_response = client.post("/runs")
    second_run_response = client.post("/runs")

    assert first_run_response.status_code == 201
    assert second_run_response.status_code == 201

    first_run_id = first_run_response.json()["id"]
    second_run_id = second_run_response.json()["id"]

    # Give both runs a document.
    for run_id, filename, content in [
        (
            first_run_id,
            "first.txt",
            b"First run content.",
        ),
        (
            second_run_id,
            "second.txt",
            b"Second run content.",
        ),
    ]:
        response = client.post(
            f"/runs/{run_id}/documents",
            files={
                "file": (
                    filename,
                    io.BytesIO(content),
                    "text/plain",
                )
            },
        )

        assert response.status_code == 201

    # Process both independently.
    first_process = client.post(
        f"/runs/{first_run_id}/process"
    )
    second_process = client.post(
        f"/runs/{second_run_id}/process"
    )

    assert first_process.status_code == 200
    assert second_process.status_code == 200

    assert first_process.json()["status"] == "paused"
    assert second_process.json()["status"] == "paused"

    # Approve only the first run.
    approve_response = client.post(
        f"/runs/{first_run_id}/approve"
    )

    assert approve_response.status_code == 200

    approved_run = approve_response.json()

    assert approved_run["status"] == "completed"
    assert approved_run["current_stage"] == "complete"

    # The second run must remain paused and awaiting review.
    second_run_response = client.get(
        f"/runs/{second_run_id}"
    )

    assert second_run_response.status_code == 200

    second_run = second_run_response.json()

    assert second_run["status"] == "paused"
    assert second_run["current_stage"] == "review"
    assert second_run["review_status"] == "pending"

def test_run_orchestration_failure_isolated_between_runs() -> None:
    # Create two independent runs.
    first_run_response = client.post("/runs")
    second_run_response = client.post("/runs")

    assert first_run_response.status_code == 201
    assert second_run_response.status_code == 201

    first_run_id = first_run_response.json()["id"]
    second_run_id = second_run_response.json()["id"]

    # Upload a valid document to the first run.
    first_document_response = client.post(
        f"/runs/{first_run_id}/documents",
        files={
            "file": (
                "first.txt",
                io.BytesIO(b"First run valid document."),
                "text/plain",
            )
        },
    )

    # Upload a valid document to the second run.
    second_document_response = client.post(
        f"/runs/{second_run_id}/documents",
        files={
            "file": (
                "second.txt",
                io.BytesIO(b"Second run valid document."),
                "text/plain",
            )
        },
    )

    assert first_document_response.status_code == 201
    assert second_document_response.status_code == 201

    first_document = first_document_response.json()
    first_document_id = first_document["id"]

    # Corrupt only Run A's storage reference so its extraction fails.
    with SessionLocal() as db:
        document = db.get(
            Document,
            uuid.UUID(first_document_id),
        )

        assert document is not None

        document.storage_reference = (
            "uploads/this-file-does-not-exist.txt"
        )

        db.commit()

    # Process Run A.
    process_response = client.post(
        f"/runs/{first_run_id}/process"
    )

    assert process_response.status_code == 409

    failed_run_response = client.get(
        f"/runs/{first_run_id}"
    )

    assert failed_run_response.status_code == 200

    failed_run = failed_run_response.json()

    assert failed_run["status"] == "failed"
    assert failed_run["current_stage"] == "extract"
    assert failed_run["error_message"] is not None

    # Run B must remain completely unaffected.
    second_run_response = client.get(
        f"/runs/{second_run_id}"
    )

    assert second_run_response.status_code == 200

    second_run = second_run_response.json()

    assert second_run["status"] == "pending"
    assert second_run["current_stage"] == "ingest"
    assert second_run["error_message"] is None

    # Run B's document must remain untouched by orchestration.
    with SessionLocal() as db:
        second_documents = (
            db.query(Document)
            .filter(
                Document.run_id == uuid.UUID(second_run_id)
            )
            .all()
        )

        assert len(second_documents) == 1

        second_document = second_documents[0]

        assert second_document.summary is None
        assert second_document.word_count is None
        assert second_document.character_count is None
        assert second_document.sentence_count is None

def test_run_orchestration_resumes_after_extraction_failure(
    monkeypatch,
) -> None:
    first_run_response = client.post("/runs")

    assert first_run_response.status_code == 201

    run_id = first_run_response.json()["id"]

    first_document_response = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "first.txt",
                io.BytesIO(
                    b"First document. "
                    b"This document should survive the interruption."
                ),
                "text/plain",
            )
        },
    )

    second_document_response = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "second.txt",
                io.BytesIO(
                    b"Second document. "
                    b"This document should be processed after resume."
                ),
                "text/plain",
            )
        },
    )

    assert first_document_response.status_code == 201
    assert second_document_response.status_code == 201

    from backend.app.services import orchestrator

    original_extract_text = orchestrator.extract_text
    first_attempt_calls: list[str] = []

    def failing_extract_text(
        file_path: str,
        mime_type: str,
    ) -> str:
        first_attempt_calls.append(file_path)

        if len(first_attempt_calls) == 2:
            raise RuntimeError("simulated worker interruption")

        return original_extract_text(file_path, mime_type)

    monkeypatch.setattr(
        orchestrator,
        "extract_text",
        failing_extract_text,
    )

    # ---------------------------------------------------------
    # First attempt:
    # extraction succeeds for document 1, then the worker
    # fails while processing document 2.
    # ---------------------------------------------------------
    process_response = client.post(
        f"/runs/{run_id}/process"
    )

    assert process_response.status_code == 409

    failed_run_response = client.get(
        f"/runs/{run_id}"
    )

    assert failed_run_response.status_code == 200

    failed_run = failed_run_response.json()

    assert failed_run["status"] == "failed"
    assert failed_run["current_stage"] == "extract"

    with SessionLocal() as db:
        documents = (
            db.query(Document)
            .filter(
                Document.run_id == uuid.UUID(run_id)
            )
            .order_by(Document.created_at.asc())
            .all()
        )

        assert len(documents) == 2

        assert documents[0].extracted_text is not None
        assert documents[0].extracted_text.startswith(
            "First document."
        )

        assert documents[1].extracted_text is None

    # ---------------------------------------------------------
    # Simulate the worker restarting.
    #
    # The persisted checkpoint must allow the orchestrator to
    # continue from the unfinished document rather than losing
    # the completed extraction.
    # ---------------------------------------------------------
    resume_calls: list[str] = []

    def tracking_extract_text(
        file_path: str,
        mime_type: str,
    ) -> str:
        resume_calls.append(file_path)
        return original_extract_text(file_path, mime_type)

    monkeypatch.setattr(
        orchestrator,
        "extract_text",
        tracking_extract_text,
    )

    resume_response = client.post(
        f"/runs/{run_id}/process"
    )

    assert resume_response.status_code == 200

    resumed_run = resume_response.json()

    assert resumed_run["id"] == run_id
    assert resumed_run["status"] == "paused"
    assert resumed_run["current_stage"] == "review"

    # Only the unfinished second document should have been
    # extracted during the resumed execution.
    assert len(resume_calls) == 1

    with SessionLocal() as db:
        documents = (
            db.query(Document)
            .filter(
                Document.run_id == uuid.UUID(run_id)
            )
            .order_by(Document.created_at.asc())
            .all()
        )

        assert len(documents) == 2

        for document in documents:
            assert document.extracted_text is not None
            assert document.summary is not None
            assert document.word_count is not None
            assert document.character_count is not None
            assert document.sentence_count is not None

def test_concurrent_runs_remain_isolated() -> None:
    # Create two completely independent runs.
    run_a_response = client.post("/runs")
    run_b_response = client.post("/runs")

    assert run_a_response.status_code == 201
    assert run_b_response.status_code == 201

    run_a_id = run_a_response.json()["id"]
    run_b_id = run_b_response.json()["id"]

    # Give each run its own document.
    document_a_response = client.post(
        f"/runs/{run_a_id}/documents",
        files={
            "file": (
                "run-a.txt",
                io.BytesIO(
                    b"Run A document. This belongs only to Run A."
                ),
                "text/plain",
            )
        },
    )

    document_b_response = client.post(
        f"/runs/{run_b_id}/documents",
        files={
            "file": (
                "run-b.txt",
                io.BytesIO(
                    b"Run B document. This belongs only to Run B."
                ),
                "text/plain",
            )
        },
    )

    assert document_a_response.status_code == 201
    assert document_b_response.status_code == 201

    # Process both runs concurrently.
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(
            client.post,
            f"/runs/{run_a_id}/process",
        )
        future_b = executor.submit(
            client.post,
            f"/runs/{run_b_id}/process",
        )

        response_a = future_a.result()
        response_b = future_b.result()

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    result_a = response_a.json()
    result_b = response_b.json()

    assert result_a["id"] == run_a_id
    assert result_b["id"] == run_b_id

    assert result_a["status"] == "paused"
    assert result_b["status"] == "paused"

    assert result_a["current_stage"] == "review"
    assert result_b["current_stage"] == "review"

    # Verify the persisted document state remains isolated.
    with SessionLocal() as db:
        documents_a = (
            db.query(Document)
            .filter(Document.run_id == uuid.UUID(run_a_id))
            .all()
        )

        documents_b = (
            db.query(Document)
            .filter(Document.run_id == uuid.UUID(run_b_id))
            .all()
        )

        assert len(documents_a) == 1
        assert len(documents_b) == 1

        assert documents_a[0].extracted_text == (
            "Run A document. This belongs only to Run A."
        )

        assert documents_b[0].extracted_text == (
            "Run B document. This belongs only to Run B."
        )

        assert documents_a[0].summary is not None
        assert documents_b[0].summary is not None


def test_duplicate_process_same_run_is_rejected() -> None:
    run_response = client.post("/runs")

    assert run_response.status_code == 201

    run_id = run_response.json()["id"]

    document_response = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "document.txt",
                io.BytesIO(
                    b"This document is processed exactly once."
                ),
                "text/plain",
            )
        },
    )

    assert document_response.status_code == 201

    # Claim the run before the duplicate request.
    with SessionLocal() as db:
        run = db.get(Run, uuid.UUID(run_id))

        assert run is not None

        run.status = RunStatus.RUNNING
        db.commit()

    duplicate_response = client.post(
        f"/runs/{run_id}/process"
    )

    assert duplicate_response.status_code == 409

    body = duplicate_response.json()

    assert "cannot be processed" in body["detail"]


def test_concurrent_process_same_run_does_not_duplicate_work(
    monkeypatch,
) -> None:
    run_response = client.post("/runs")

    assert run_response.status_code == 201

    run_id = run_response.json()["id"]

    document_response = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "document.txt",
                io.BytesIO(
                    b"This document must only be extracted once."
                ),
                "text/plain",
            )
        },
    )

    assert document_response.status_code == 201

    from backend.app.services import orchestrator

    original_extract_text = orchestrator.extract_text

    extraction_calls: list[str] = []
    extraction_lock = threading.Lock()

    def tracked_extract_text(
        file_path: str,
        mime_type: str,
    ) -> str:
        with extraction_lock:
            extraction_calls.append(file_path)

        return original_extract_text(file_path, mime_type)

    monkeypatch.setattr(
        orchestrator,
        "extract_text",
        tracked_extract_text,
    )

    # Make both requests start at approximately the same time.
    barrier = threading.Barrier(2)

    def process() -> object:
        barrier.wait()
        return client.post(
            f"/runs/{run_id}/process"
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(process)
        future_b = executor.submit(process)

        response_a = future_a.result()
        response_b = future_b.result()

    statuses = {
        response_a.status_code,
        response_b.status_code,
    }

    # Exactly one request owns the processing operation.
    assert statuses == {200, 409}

    # Extraction must not happen twice.
    assert len(extraction_calls) == 1

    final_response = client.get(
        f"/runs/{run_id}"
    )

    assert final_response.status_code == 200

    final_run = final_response.json()

    assert final_run["status"] == "paused"
    assert final_run["current_stage"] == "review"

    with SessionLocal() as db:
        documents = (
            db.query(Document)
            .filter(Document.run_id == uuid.UUID(run_id))
            .all()
        )

        assert len(documents) == 1
        assert documents[0].extracted_text is not None
        assert documents[0].summary is not None