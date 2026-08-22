from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    requirement: str = Field(min_length=1)
    severity: str = "medium"


class RuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    name: str
    description: str | None
    requirement: str
    severity: str
    created_at: datetime


class RuleEvaluationResponse(BaseModel):
    rule_id: UUID
    status: str
    explanation: str
    evidence_ids: list[UUID]