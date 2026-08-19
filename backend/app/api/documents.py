import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.document import DocumentResponse
from backend.app.services.document_service import (
    ALLOWED_MIME_TYPES,
    create_document,
)
from backend.app.services.run_service import get_run


router = APIRouter(
    prefix="/runs/{run_id}/documents",
    tags=["documents"],
)


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    run_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    run = get_run(db, run_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported document type",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is empty",
        )

    return create_document(
        db=db,
        run=run,
        filename=file.filename or "document",
        mime_type=file.content_type or "application/octet-stream",
        content=content,
    )