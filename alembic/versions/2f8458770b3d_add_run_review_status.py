"""add run review status

Revision ID: 2f8458770b3d
Revises: f2fd22768999
Create Date: 2026-08-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f8458770b3d"
down_revision: Union[str, Sequence[str], None] = "f2fd22768999"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    review_status = sa.Enum(
        "PENDING",
        "APPROVED",
        "REJECTED",
        name="review_status",
    )

    review_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "runs",
        sa.Column(
            "review_status",
            review_status,
            nullable=False,
            server_default="PENDING",
        ),
    )

    op.alter_column(
        "runs",
        "review_status",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("runs", "review_status")

    review_status = sa.Enum(
        "PENDING",
        "APPROVED",
        "REJECTED",
        name="review_status",
    )

    review_status.drop(op.get_bind(), checkfirst=True)