from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.conflict import Conflict
from backend.app.models.document import Document
from backend.app.models.evidence import Evidence


def create_conflict(
    db: Session,
    run_id: UUID,
    title: str,
    description: str,
    severity: str = "medium",
    status: str = "pending",
) -> Conflict:
    conflict = Conflict(
        run_id=run_id,
        title=title,
        description=description,
        severity=severity,
        status=status,
    )
    db.add(conflict)
    db.commit()
    db.refresh(conflict)
    return conflict


def list_conflicts(
    db: Session,
    run_id: UUID,
) -> list[Conflict]:
    return list(
        db.scalars(
            select(Conflict)
            .where(Conflict.run_id == run_id)
            .order_by(Conflict.created_at.asc())
        ).all()
    )


def detect_conflicts(
    db: Session,
    run_id: UUID,
) -> list[Conflict]:
    """
    Detect deterministic contradictions between evidence belonging to
    different documents in the same run.

    This intentionally uses the evidence already persisted by Phase 13.
    It does not introduce another LLM or extraction pipeline.
    """

    documents = list(
        db.scalars(
            select(Document)
            .where(Document.run_id == run_id)
        ).all()
    )

    if len(documents) < 2:
        return []

    document_ids = [document.id for document in documents]

    evidence_items = list(
        db.scalars(
            select(Evidence)
            .where(Evidence.document_id.in_(document_ids))
            .order_by(Evidence.created_at.asc())
        ).all()
    )

    existing = list_conflicts(db, run_id)

    existing_keys = {
        (
            conflict.title,
            conflict.description,
        )
        for conflict in existing
    }

    conflicts: list[Conflict] = []

    for index, left in enumerate(evidence_items):
        left_claim = _normalise_claim(left.claim)

        if not left_claim:
            continue

        for right in evidence_items[index + 1 :]:
            if left.document_id == right.document_id:
                continue

            right_claim = _normalise_claim(right.claim)

            if not right_claim:
                continue

            parsed_left = _parse_claim(left_claim)
            parsed_right = _parse_claim(right_claim)

            if not parsed_left or not parsed_right:
                continue

            left_subject, left_value = parsed_left
            right_subject, right_value = parsed_right

            if left_subject != right_subject:
                continue

            if left_value == right_value:
                continue

            title = f"Conflicting evidence: {left_subject}"

            description = (
                f"Different documents provide different values for "
                f"'{left_subject}'. "
                f"Document {left.document_id} states '{left.claim}', "
                f"while document {right.document_id} states "
                f"'{right.claim}'. "
                f"Evidence IDs: {left.id}, {right.id}."
            )

            key = (title, description)

            if key in existing_keys:
                continue

            conflict = Conflict(
                run_id=run_id,
                title=title,
                description=description,
                severity="medium",
                status="pending",
            )

            db.add(conflict)
            existing_keys.add(key)
            conflicts.append(conflict)

    if conflicts:
        db.commit()
        for conflict in conflicts:
            db.refresh(conflict)

    return conflicts


def _normalise_claim(claim: str | None) -> str:
    if not claim:
        return ""

    return " ".join(claim.strip().lower().split())


def _parse_claim(claim: str) -> tuple[str, str] | None:
    """
    Extract a simple subject/value pair from common factual claim formats.

    Examples:
        "inspection interval: 30 days"
        "inspection interval is 30 days"
        "inspection interval = 30 days"
    """

    separators = (
        " is ",
        " = ",
        ": ",
    )

    for separator in separators:
        if separator in claim:
            subject, value = claim.split(separator, 1)

            subject = subject.strip(" .")
            value = value.strip(" .")

            if subject and value:
                return subject, value

    return None