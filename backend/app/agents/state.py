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

class EvidenceItem(TypedDict):
    claim: str
    excerpt: str
    start_offset: int
    end_offset: int


class DocumentState(TypedDict, total=False):
    run_id: str
    document_id: str
    text: str
    summary: str
    word_count: int
    character_count: int
    sentence_count: int
    evidence: list[EvidenceItem]
    status: str
    error: str | None