import re


class AnalysisError(Exception):
    pass


def analyze_text(text: str) -> dict:
    if not text or not text.strip():
        raise AnalysisError("Document text is empty")

    normalized_text = text.strip()

    sentences = [
        sentence.strip()
        for sentence in re.split(r"[.!?]+", normalized_text)
        if sentence.strip()
    ]

    words = normalized_text.split()

    return {
        "summary": sentences[0] if sentences else normalized_text,
        "word_count": len(words),
        "character_count": len(normalized_text),
        "sentence_count": len(sentences),
    }