from pydantic import BaseModel, Field


class ExtractionResponse(BaseModel):
    document_id: str
    filename: str
    character_count: int = Field(ge=0)
    text: str