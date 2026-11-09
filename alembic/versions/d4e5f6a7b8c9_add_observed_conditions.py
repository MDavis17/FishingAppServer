"""add observed_conditions table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "observed_conditions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("observed_hour", sa.DateTime(), nullable=False),
        sa.Column("air_temp_f", sa.Float(), nullable=True),
        sa.Column("weather_description", sa.String(), nullable=True),
        sa.Column("water_temp_f", sa.Float(), nullable=True),
        sa.Column("wind_speed_mph", sa.Float(), nullable=True),
        sa.Column("wind_direction_deg", sa.Float(), nullable=True),
        sa.Column("wind_gusts_mph", sa.Float(), nullable=True),
        sa.Column("pressure_inhg", sa.Float(), nullable=True),
        sa.Column("surf_height_ft", sa.Float(), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "latitude",
            "longitude",
            "observed_hour",
            name="uq_observed_conditions_lat_lng_hour",
        ),
    )
    op.create_index(
        op.f("ix_observed_conditions_observed_hour"),
        "observed_conditions",
        ["observed_hour"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_observed_conditions_observed_hour"),
        table_name="observed_conditions",
    )
    op.drop_table("observed_conditions")
