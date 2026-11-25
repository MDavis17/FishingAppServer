"""add is_catch_pb to catches

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-11-24 12:00:00.000000

"""
from collections import defaultdict
from typing import Optional, Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "j0k1l2m3n4o5"
down_revision: Union[str, Sequence[str], None] = "i9j0k1l2m3n4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _known_species_names(connection) -> set[str]:
    rows = connection.execute(sa.text("SELECT name FROM species")).fetchall()
    return {row[0] for row in rows}


def _backfill_historical_pb_flags(connection) -> None:
    known = _known_species_names(connection)
    catches = connection.execute(
        sa.text(
            """
            SELECT id, user_id, species, length, date_time
            FROM catches
            ORDER BY user_id, species, date_time, id
            """
        )
    ).fetchall()

    by_user_species: dict[tuple[int, str], list] = defaultdict(list)
    for row in catches:
        by_user_species[(row.user_id, row.species)].append(row)

    updates: list[tuple[int, bool]] = []
    for (user_id, species), rows in by_user_species.items():
        max_length: Optional[float] = None
        for catch_row in rows:
            is_pb = False
            if (
                species in known
                and catch_row.length is not None
                and (max_length is None or catch_row.length > max_length)
            ):
                is_pb = True
                max_length = catch_row.length
            updates.append((catch_row.id, is_pb))

    if not updates:
        return

    for catch_id, is_pb in updates:
        connection.execute(
            sa.text("UPDATE catches SET is_catch_pb = :is_pb WHERE id = :id"),
            {"is_pb": is_pb, "id": catch_id},
        )


def upgrade() -> None:
    op.add_column(
        "catches",
        sa.Column(
            "is_catch_pb",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    connection = op.get_bind()
    _backfill_historical_pb_flags(connection)
    op.alter_column("catches", "is_catch_pb", server_default=None)


def downgrade() -> None:
    op.drop_column("catches", "is_catch_pb")