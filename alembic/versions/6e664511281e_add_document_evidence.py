"""add document evidence

Revision ID: 6e664511281e
Revises: xxxxxxxxxxxx
Create Date: 2026-08-20 14:43:18.246619

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6e664511281e'
down_revision: Union[str, None] = 'xxxxxxxxxxxx'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass