import io
import uuid
from hashlib import sha256

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def create_run() -> str:
    response = client.post("/runs")

    assert response.status_code == 201

    return response.json()["id"]


def test_upload_document() -> None:
    run_id = create_run()

    content = b"Hello SuperDocs"

    response = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "test.txt",
                io.BytesIO(content),
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert uuid.UUID(data["id"])
    assert data["run_id"] == run_id
    assert data["filename"] == "test.txt"
    assert data["mime_type"] == "text/plain"
    assert data["checksum"] == sha256(content).hexdigest()
    assert data["metadata_json"] is not None


def test_upload_document_for_missing_run() -> None:
    run_id = uuid.uuid4()

    response = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "test.txt",
                io.BytesIO(b"Hello"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Run not found",
    }


def test_upload_empty_document() -> None:
    run_id = create_run()

    response = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "empty.txt",
                io.BytesIO(b""),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Document is empty",
    }


def test_upload_unsupported_document() -> None:
    run_id = create_run()

    response = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "image.jpg",
                io.BytesIO(b"fake image"),
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 415
    assert response.json() == {
        "detail": "Unsupported document type",
    }