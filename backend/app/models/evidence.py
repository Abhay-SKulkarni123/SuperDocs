from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.models.document import Document

from pydantic import BaseModel, ConfigDict

class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    claim: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    excerpt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    start_offset: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    end_offset: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="evidence",
    )

class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    claim: str
    excerpt: str
    start_offset: int | None
    end_offset: int | None
    created_at: datetime