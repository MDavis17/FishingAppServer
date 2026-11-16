"""add personal_bests table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "personal_bests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("species_id", sa.Integer(), nullable=False),
        sa.Column("catch_id", sa.Integer(), nullable=False),
        sa.Column("location_lat", sa.Float(), nullable=True),
        sa.Column("location_lng", sa.Float(), nullable=True),
        sa.Column("length", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("bait", sa.String(), nullable=True),
        sa.Column("caught_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["catch_id"], ["catches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["species_id"], ["species.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("catch_id"),
        sa.UniqueConstraint("user_id", "species_id", name="uq_personal_bests_user_species"),
    )
    op.create_index(
        op.f("ix_personal_bests_user_id"),
        "personal_bests",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_personal_bests_species_id"),
        "personal_bests",
        ["species_id"],
        unique=False,
    )

    # Backfill one PB per (user_id, species_id) from measured catches.
    op.execute(
        sa.text(
            """
            INSERT INTO personal_bests (
                user_id, species_id, catch_id,
                location_lat, location_lng, length, weight, bait, caught_at
            )
            SELECT DISTINCT ON (c.user_id, s.id)
                c.user_id,
                s.id,
                c.id,
                c.location_lat,
                c.location_lng,
                c.length,
                c.weight,
                c.bait,
                c.date_time
            FROM catches c
            INNER JOIN species s ON s.name = c.species
            WHERE c.length IS NOT NULL
            ORDER BY c.user_id, s.id, c.length DESC, c.date_time DESC
            """
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_personal_bests_species_id"), table_name="personal_bests")
    op.drop_index(op.f("ix_personal_bests_user_id"), table_name="personal_bests")
    op.drop_table("personal_bests")