"""add trip type enum column

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-11-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TRIP_TYPE_ENUM = sa.Enum(
    "Surf",
    "Kayak",
    "Boat",
    "Spearfishing",
    "Pier",
    "Free Diving",
    "Crabbing",
    "Rock/Jetty",
    "Fly Fishing",
    name="trip_type",
)


def upgrade() -> None:
    TRIP_TYPE_ENUM.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "trips",
        sa.Column(
            "trip_type",
            TRIP_TYPE_ENUM,
            nullable=False,
            server_default="Surf",
        ),
    )
    op.alter_column("trips", "trip_type", server_default=None)


def downgrade() -> None:
    op.drop_column("trips", "trip_type")
    TRIP_TYPE_ENUM.drop(op.get_bind(), checkfirst=True)
