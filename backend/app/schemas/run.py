import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict

from backend.app.models.run import ProcessingStage, RunStatus


class RunCreateResponse(BaseModel):
    id: uuid.UUID
    status: RunStatus
    current_stage: ProcessingStage

    model_config = ConfigDict(from_attributes=True)


class RunResponse(BaseModel):
    id: uuid.UUID
    status: RunStatus
    current_stage: ProcessingStage
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)