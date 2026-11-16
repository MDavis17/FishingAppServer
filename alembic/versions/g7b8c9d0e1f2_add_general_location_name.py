"""add general_location_name to trips and catches

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-11-16 12:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "trips",
        sa.Column("general_location_name", sa.String(), nullable=True),
    )
    op.add_column(
        "catches",
        sa.Column("general_location_name", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("catches", "general_location_name")
    op.drop_column("trips", "general_location_name")