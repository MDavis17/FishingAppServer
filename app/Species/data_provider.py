from typing import Optional, Set

from sqlalchemy.orm import Session

from app.Auth.models import UserFavorite
from app.mock_database.mock_db import species_db


def get_species_by_id(species_id: int):
    for species in species_db:
        if species["id"] == species_id:
            return species
    return None


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


def _species_for_user(species: dict, favorite_ids: Set[int]) -> dict:
    return {**species, "isFavorite": species["id"] in favorite_ids}


def _filter_kingdom(species_list: list, kingdom: Optional[str]) -> list:
    if not kingdom:
        return species_list
    return [s for s in species_list if s.get("kingdom") == kingdom]


def get_species(db: Session, user_id: int, kingdom: Optional[str] = None):
    favorite_ids = get_user_favorite_species_ids(db, user_id)
    non_favorites = [
        _species_for_user(s, favorite_ids)
        for s in species_db
        if s["id"] not in favorite_ids
    ]
    non_favorites = _filter_kingdom(non_favorites, kingdom)
    return sorted(non_favorites, key=lambda s: s["name"].lower())


def get_favorite_species(db: Session, user_id: int, kingdom: Optional[str] = None):
    favorite_ids = get_user_favorite_species_ids(db, user_id)
    favorites = [
        _species_for_user(s, favorite_ids)
        for s in species_db
        if s["id"] in favorite_ids
    ]
    favorites = _filter_kingdom(favorites, kingdom)
    return sorted(favorites, key=lambda s: s["name"].lower())
