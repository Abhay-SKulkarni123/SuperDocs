import uuid

from backend.app.agents.workflow import document_workflow


def test_document_workflow_analyzes_document() -> None:
    result = document_workflow.invoke(
        {
            "run_id": str(uuid.uuid4()),
            "document_id": str(uuid.uuid4()),
            "text": (
                "SuperDocs processes documents. "
                "The system extracts useful information."
            ),
            "status": "pending",
        }
    )

    assert result["status"] == "analyzed"
    assert result["summary"] == "SuperDocs processes documents"
    assert result["word_count"] == 8
    assert result["sentence_count"] == 2
    assert result["character_count"] == 70