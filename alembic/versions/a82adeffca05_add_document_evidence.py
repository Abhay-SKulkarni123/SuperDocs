"""add document evidence

Revision ID: xxxxxxxxxxxx
Revises: 2f8458770b3d
Create Date: 2026-08-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "xxxxxxxxxxxx"
down_revision: Union[str, Sequence[str], None] = "2f8458770b3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evidence",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "claim",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "excerpt",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "start_offset",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "end_offset",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_evidence_document_id",
        "evidence",
        ["document_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_evidence_document_id",
        table_name="evidence",
    )

    op.drop_table("evidence")