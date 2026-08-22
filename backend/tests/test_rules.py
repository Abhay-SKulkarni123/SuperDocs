import uuid

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def create_run() -> str:
    response = client.post("/runs")

    assert response.status_code == 201

    return response.json()["id"]


def test_create_rule() -> None:
    run_id = create_run()

    response = client.post(
        f"/runs/{run_id}/rules",
        json={
            "name": "Inspection interval",
            "description": "Verify inspection interval.",
            "requirement": "must contain inspection interval",
            "severity": "high",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert uuid.UUID(data["id"])
    assert data["run_id"] == run_id
    assert data["name"] == "Inspection interval"
    assert data["description"] == "Verify inspection interval."
    assert data["requirement"] == "must contain inspection interval"
    assert data["severity"] == "high"


def test_list_rules() -> None:
    run_id = create_run()

    client.post(
        f"/runs/{run_id}/rules",
        json={
            "name": "Rule one",
            "requirement": "must contain approval",
        },
    )

    client.post(
        f"/runs/{run_id}/rules",
        json={
            "name": "Rule two",
            "requirement": "must contain signature",
        },
    )

    response = client.get(
        f"/runs/{run_id}/rules"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Rule one"
    assert data[1]["name"] == "Rule two"


def test_create_rule_for_missing_run() -> None:
    run_id = uuid.uuid4()

    response = client.post(
        f"/runs/{run_id}/rules",
        json={
            "name": "Missing run rule",
            "requirement": "must contain approval",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Run not found",
    }


def test_list_rules_for_missing_run() -> None:
    run_id = uuid.uuid4()

    response = client.get(
        f"/runs/{run_id}/rules"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Run not found",
    }


def test_evaluate_rules_with_no_evidence_is_inconclusive() -> None:
    run_id = create_run()

    client.post(
        f"/runs/{run_id}/rules",
        json={
            "name": "Approval requirement",
            "requirement": "must contain approval",
        },
    )

    response = client.post(
        f"/runs/{run_id}/rules/evaluate"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["status"] == "inconclusive"
    assert data[0]["evidence_ids"] == []


def test_evaluate_rule_with_matching_evidence() -> None:
    run_id = create_run()

    document = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "approval.txt",
                b"Final approval was granted by the compliance team.",
                "text/plain",
            )
        },
    )

    assert document.status_code in (200, 201)

    client.post(
        f"/runs/{run_id}/rules",
        json={
            "name": "Approval requirement",
            "requirement": "must contain approval",
        },
    )

    response = client.post(
        f"/runs/{run_id}/rules/evaluate"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["status"] == "pass"
    assert data[0]["evidence_ids"]


def test_evaluate_rule_with_non_matching_evidence() -> None:
    run_id = create_run()

    document = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "document.txt",
                b"The document contains a delivery schedule.",
                "text/plain",
            )
        },
    )

    assert document.status_code in (200, 201)

    client.post(
        f"/runs/{run_id}/rules",
        json={
            "name": "Approval requirement",
            "requirement": "must contain approval",
        },
    )

    response = client.post(
        f"/runs/{run_id}/rules/evaluate"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["status"] == "fail"
    assert data[0]["evidence_ids"] == []


def test_evaluate_missing_run() -> None:
    run_id = uuid.uuid4()

    response = client.post(
        f"/runs/{run_id}/rules/evaluate"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Run not found",
    }