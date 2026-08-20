import uuid
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_create_run() -> None:
    response = client.post("/runs")

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert uuid.UUID(data["id"])

    assert data["status"] == "pending"
    assert data["current_stage"] == "ingest"

    assert data["error_message"] is None
    assert data["started_at"] is None
    assert data["completed_at"] is None


def test_get_run() -> None:
    create_response = client.post("/runs")

    assert create_response.status_code == 201

    run_id = create_response.json()["id"]

    response = client.get(f"/runs/{run_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == run_id
    assert data["status"] == "pending"
    assert data["current_stage"] == "ingest"


def test_get_missing_run() -> None:
    run_id = uuid.uuid4()

    response = client.get(f"/runs/{run_id}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Run not found",
    }

def test_detect_conflict_between_documents(client, db_session):
    # Create a run
    response = client.post("/runs")
    assert response.status_code == 201
    run_id = response.json()["id"]

    # Create two documents through the existing API
    first = client.post(
        f"/runs/{run_id}/documents",
        files={"file": ("first.txt", b"Inspection interval is 30 days", "text/plain")},
    )
    second = client.post(
        f"/runs/{run_id}/documents",
        files={"file": ("second.txt", b"Inspection interval is 45 days", "text/plain")},
    )

    assert first.status_code in (200, 201)
    assert second.status_code in (200, 201)

    # Detect conflicts
    response = client.post(f"/runs/{run_id}/conflicts")

    assert response.status_code == 200

    conflicts = response.json()

    assert len(conflicts) == 1
    assert "inspection interval" in conflicts[0]["title"].lower()


def test_get_run_conflicts(client):
    response = client.post("/runs")
    assert response.status_code == 201

    run_id = response.json()["id"]

    response = client.get(f"/runs/{run_id}/conflicts")

    assert response.status_code == 200
    assert response.json() == []


def test_conflict_detection_is_idempotent(client):
    response = client.post("/runs")
    assert response.status_code == 201

    run_id = response.json()["id"]

    first = client.post(
        f"/runs/{run_id}/documents",
        files={"file": ("first.txt", b"Inspection interval is 30 days", "text/plain")},
    )
    second = client.post(
        f"/runs/{run_id}/documents",
        files={"file": ("second.txt", b"Inspection interval is 45 days", "text/plain")},
    )

    assert first.status_code in (200, 201)
    assert second.status_code in (200, 201)

    first_detection = client.post(f"/runs/{run_id}/conflicts")
    second_detection = client.post(f"/runs/{run_id}/conflicts")

    assert first_detection.status_code == 200
    assert second_detection.status_code == 200

    assert len(first_detection.json()) == 1
    assert len(second_detection.json()) == 0

    listed = client.get(f"/runs/{run_id}/conflicts")
    assert listed.status_code == 200
    assert len(listed.json()) == 1