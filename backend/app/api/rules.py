from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.rule import (
    RuleCreate,
    RuleEvaluationResponse,
    RuleResponse,
)
from backend.app.services.rule_evaluation import evaluate_run_rules
from backend.app.services.rule_service import (
    create_rule,
    list_rules,
)


router = APIRouter(
    prefix="/runs/{run_id}/rules",
    tags=["rules"],
)


@router.post(
    "",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_run_rule(
    run_id: UUID,
    payload: RuleCreate,
    db: Session = Depends(get_db),
) -> RuleResponse:
    return create_rule(
        db,
        run_id,
        name=payload.name,
        description=payload.description,
        requirement=payload.requirement,
        severity=payload.severity,
    )


@router.get(
    "",
    response_model=list[RuleResponse],
)
def get_run_rules(
    run_id: UUID,
    db: Session = Depends(get_db),
) -> list[RuleResponse]:
    return list_rules(db, run_id)


@router.post(
    "/evaluate",
    response_model=list[RuleEvaluationResponse],
)
def evaluate_rules_for_run(
    run_id: UUID,
    db: Session = Depends(get_db),
) -> list[RuleEvaluationResponse]:
    return evaluate_run_rules(db, run_id)