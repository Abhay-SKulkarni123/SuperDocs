from backend.app.services.extraction import extract_text


def run_extraction(file_path: str, mime_type: str) -> str:
    return extract_text(
        file_path=file_path,
        mime_type=mime_type,
    )