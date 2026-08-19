import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    run_id: uuid.UUID
    filename: str
    mime_type: str
    storage_reference: str
    checksum: str
    created_at: datetime
    metadata_json: str | None