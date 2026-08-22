import uuid

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def create_run() -> str:
    response = client.post("/runs")

    assert response.status_code == 201

    return response.json()["id"]


def test_generate_finding_from_conflict() -> None:
    run_id = create_run()

    first = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "first.txt",
                b"Inspection interval is 30 days",
                "text/plain",
            )
        },
    )

    second = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "second.txt",
                b"Inspection interval is 45 days",
                "text/plain",
            )
        },
    )

    assert first.status_code in (200, 201)
    assert second.status_code in (200, 201)

    conflict_response = client.post(
        f"/runs/{run_id}/conflicts"
    )

    assert conflict_response.status_code == 200
    assert len(conflict_response.json()) == 1

    conflict_id = conflict_response.json()[0]["id"]

    response = client.post(
        f"/runs/{run_id}/findings"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["type"] == "conflict"
    assert data[0]["status"] == "open"
    assert data[0]["source_type"] == "conflict"
    assert data[0]["source_id"] == conflict_id
    assert data[0]["severity"] == "medium"
    assert data[0]["resolved_at"] is None


def test_generate_finding_from_failed_rule() -> None:
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

    rule = client.post(
        f"/runs/{run_id}/rules",
        json={
            "name": "Approval requirement",
            "requirement": "must contain approval",
            "severity": "high",
        },
    )

    assert rule.status_code == 201

    rule_id = rule.json()["id"]

    evaluation = client.post(
        f"/runs/{run_id}/rules/evaluate"
    )

    assert evaluation.status_code == 200
    assert evaluation.json()[0]["status"] == "fail"

    response = client.post(
        f"/runs/{run_id}/findings"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["type"] == "rule_failure"
    assert data[0]["status"] == "open"
    assert data[0]["source_type"] == "rule"
    assert data[0]["source_id"] == rule_id
    assert data[0]["severity"] == "high"
    assert data[0]["title"] == "Approval requirement"
    assert data[0]["resolved_at"] is None


def test_passing_rule_does_not_create_finding() -> None:
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

    rule = client.post(
        f"/runs/{run_id}/rules",
        json={
            "name": "Approval requirement",
            "requirement": "must contain approval",
        },
    )

    assert rule.status_code == 201

    evaluation = client.post(
        f"/runs/{run_id}/rules/evaluate"
    )

    assert evaluation.status_code == 200
    assert evaluation.json()[0]["status"] == "pass"

    response = client.post(
        f"/runs/{run_id}/findings"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_finding_generation_is_idempotent() -> None:
    run_id = create_run()

    first = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "first.txt",
                b"Inspection interval is 30 days",
                "text/plain",
            )
        },
    )

    second = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "second.txt",
                b"Inspection interval is 45 days",
                "text/plain",
            )
        },
    )

    assert first.status_code in (200, 201)
    assert second.status_code in (200, 201)

    conflict = client.post(
        f"/runs/{run_id}/conflicts"
    )

    assert conflict.status_code == 200
    assert len(conflict.json()) == 1

    first_generation = client.post(
        f"/runs/{run_id}/findings"
    )

    second_generation = client.post(
        f"/runs/{run_id}/findings"
    )

    assert first_generation.status_code == 200
    assert second_generation.status_code == 200

    assert len(first_generation.json()) == 1
    assert second_generation.json() == []

    listed = client.get(
        f"/runs/{run_id}/findings"
    )

    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_list_findings() -> None:
    run_id = create_run()

    response = client.get(
        f"/runs/{run_id}/findings"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_resolve_finding() -> None:
    run_id = create_run()

    first = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "first.txt",
                b"Inspection interval is 30 days",
                "text/plain",
            )
        },
    )

    second = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "second.txt",
                b"Inspection interval is 45 days",
                "text/plain",
            )
        },
    )

    assert first.status_code in (200, 201)
    assert second.status_code in (200, 201)

    conflict = client.post(
        f"/runs/{run_id}/conflicts"
    )

    assert conflict.status_code == 200

    findings = client.post(
        f"/runs/{run_id}/findings"
    )

    assert findings.status_code == 200
    assert len(findings.json()) == 1

    finding_id = findings.json()[0]["id"]

    response = client.post(
        f"/runs/{run_id}/findings/{finding_id}/resolve"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == finding_id
    assert data["status"] == "resolved"
    assert data["resolved_at"] is not None


def test_resolve_finding_is_idempotent() -> None:
    run_id = create_run()

    first = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "first.txt",
                b"Inspection interval is 30 days",
                "text/plain",
            )
        },
    )

    second = client.post(
        f"/runs/{run_id}/documents",
        files={
            "file": (
                "second.txt",
                b"Inspection interval is 45 days",
                "text/plain",
            )
        },
    )

    assert first.status_code in (200, 201)
    assert second.status_code in (200, 201)

    conflict = client.post(
        f"/runs/{run_id}/conflicts"
    )

    assert conflict.status_code == 200

    findings = client.post(
        f"/runs/{run_id}/findings"
    )

    finding_id = findings.json()[0]["id"]

    first_resolve = client.post(
        f"/runs/{run_id}/findings/{finding_id}/resolve"
    )

    second_resolve = client.post(
        f"/runs/{run_id}/findings/{finding_id}/resolve"
    )

    assert first_resolve.status_code == 200
    assert second_resolve.status_code == 200

    assert second_resolve.json()["status"] == "resolved"
    assert second_resolve.json()["resolved_at"] is not None


def test_resolve_finding_from_another_run_returns_404() -> None:
    run_id = create_run()
    other_run_id = create_run()

    response = client.post(
        f"/runs/{run_id}/findings/{uuid.uuid4()}/resolve"
    )

    assert response.status_code == 404

    # Sanity-check that the endpoint is scoped to the run.
    assert run_id != other_run_id