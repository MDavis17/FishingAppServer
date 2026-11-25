import logging
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from app.models.db_models import CatchEntry
from app.models.db_models import PersonalBest as PersonalBestRow
from app.models.db_models import Species as SpeciesRow

logger = logging.getLogger(__name__)


def species_id_for_name(db: Session, species_name: str) -> Optional[int]:
    row = db.query(SpeciesRow.id).filter(SpeciesRow.name == species_name).first()
    return row[0] if row else None


def get_personal_best_row(
    db: Session, user_id: int, species_id: int
) -> Optional[PersonalBestRow]:
    return (
        db.query(PersonalBestRow)
        .filter(
            PersonalBestRow.user_id == user_id,
            PersonalBestRow.species_id == species_id,
        )
        .first()
    )


def get_personal_best_by_catch_ids(
    db: Session, user_id: int, catch_ids: List[int]
) -> Set[int]:
    if not catch_ids:
        return set()
    rows = (
        db.query(PersonalBestRow.catch_id)
        .filter(
            PersonalBestRow.user_id == user_id,
            PersonalBestRow.catch_id.in_(catch_ids),
        )
        .all()
    )
    return {row[0] for row in rows}


def pb_catch_ids_for_species_names(
    db: Session, user_id: int, species_names: List[str]
) -> Dict[str, int]:
    if not species_names:
        return {}
    rows = (
        db.query(SpeciesRow.name, PersonalBestRow.catch_id)
        .join(PersonalBestRow, PersonalBestRow.species_id == SpeciesRow.id)
        .filter(
            PersonalBestRow.user_id == user_id,
            SpeciesRow.name.in_(species_names),
        )
        .all()
    )
    return {name: catch_id for name, catch_id in rows}


def _longest_catch_for_species(
    db: Session, user_id: int, species_name: str
) -> Optional[CatchEntry]:
    return (
        db.query(CatchEntry)
        .filter(
            CatchEntry.user_id == user_id,
            CatchEntry.species == species_name,
            CatchEntry.length.isnot(None),
        )
        .order_by(CatchEntry.length.desc(), CatchEntry.date_time.desc())
        .first()
    )


def _upsert_from_catch(
    db: Session,
    user_id: int,
    species_id: int,
    catch: CatchEntry,
) -> None:
    existing = get_personal_best_row(db, user_id, species_id)
    if existing is not None:
        existing.catch_id = catch.id
        existing.location_lat = catch.location_lat
        existing.location_lng = catch.location_lng
        existing.length = catch.length
        existing.weight = catch.weight
        existing.bait = catch.bait
        existing.caught_at = catch.date_time
    else:
        db.add(
            PersonalBestRow(
                user_id=user_id,
                species_id=species_id,
                catch_id=catch.id,
                location_lat=catch.location_lat,
                location_lng=catch.location_lng,
                length=catch.length,
                weight=catch.weight,
                bait=catch.bait,
                caught_at=catch.date_time,
            )
        )


def record_catch_for_personal_best(
    db: Session, catch_row: CatchEntry
) -> None:
    if catch_row.length is None:
        return
    if catch_row.id is None:
        return

    species_id = species_id_for_name(db, catch_row.species)
    if species_id is None:
        return

    existing = get_personal_best_row(db, catch_row.user_id, species_id)
    if existing is not None:
        if catch_row.length <= existing.length:
            return
        _upsert_from_catch(db, catch_row.user_id, species_id, catch_row)
        db.commit()
        return

    longest = _longest_catch_for_species(db, catch_row.user_id, catch_row.species)
    if longest is None or longest.id != catch_row.id:
        return

    _upsert_from_catch(db, catch_row.user_id, species_id, catch_row)
    db.commit()


def recompute_personal_best_for_user_species(
    db: Session, user_id: int, species_id: int, species_name: str
) -> None:
    existing = get_personal_best_row(db, user_id, species_id)
    longest = _longest_catch_for_species(db, user_id, species_name)

    if longest is None:
        if existing is not None:
            db.delete(existing)
            db.commit()
        return

    _upsert_from_catch(db, user_id, species_id, longest)
    db.commit()


def recompute_historical_catch_pb_flags_for_user_species(
    db: Session, user_id: int, species_name: str
) -> None:
    known_species = species_id_for_name(db, species_name) is not None

    rows = (
        db.query(CatchEntry)
        .filter(
            CatchEntry.user_id == user_id,
            CatchEntry.species == species_name,
        )
        .order_by(CatchEntry.date_time.asc(), CatchEntry.id.asc())
        .all()
    )

    for row in rows:
        row.is_catch_pb = False

    if known_species:
        max_length_so_far: Optional[float] = None
        for row in rows:
            if row.length is None:
                continue
            if max_length_so_far is None or row.length > max_length_so_far:
                row.is_catch_pb = True
                max_length_so_far = row.length

    db.commit()


def species_pairs_for_deleted_pb_catches(
    db: Session, user_id: int, catch_ids: List[int]
) -> List[Tuple[int, str]]:
    if not catch_ids:
        return []
    rows = (
        db.query(PersonalBestRow.species_id, SpeciesRow.name)
        .join(SpeciesRow, SpeciesRow.id == PersonalBestRow.species_id)
        .filter(
            PersonalBestRow.user_id == user_id,
            PersonalBestRow.catch_id.in_(catch_ids),
        )
        .all()
    )
    return [(species_id, name) for species_id, name in rows]