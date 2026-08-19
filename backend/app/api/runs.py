import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.schemas.run import RunResponse
from backend.app.services.run_service import create_run, get_run

router = APIRouter(
    prefix="/runs",
    tags=["runs"],
)


@router.post(
    "",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_run(
    db: Session = Depends(get_db),
) -> RunResponse:
    return create_run(db)


@router.get(
    "/{run_id}",
    response_model=RunResponse,
)
def get_existing_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> RunResponse:
    run = get_run(db, run_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    return run