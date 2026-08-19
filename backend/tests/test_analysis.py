import pytest

from backend.app.services.analysis import AnalysisError, analyze_text


def test_analyze_text_returns_basic_document_statistics() -> None:
    result = analyze_text(
        "SuperDocs processes documents. "
        "The system extracts useful information."
    )

    assert result["summary"] == "SuperDocs processes documents"
    assert result["word_count"] == 8
    assert result["sentence_count"] == 2
    assert result["character_count"] == 70


def test_analyze_text_handles_multiple_sentence_delimiters() -> None:
    result = analyze_text(
        "First document sentence! "
        "Second document sentence? "
        "Third document sentence."
    )

    assert result["summary"] == "First document sentence"
    assert result["sentence_count"] == 3
    assert result["word_count"] == 9


def test_analyze_text_strips_surrounding_whitespace() -> None:
    result = analyze_text(
        "  SuperDocs processes documents.  "
    )

    assert result["summary"] == "SuperDocs processes documents"
    assert result["word_count"] == 3
    assert result["sentence_count"] == 1
    assert result["character_count"] == 30


def test_analyze_text_rejects_empty_text() -> None:
    with pytest.raises(AnalysisError, match="Document text is empty"):
        analyze_text("   ")