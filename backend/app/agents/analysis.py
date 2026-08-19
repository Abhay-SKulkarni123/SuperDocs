from backend.app.services.analysis import analyze_text


def run_analysis(text: str) -> dict:
    return analyze_text(text)