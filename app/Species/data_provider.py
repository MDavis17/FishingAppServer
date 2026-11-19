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


def _coordinates_match_trip(catch: CatchEntry) -> bool:
    trip = catch.trip
    if trip is None:
        return False
    if catch.location_lat is None or catch.location_lng is None:
        return True
    return (
        catch.location_lat == trip.location_lat
        and catch.location_lng == trip.location_lng
    )


def _resolve_general_location_name(catch: CatchEntry) -> Optional[str]:
    if catch.general_location_name:
        return catch.general_location_name
    trip = catch.trip
    if trip is None:
        return None
    if _coordinates_match_trip(catch) and trip.general_location_name:
        return trip.general_location_name
    return None


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
        "group": species.group.name if species.group else None,
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
        .options(joinedload(CatchEntry.trip))
        .filter(*base_filter)
        .order_by(CatchEntry.date_time.desc())
        .all()
    )

    total_catches = len(catch_rows)

    def _catch_item(row: CatchEntry) -> Dict[str, Any]:
        item: Dict[str, Any] = {
            "id": row.id,
            "dateTime": row.date_time,
            "length": row.length,
            "weight": row.weight,
        }
        general_name = _resolve_general_location_name(row)
        if general_name:
            item["generalLocationName"] = general_name
        return item

    catches = [_catch_item(row) for row in catch_rows]

    catch_by_id = {row.id: row for row in catch_rows}

    personal_best: Optional[Dict[str, Any]] = None
    pb_row = personal_best_data.get_personal_best_row(db, user_id, species_id)
    if pb_row is not None:
        pb_catch = catch_by_id.get(pb_row.catch_id)
        if pb_catch is not None:
            personal_best = _catch_item(pb_catch)
        else:
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
        .options(joinedload(SpeciesRow.regions), joinedload(SpeciesRow.group))
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


def _escape_ilike_pattern(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_user_caught_species_names(db: Session, user_id: int) -> Set[str]:
    rows = (
        db.query(CatchEntry.species)
        .filter(CatchEntry.user_id == user_id)
        .distinct()
        .all()
    )
    return {row[0] for row in rows}


def get_species(
    db: Session,
    user_id: int,
    kingdom: Optional[str] = None,
    search: Optional[str] = None,
    caught: Optional[str] = None,
    favorites_only: bool = False,
    sort: str = "name_asc",
):
    favorite_ids = get_user_favorite_species_ids(db, user_id)

    if favorites_only and not favorite_ids:
        return []

    query = db.query(SpeciesRow).options(
        joinedload(SpeciesRow.regions),
        joinedload(SpeciesRow.group),
    )

    if kingdom:
        query = query.filter(SpeciesRow.kingdom == kingdom)

    if search and search.strip():
        pattern = f"%{_escape_ilike_pattern(search.strip())}%"
        query = query.filter(SpeciesRow.name.ilike(pattern, escape="\\"))

    if favorites_only:
        query = query.filter(SpeciesRow.id.in_(favorite_ids))

    if caught == "caught":
        caught_names = get_user_caught_species_names(db, user_id)
        if not caught_names:
            return []
        query = query.filter(SpeciesRow.name.in_(caught_names))
    elif caught == "uncaught":
        caught_names = get_user_caught_species_names(db, user_id)
        if caught_names:
            query = query.filter(~SpeciesRow.name.in_(caught_names))

    if sort == "name_desc":
        query = query.order_by(SpeciesRow.name.desc())
    else:
        query = query.order_by(SpeciesRow.name.asc())

    rows = query.all()
    return [_species_row_to_dict(s, favorite_ids) for s in rows]
