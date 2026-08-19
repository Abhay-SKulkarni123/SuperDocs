from backend.app.agents.workflow import document_workflow


def test_document_workflow_uses_analysis_agent() -> None:
    result = document_workflow.invoke(
        {
            "run_id": "test-run",
            "document_id": "test-document",
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
    assert result["character_count"] == 70
    assert result["sentence_count"] == 2