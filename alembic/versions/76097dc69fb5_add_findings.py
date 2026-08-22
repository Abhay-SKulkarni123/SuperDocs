"""add findings

Revision ID: 76097dc69fb5
Revises: ce26006397af
Create Date: 2026-08-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "76097dc69fb5"
down_revision: Union[str, None] = "ce26006397af"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    finding_type = postgresql.ENUM(
        "conflict",
        "rule_failure",
        name="finding_type",
        create_type=False,
    )

    finding_status = postgresql.ENUM(
        "open",
        "resolved",
        name="finding_status",
        create_type=False,
    )

    finding_type.create(
        op.get_bind(),
        checkfirst=True,
    )

    finding_status.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.create_table(
        "findings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "type",
            finding_type,
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "status",
            finding_status,
            nullable=False,
        ),
        sa.Column(
            "source_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_findings_run_id",
        "findings",
        ["run_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_findings_run_id",
        table_name="findings",
    )

    op.drop_table("findings")

    finding_status = postgresql.ENUM(
        "open",
        "resolved",
        name="finding_status",
    )

    finding_type = postgresql.ENUM(
        "conflict",
        "rule_failure",
        name="finding_type",
    )

    finding_status.drop(
        op.get_bind(),
        checkfirst=True,
    )

    finding_type.drop(
        op.get_bind(),
        checkfirst=True,
    )