from pathlib import Path

import pytest

from backend.app.agents.extraction import run_extraction
from backend.app.services.extraction import (
    DocumentExtractionError,
    extract_text,
)


def test_extract_text_from_plain_text(tmp_path: Path) -> None:
    document = tmp_path / "sample.txt"
    document.write_text(
        "SuperDocs document extraction test.",
        encoding="utf-8",
    )

    result = extract_text(
        file_path=str(document),
        mime_type="text/plain",
    )

    assert result == "SuperDocs document extraction test."


def test_agent_runs_extraction(tmp_path: Path) -> None:
    document = tmp_path / "sample.txt"
    document.write_text(
        "Extract this document.",
        encoding="utf-8",
    )

    result = run_extraction(
        file_path=str(document),
        mime_type="text/plain",
    )

    assert result == "Extract this document."


def test_missing_document_raises_error(tmp_path: Path) -> None:
    document = tmp_path / "missing.txt"

    with pytest.raises(DocumentExtractionError):
        extract_text(
            file_path=str(document),
            mime_type="text/plain",
        )


def test_unsupported_document_type_raises_error(tmp_path: Path) -> None:
    document = tmp_path / "sample.pdf"
    document.write_bytes(b"not a real pdf")

    with pytest.raises(DocumentExtractionError):
        extract_text(
            file_path=str(document),
            mime_type="application/pdf",
        )