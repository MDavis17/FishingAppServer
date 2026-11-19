"""add species_groups table and species.group_id

Revision ID: h8i9j0k1l2m3
Revises: g7b8c9d0e1f2
Create Date: 2026-11-20 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "h8i9j0k1l2m3"
down_revision: Union[str, Sequence[str], None] = "g7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "species_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_species_groups_id"), "species_groups", ["id"], unique=False)
    op.create_index(op.f("ix_species_groups_name"), "species_groups", ["name"], unique=True)

    op.add_column(
        "species",
        sa.Column("group_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_species_group_id_species_groups",
        "species",
        "species_groups",
        ["group_id"],
        ["id"],
    )
    op.create_index(op.f("ix_species_group_id"), "species", ["group_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_species_group_id"), table_name="species")
    op.drop_constraint("fk_species_group_id_species_groups", "species", type_="foreignkey")
    op.drop_column("species", "group_id")
    op.drop_index(op.f("ix_species_groups_name"), table_name="species_groups")
    op.drop_index(op.f("ix_species_groups_id"), table_name="species_groups")
    op.drop_table("species_groups")