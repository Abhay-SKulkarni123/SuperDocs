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