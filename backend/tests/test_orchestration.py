import io

from fastapi.testclient import TestClient

from backend.app.main import app


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