from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import Session, joinedload

from app.Auth.models import UserFavorite
from app.models.db_models import CatchEntry
from app.models.db_models import Species as SpeciesRow


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
    with_length = [row for row in catch_rows if row.length is not None]
    if with_length:
        best_row = with_length[0]
        for row in with_length[1:]:
            if row.length > best_row.length:
                best_row = row
            elif row.length == best_row.length and row.date_time > best_row.date_time:
                best_row = row
        personal_best = _catch_item(best_row)

    most_recent_catch = _catch_item(catch_rows[0]) if catch_rows else None

    return {
        "totalCatches": total_catches,
        "personalBest": personal_best,
        "mostRecentCatch": most_recent_catch,
        "catches": catches,
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
