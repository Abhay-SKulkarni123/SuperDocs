"""add run observability metrics

Revision ID: e01bd4c9c1ee
Revises: 76097dc69fb5
Create Date: 2026-08-22 18:40:28.526925
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e01bd4c9c1ee"
down_revision: Union[str, None] = "76097dc69fb5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep rules and findings tables.
    # This migration only adds observability fields to runs.

    op.add_column(
        "runs",
        sa.Column("stage_timings_json", sa.JSON(), nullable=True),
    )
    op.add_column(
        "runs",
        sa.Column("total_duration_ms", sa.Float(), nullable=True),
    )
    op.add_column(
        "runs",
        sa.Column("model_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "runs",
        sa.Column("input_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "runs",
        sa.Column("output_tokens", sa.Integer(), nullable=True),
    )
    op.add_column(
        "runs",
        sa.Column("estimated_cost", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("runs", "estimated_cost")
    op.drop_column("runs", "output_tokens")
    op.drop_column("runs", "input_tokens")
    op.drop_column("runs", "model_name")
    op.drop_column("runs", "total_duration_ms")
    op.drop_column("runs", "stage_timings_json")