from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.document import Document
from backend.app.models.evidence import Evidence
from backend.app.models.rule import Rule
from backend.app.models.run import Run


def _ensure_run_exists(
    db: Session,
    run_id: UUID,
) -> None:
    statement = select(Run.id).where(Run.id == run_id)

    if db.scalar(statement) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )


def create_rule(
    db: Session,
    run_id: UUID,
    *,
    name: str,
    description: str | None,
    requirement: str,
    severity: str,
) -> Rule:
    _ensure_run_exists(db, run_id)

    rule = Rule(
        run_id=run_id,
        name=name,
        description=description,
        requirement=requirement,
        severity=severity,
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    return rule


def list_rules(
    db: Session,
    run_id: UUID,
) -> list[Rule]:
    _ensure_run_exists(db, run_id)

    statement = (
        select(Rule)
        .where(Rule.run_id == run_id)
        .order_by(Rule.created_at.asc())
    )

    return list(db.scalars(statement).all())


def get_run_evidence(
    db: Session,
    run_id: UUID,
) -> list[Evidence]:
    statement = (
        select(Evidence)
        .join(Document, Evidence.document_id == Document.id)
        .where(Document.run_id == run_id)
        .order_by(Evidence.created_at.asc())
    )

    return list(db.scalars(statement).all())


def ensure_run_exists(
    db: Session,
    run_id: UUID,
) -> None:
    _ensure_run_exists(db, run_id)