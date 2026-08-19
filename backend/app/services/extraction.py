from pathlib import Path


class DocumentExtractionError(Exception):
    pass


def extract_text(file_path: str, mime_type: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise DocumentExtractionError("Document file does not exist")

    if mime_type == "text/plain":
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentExtractionError(
                "Unable to decode text document as UTF-8"
            ) from exc

    raise DocumentExtractionError(
        f"Unsupported document type: {mime_type}"
    )