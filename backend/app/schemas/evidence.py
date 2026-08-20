import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    claim: str
    excerpt: str
    start_offset: int | None
    end_offset: int | None
    created_at: datetime
