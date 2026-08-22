from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.finding import Finding
from backend.app.schemas.finding import FindingResponse
from backend.app.services.finding_service import (
    generate_findings,
    list_findings,
    resolve_finding,
)


router = APIRouter(
    prefix="/runs/{run_id}/findings",
    tags=["findings"],
)


@router.post(
    "",
    response_model=list[FindingResponse],
)
def generate_run_findings(
    run_id: UUID,
    db: Session = Depends(get_db),
) -> list[FindingResponse]:
    return generate_findings(db, run_id)


@router.get(
    "",
    response_model=list[FindingResponse],
)
def get_run_findings(
    run_id: UUID,
    db: Session = Depends(get_db),
) -> list[FindingResponse]:
    return list_findings(db, run_id)


@router.post(
    "/{finding_id}/resolve",
    response_model=FindingResponse,
)
def resolve_run_finding(
    run_id: UUID,
    finding_id: UUID,
    db: Session = Depends(get_db),
) -> FindingResponse:
    finding = db.get(Finding, finding_id)

    if finding is None or finding.run_id != run_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )

    return resolve_finding(db, finding)