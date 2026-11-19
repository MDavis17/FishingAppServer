"""add saved_locations and trips.location_id

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-11-20 15:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

TRIP_TYPE_ENUM = postgresql.ENUM(
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
    create_type=False,
)

revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, Sequence[str], None] = "h8i9j0k1l2m3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "saved_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("location_lat", sa.Float(), nullable=False),
        sa.Column("location_lng", sa.Float(), nullable=False),
        sa.Column("location_name", sa.String(), nullable=False),
        sa.Column("general_location_name", sa.String(), nullable=True),
        sa.Column(
            "did_catch_fish_here",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("notes", sa.String(length=800), nullable=True),
        sa.Column("trip_type", TRIP_TYPE_ENUM, nullable=True),
        sa.Column("last_fished_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_saved_locations_id"),
        "saved_locations",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_saved_locations_user_id"),
        "saved_locations",
        ["user_id"],
        unique=False,
    )
    op.alter_column("saved_locations", "did_catch_fish_here", server_default=None)

    op.add_column("trips", sa.Column("location_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_trips_location_id_saved_locations",
        "trips",
        "saved_locations",
        ["location_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_trips_location_id"),
        "trips",
        ["location_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_trips_location_id"), table_name="trips")
    op.drop_constraint(
        "fk_trips_location_id_saved_locations",
        "trips",
        type_="foreignkey",
    )
    op.drop_column("trips", "location_id")

    op.drop_index(op.f("ix_saved_locations_user_id"), table_name="saved_locations")
    op.drop_index(op.f("ix_saved_locations_id"), table_name="saved_locations")
    op.drop_table("saved_locations")