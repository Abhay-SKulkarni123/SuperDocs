from dataclasses import dataclass

from backend.app.services.analysis import analyze_text


@dataclass(frozen=True)
class AnalysisResult:
    summary: str
    word_count: int
    character_count: int
    sentence_count: int


class AnalyzerAgent:
    """
    Deterministic analysis agent used as the first analysis-stage
    implementation.

    The interface is intentionally isolated so an LLM-backed
    implementation can be introduced later without changing the
    processing pipeline.
    """

    def analyze(self, text: str) -> AnalysisResult:
        result = analyze_text(text)

        return AnalysisResult(
            summary=result["summary"],
            word_count=result["word_count"],
            character_count=result["character_count"],
            sentence_count=result["sentence_count"],
        )


def run_analysis(text: str) -> AnalysisResult:
    agent = AnalyzerAgent()
    return agent.analyze(text)