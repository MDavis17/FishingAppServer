"""add fishing tables

Revision ID: 6082aaa21ba0
Revises: 4f076147ee78
Create Date: 2026-10-19 02:09:01.753777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6082aaa21ba0"
down_revision: Union[str, Sequence[str], None] = "4f076147ee78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "regions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_regions_id"), "regions", ["id"], unique=False)
    op.create_index(op.f("ix_regions_name"), "regions", ["name"], unique=True)

    op.create_table(
        "species",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("scientific_name", sa.String(), nullable=True),
        sa.Column("avg_length", sa.String(), nullable=True),
        sa.Column("length_units", sa.String(), nullable=True),
        sa.Column("lifespan", sa.String(), nullable=True),
        sa.Column("depth_range", sa.String(), nullable=True),
        sa.Column("image", sa.String(), nullable=False),
        sa.Column("kingdom", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_species_id"), "species", ["id"], unique=False)
    op.create_index(op.f("ix_species_kingdom"), "species", ["kingdom"], unique=False)
    op.create_index(op.f("ix_species_name"), "species", ["name"], unique=False)

    op.create_table(
        "species_regions",
        sa.Column("species_id", sa.Integer(), nullable=False),
        sa.Column("region_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["species_id"], ["species.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("species_id", "region_id"),
    )

    op.create_table(
        "trips",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("location_name", sa.String(), nullable=False),
        sa.Column("location_lat", sa.Float(), nullable=False),
        sa.Column("location_lng", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trips_id"), "trips", ["id"], unique=False)
    op.create_index(op.f("ix_trips_user_id"), "trips", ["user_id"], unique=False)

    op.create_table(
        "catches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trip_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date_time", sa.DateTime(), nullable=False),
        sa.Column("species", sa.String(), nullable=False),
        sa.Column("water_type", sa.String(), nullable=False),
        sa.Column("bait", sa.String(), nullable=True),
        sa.Column("location_name", sa.String(), nullable=True),
        sa.Column("location_lat", sa.Float(), nullable=True),
        sa.Column("location_lng", sa.Float(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("length", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_catches_id"), "catches", ["id"], unique=False)
    op.create_index(op.f("ix_catches_trip_id"), "catches", ["trip_id"], unique=False)
    op.create_index(op.f("ix_catches_user_id"), "catches", ["user_id"], unique=False)

    op.create_table(
        "trip_target_species",
        sa.Column("trip_id", sa.Integer(), nullable=False),
        sa.Column("species_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["species_id"], ["species.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("trip_id", "species_id"),
    )

    op.create_table(
        "user_favorites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("species_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["species_id"], ["species.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "species_id", name="unique_user_species"),
    )
    op.create_index(op.f("ix_user_favorites_id"), "user_favorites", ["id"], unique=False)
    op.create_index(
        op.f("ix_user_favorites_species_id"), "user_favorites", ["species_id"], unique=False
    )
    op.create_index(
        op.f("ix_user_favorites_user_id"), "user_favorites", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_favorites_user_id"), table_name="user_favorites")
    op.drop_index(op.f("ix_user_favorites_species_id"), table_name="user_favorites")
    op.drop_index(op.f("ix_user_favorites_id"), table_name="user_favorites")
    op.drop_table("user_favorites")

    op.drop_table("trip_target_species")

    op.drop_index(op.f("ix_catches_user_id"), table_name="catches")
    op.drop_index(op.f("ix_catches_trip_id"), table_name="catches")
    op.drop_index(op.f("ix_catches_id"), table_name="catches")
    op.drop_table("catches")

    op.drop_index(op.f("ix_trips_user_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_id"), table_name="trips")
    op.drop_table("trips")

    op.drop_table("species_regions")

    op.drop_index(op.f("ix_species_name"), table_name="species")
    op.drop_index(op.f("ix_species_kingdom"), table_name="species")
    op.drop_index(op.f("ix_species_id"), table_name="species")
    op.drop_table("species")

    op.drop_index(op.f("ix_regions_name"), table_name="regions")
    op.drop_index(op.f("ix_regions_id"), table_name="regions")
    op.drop_table("regions")
