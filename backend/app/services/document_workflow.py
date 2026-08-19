from sqlalchemy.orm import Session

from backend.app.agents.workflow import document_workflow
from backend.app.models.document import Document


class DocumentWorkflowError(Exception):
    pass


def process_document(
    db: Session,
    document: Document,
) -> Document:
    if not document.extracted_text:
        raise DocumentWorkflowError("Document has no extracted text")

    result = document_workflow.invoke(
        {
            "run_id": str(document.run_id),
            "document_id": str(document.id),
            "text": document.extracted_text,
            "status": "pending",
        }
    )

    document.summary = result.get("summary")
    document.word_count = result.get("word_count")
    document.character_count = result.get("character_count")
    document.sentence_count = result.get("sentence_count")

    db.add(document)
    db.commit()
    db.refresh(document)

    return document