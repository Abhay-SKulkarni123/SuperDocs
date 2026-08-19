from backend.app.agents.analyzer import run_analysis


def test_analysis_agent_integrates_with_extracted_text() -> None:
    extracted_text = (
        "SuperDocs processes documents. "
        "The system extracts useful information."
    )

    result = run_analysis(extracted_text)

    assert result.summary == "SuperDocs processes documents"
    assert result.word_count == 8
    assert result.character_count == 70
    assert result.sentence_count == 2