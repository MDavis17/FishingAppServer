from calendar import month_abbr
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import Session, joinedload

import app.PersonalBests.data_provider as personal_best_data
from app.Auth.models import UserFavorite
from app.models.db_models import CatchEntry
from app.models.db_models import Species as SpeciesRow

_MONTH_LABELS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def _monthly_catch_counts(catch_rows: List[CatchEntry]) -> List[Dict[str, Any]]:
    totals = [0] * 12
    for row in catch_rows:
        totals[row.date_time.month - 1] += 1
    return [
        {"month": index + 1, "label": _MONTH_LABELS[index], "count": totals[index]}
        for index in range(12)
    ]


def _normalize_species_images(raw: Any) -> Optional[List[Dict[str, str]]]:
    if not raw or not isinstance(raw, list):
        return None
    images: List[Dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        label = item.get("label")
        if url and label:
            images.append({"url": str(url), "label": str(label)})
    return images if images else None


def _species_row_to_dict(species: SpeciesRow, favorite_ids: Set[int]) -> Dict[str, Any]:
    return {
        "id": species.id,
        "name": species.name,
        "scientificName": species.scientific_name or "",
        "avgLength": species.avg_length or "",
        "lengthUnits": species.length_units,
        "lifespan": species.lifespan or "",
        "depthRange": species.depth_range or "",
        "region": [r.name for r in species.regions],
        "image": species.image,
        "images": _normalize_species_images(species.images),
        "isFavorite": species.id in favorite_ids,
        "kingdom": species.kingdom,
    }


def get_species_catch_history(
    db: Session, species_id: int, user_id: int
) -> Optional[Dict[str, Any]]:
    species = get_species_by_id(db, species_id)
    if species is None:
        return None

    species_name = species["name"]
    base_filter = (
        CatchEntry.user_id == user_id,
        CatchEntry.species == species_name,
    )

    catch_rows = (
        db.query(CatchEntry)
        .filter(*base_filter)
        .order_by(CatchEntry.date_time.desc())
        .all()
    )

    total_catches = len(catch_rows)

    def _catch_item(row: CatchEntry) -> Dict[str, Any]:
        return {
            "id": row.id,
            "dateTime": row.date_time,
            "length": row.length,
            "weight": row.weight,
        }

    catches = [_catch_item(row) for row in catch_rows]

    personal_best: Optional[Dict[str, Any]] = None
    pb_row = personal_best_data.get_personal_best_row(db, user_id, species_id)
    if pb_row is not None:
        personal_best = {
            "id": pb_row.catch_id,
            "dateTime": pb_row.caught_at,
            "length": pb_row.length,
            "weight": pb_row.weight,
        }

    most_recent_catch = _catch_item(catch_rows[0]) if catch_rows else None

    counts_by_month = [0] * 12
    for row in catch_rows:
        if row.date_time is not None:
            counts_by_month[row.date_time.month - 1] += 1

    monthly_counts = [
        {
            "month": m,
            "label": month_abbr[m],
            "count": counts_by_month[m - 1],
        }
        for m in range(1, 13)
    ]

    return {
        "totalCatches": total_catches,
        "personalBest": personal_best,
        "mostRecentCatch": most_recent_catch,
        "catches": catches,
        "monthlyCounts": _monthly_catch_counts(catch_rows),
    }


def get_species_by_id(db: Session, species_id: int, user_id: Optional[int] = None):
    row = (
        db.query(SpeciesRow)
        .options(joinedload(SpeciesRow.regions))
        .filter(SpeciesRow.id == species_id)
        .first()
    )
    if row is None:
        return None
    favorite_ids: Set[int] = set()
    if user_id is not None:
        favorite_ids = get_user_favorite_species_ids(db, user_id)
    return _species_row_to_dict(row, favorite_ids)


def get_user_favorite_species_ids(db: Session, user_id: int) -> Set[int]:
    rows = db.query(UserFavorite.species_id).filter(UserFavorite.user_id == user_id).all()
    return {row[0] for row in rows}


def toggle_user_favorite(db: Session, user_id: int, species_id: int) -> bool:
    existing = (
        db.query(UserFavorite)
        .filter(
            UserFavorite.user_id == user_id,
            UserFavorite.species_id == species_id,
        )
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return False

    db.add(UserFavorite(user_id=user_id, species_id=species_id))
    db.commit()
    return True


def _filter_kingdom(species_list: list, kingdom: Optional[str]) -> list:
    if not kingdom:
        return species_list
    return [s for s in species_list if s.get("kingdom") == kingdom]


def get_species(db: Session, user_id: int, kingdom: Optional[str] = None):
    favorite_ids = get_user_favorite_species_ids(db, user_id)
    rows = (
        db.query(SpeciesRow)
        .options(joinedload(SpeciesRow.regions))
        .order_by(SpeciesRow.name.asc())
        .all()
    )
    non_favorites = [
        _species_row_to_dict(s, favorite_ids)
        for s in rows
        if s.id not in favorite_ids
    ]
    return _filter_kingdom(non_favorites, kingdom)


def get_favorite_species(db: Session, user_id: int, kingdom: Optional[str] = None):
    favorite_ids = get_user_favorite_species_ids(db, user_id)
    if not favorite_ids:
        return []
    rows = (
        db.query(SpeciesRow)
        .options(joinedload(SpeciesRow.regions))
        .filter(SpeciesRow.id.in_(favorite_ids))
        .order_by(SpeciesRow.name.asc())
        .all()
    )
    favorites = [_species_row_to_dict(s, favorite_ids) for s in rows]
    return _filter_kingdom(favorites, kingdom)
