import hashlib
from pathlib import Path


STORAGE_ROOT = Path("uploads")


def save_document(
    filename: str,
    content: bytes,
) -> tuple[str, str]:
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

    checksum = hashlib.sha256(content).hexdigest()

    file_path = STORAGE_ROOT / f"{checksum}_{filename}"
    file_path.write_bytes(content)

    return str(file_path), checksum