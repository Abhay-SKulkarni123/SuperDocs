from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConflictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    title: str
    description: str
    severity: str
    status: str
    created_at: datetime
