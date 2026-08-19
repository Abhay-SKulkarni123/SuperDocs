from typing import TypedDict


class DocumentState(TypedDict, total=False):
    run_id: str
    document_id: str
    text: str
    summary: str
    word_count: int
    character_count: int
    sentence_count: int
    status: str
    error: str | None