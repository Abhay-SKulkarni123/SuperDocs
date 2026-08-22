import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.document import Document
from backend.app.models.run import Run
from backend.app.services.storage_service import save_document
from backend.app.models.evidence import Evidence

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
}


def create_document(
    db: Session,
    run: Run,
    filename: str,
    mime_type: str,
    content: bytes,
) -> Document:
    storage_reference, checksum = save_document(
        filename=filename,
        content=content,
    )

    extracted_text = None

    if mime_type == "text/plain":
        extracted_text = content.decode("utf-8")

    document = Document(
        id=uuid.uuid4(),
        run_id=run.id,
        filename=filename,
        mime_type=mime_type,
        storage_reference=storage_reference,
        checksum=checksum,
        created_at=datetime.now(timezone.utc),
        metadata_json=json.dumps(
            {
                "size_bytes": len(content),
                "extraction_completed": False,
            }
        ),
        extracted_text=extracted_text,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def get_document(
    db: Session,
    document_id: uuid.UUID,
) -> Document | None:
    statement = select(Document).where(Document.id == document_id)
    return db.scalar(statement)

def get_document_evidence(
    db: Session,
    document_id,
) -> list[Evidence]:
    statement = (
        select(Evidence)
        .where(Evidence.document_id == document_id)
        .order_by(Evidence.created_at.asc())
    )

    return list(db.scalars(statement).all())