import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingStage(str, enum.Enum):
    INGEST = "ingest"
    EXTRACT = "extract"
    ANALYZE = "analyze"
    REVIEW = "review"
    COMMIT = "commit"
    COMPLETE = "complete"


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, name="run_status"),
        default=RunStatus.PENDING,
        nullable=False,
    )

    current_stage: Mapped[ProcessingStage] = mapped_column(
        Enum(ProcessingStage, name="processing_stage"),
        default=ProcessingStage.INGEST,
        nullable=False,
    )

    review_status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="review_status"),
        default=ReviewStatus.PENDING,
        nullable=False,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="run",
        cascade="all, delete-orphan",
    )

    # Phase 21: cost and timing observability

    stage_timings_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    total_duration_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    input_tokens: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    output_tokens: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    estimated_cost: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )