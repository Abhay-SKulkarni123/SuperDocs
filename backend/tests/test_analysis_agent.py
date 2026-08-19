from backend.app.agents.analyzer import AnalysisResult, AnalyzerAgent, run_analysis


def test_analyzer_agent_returns_structured_result() -> None:
    result = run_analysis(
        "SuperDocs processes documents. "
        "The system extracts useful information."
    )

    assert isinstance(result, AnalysisResult)
    assert result.summary == "SuperDocs processes documents"
    assert result.word_count == 8
    assert result.character_count == 70
    assert result.sentence_count == 2


def test_analyzer_agent_can_be_instantiated() -> None:
    agent = AnalyzerAgent()

    result = agent.analyze("SuperDocs analyzes documents.")

    assert isinstance(result, AnalysisResult)
    assert result.summary == "SuperDocs analyzes documents"
    assert result.word_count == 3
    assert result.character_count == 29
    assert result.sentence_count == 1


def test_analyzer_agent_rejects_empty_text() -> None:
    agent = AnalyzerAgent()

    try:
        agent.analyze("")
        assert False, "Expected empty text to raise an error"
    except Exception as exc:
        assert str(exc) == "Document text is empty"