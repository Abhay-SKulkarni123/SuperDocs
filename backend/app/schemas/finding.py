from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    type: str
    title: str
    description: str
    severity: str
    status: str
    source_type: str
    source_id: UUID
    created_at: datetime
    resolved_at: datetime | None