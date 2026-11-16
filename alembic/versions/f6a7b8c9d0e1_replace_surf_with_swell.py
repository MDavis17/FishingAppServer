"""replace surf_height_ft with swell on observed_conditions

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("observed_conditions") as batch_op:
        batch_op.drop_column("surf_height_ft")
        batch_op.add_column(sa.Column("swell_height_ft", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("swell_period_s", sa.Float(), nullable=True))
        batch_op.add_column(
            sa.Column("swell_direction_deg", sa.Float(), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "swell_captured",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("observed_conditions") as batch_op:
        batch_op.drop_column("swell_captured")
        batch_op.drop_column("swell_direction_deg")
        batch_op.drop_column("swell_period_s")
        batch_op.drop_column("swell_height_ft")
        batch_op.add_column(sa.Column("surf_height_ft", sa.Float(), nullable=True))