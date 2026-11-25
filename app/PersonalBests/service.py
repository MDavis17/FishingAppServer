import logging
from typing import List, Tuple

from sqlalchemy.orm import Session

import app.PersonalBests.data_provider as data_provider

logger = logging.getLogger(__name__)


def record_catch_for_personal_best(db: Session, catch_row) -> None:
    try:
        data_provider.record_catch_for_personal_best(db, catch_row)
    except Exception:
        logger.exception("Failed to update personal best after catch create")
        try:
            db.rollback()
        except Exception:
            pass


def recompute_after_catch_deletes(
    db: Session,
    user_id: int,
    deleted_catch_ids: List[int],
    species_to_recompute: List[Tuple[int, str]],
) -> None:
    if not species_to_recompute:
        return
    seen: set[int] = set()
    for species_id, species_name in species_to_recompute:
        if species_id in seen:
            continue
        seen.add(species_id)
        try:
            data_provider.recompute_personal_best_for_user_species(
                db, user_id, species_id, species_name
            )
        except Exception:
            logger.exception(
                "Failed to recompute personal best for user=%s species=%s after deletes %s",
                user_id,
                species_id,
                deleted_catch_ids,
            )
            try:
                db.rollback()
            except Exception:
                pass


def species_pairs_for_deleted_pb_catches(
    db: Session, user_id: int, catch_ids: List[int]
) -> List[Tuple[int, str]]:
    return data_provider.species_pairs_for_deleted_pb_catches(
        db, user_id, catch_ids
    )


def recompute_historical_pb_flags_for_species(
    db: Session, user_id: int, species_name: str
) -> None:
    try:
        data_provider.recompute_historical_catch_pb_flags_for_user_species(
            db, user_id, species_name
        )
    except Exception:
        logger.exception(
            "Failed to recompute historical PB flags for user=%s species=%s",
            user_id,
            species_name,
        )
        try:
            db.rollback()
        except Exception:
            pass


def recompute_historical_pb_flags_for_species_list(
    db: Session, user_id: int, species_names: List[str]
) -> None:
    seen: set[str] = set()
    for name in species_names:
        if not name or name in seen:
            continue
        seen.add(name)
        recompute_historical_pb_flags_for_species(db, user_id, name)