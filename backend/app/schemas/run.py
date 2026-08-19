import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from backend.app.models.run import ProcessingStage, RunStatus

class RunCreate(BaseModel):
    pass


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: RunStatus
    current_stage: ProcessingStage
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None