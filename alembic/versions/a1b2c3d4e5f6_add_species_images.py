"""add species images gallery column

Revision ID: a1b2c3d4e5f6
Revises: 6082aaa21ba0
Create Date: 2026-11-02 22:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "6082aaa21ba0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("species", sa.Column("images", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("species", "images")
