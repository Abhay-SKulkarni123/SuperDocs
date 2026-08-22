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
    Detect deterministic contradictions between documents
    belonging to the same run.

    Persisted evidence is preferred. If no evidence exists,
    fall back to the extracted document text.
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

    # ---------------------------------------------------------
    # Path 1: Use persisted evidence when available
    # ---------------------------------------------------------
    if evidence_items:
        claims_by_document: dict[
            UUID,
            list[tuple[str, str]],
        ] = {}

        for evidence in evidence_items:
            parsed = _parse_claim(
                _normalise_claim(evidence.claim)
            )

            if parsed:
                claims_by_document.setdefault(
                    evidence.document_id,
                    [],
                ).append(parsed)

        conflicts.extend(
            _detect_claim_conflicts(
                db=db,
                run_id=run_id,
                claims_by_document=claims_by_document,
                existing_keys=existing_keys,
                evidence_items=evidence_items,
            )
        )

    # ---------------------------------------------------------
    # Path 2: No evidence yet — use extracted document text
    # ---------------------------------------------------------
    else:
        claims_by_document: dict[
            UUID,
            list[tuple[str, str]],
        ] = {}

        for document in documents:
            for claim in _extract_claims(
                document.extracted_text
            ):
                parsed = _parse_claim(
                    _normalise_claim(claim)
                )

                if parsed:
                    claims_by_document.setdefault(
                        document.id,
                        [],
                    ).append(parsed)

        conflicts.extend(
            _detect_claim_conflicts_from_documents(
                db=db,
                run_id=run_id,
                claims_by_document=claims_by_document,
                existing_keys=existing_keys,
            )
        )

    # ---------------------------------------------------------
    # Persist newly detected conflicts
    # ---------------------------------------------------------
    if conflicts:
        db.commit()

        for conflict in conflicts:
            db.refresh(conflict)

    return conflicts

def _detect_claim_conflicts(
    db: Session,
    run_id: UUID,
    claims_by_document: dict[UUID, list[tuple[str, str]]],
    existing_keys: set[tuple[str, str]],
    evidence_items: list[Evidence],
) -> list[Conflict]:

    conflicts: list[Conflict] = []

    document_ids = list(claims_by_document.keys())

    for index, left_document_id in enumerate(document_ids):
        for right_document_id in document_ids[index + 1:]:
            for left_subject, left_value in claims_by_document[
                left_document_id
            ]:
                for right_subject, right_value in claims_by_document[
                    right_document_id
                ]:
                    if left_subject != right_subject:
                        continue

                    if left_value == right_value:
                        continue

                    left_evidence = _find_evidence_for_claim(
                        evidence_items,
                        left_document_id,
                        left_subject,
                        left_value,
                    )

                    right_evidence = _find_evidence_for_claim(
                        evidence_items,
                        right_document_id,
                        right_subject,
                        right_value,
                    )

                    title = f"Conflicting evidence: {left_subject}"

                    description = (
                        f"Different documents provide different values for "
                        f"'{left_subject}'. "
                        f"Document {left_document_id} states "
                        f"'{left_evidence.claim if left_evidence else left_subject + ' is ' + left_value}', "
                        f"while document {right_document_id} states "
                        f"'{right_evidence.claim if right_evidence else right_subject + ' is ' + right_value}'."
                    )

                    if left_evidence and right_evidence:
                        description += (
                            f" Evidence IDs: {left_evidence.id}, "
                            f"{right_evidence.id}."
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

    return conflicts


def _detect_claim_conflicts_from_documents(
    db: Session,
    run_id: UUID,
    claims_by_document: dict[UUID, list[tuple[str, str]]],
    existing_keys: set[tuple[str, str]],
) -> list[Conflict]:
    conflicts: list[Conflict] = []

    document_ids = list(claims_by_document.keys())

    for index, left_document_id in enumerate(document_ids):
        for right_document_id in document_ids[index + 1:]:
            for left_subject, left_value in claims_by_document[
                left_document_id
            ]:
                for right_subject, right_value in claims_by_document[
                    right_document_id
                ]:
                    if left_subject != right_subject:
                        continue

                    if left_value == right_value:
                        continue

                    title = f"Conflicting evidence: {left_subject}"

                    description = (
                        f"Different documents provide different values for "
                        f"'{left_subject}'. "
                        f"Document {left_document_id} states "
                        f"'{left_subject} is {left_value}', "
                        f"while document {right_document_id} states "
                        f"'{right_subject} is {right_value}'."
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

    return conflicts

def _find_evidence_for_claim(
    evidence_items: list[Evidence],
    document_id: UUID,
    subject: str,
    value: str,
) -> Evidence | None:
    for evidence in evidence_items:
        if evidence.document_id != document_id:
            continue

        parsed = _parse_claim(
            _normalise_claim(evidence.claim)
        )

        if parsed == (subject, value):
            return evidence

    return None


def _extract_claims(text: str | None) -> list[str]:
    if not text:
        return []

    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


def _normalise_claim(claim: str | None) -> str:
    if not claim:
        return ""

    return " ".join(
        claim.strip().lower().split()
    )


def _parse_claim(
    claim: str,
) -> tuple[str, str] | None:
    separators = (
        " is ",
        " = ",
        ": ",
    )

    for separator in separators:
        if separator in claim:
            subject, value = claim.split(
                separator,
                1,
            )

            subject = subject.strip(" .")
            value = value.strip(" .")

            if subject and value:
                return subject, value

    return None