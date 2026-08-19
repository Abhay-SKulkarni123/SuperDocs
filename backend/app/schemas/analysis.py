from pydantic import BaseModel, Field


class AnalysisResponse(BaseModel):
    summary: str
    word_count: int = Field(ge=0)
    character_count: int = Field(ge=0)
    sentence_count: int = Field(ge=0)