from typing import Optional

from app.mock_database.mock_db import species_db


def get_species_by_id(species_id: int):
    for species in species_db:
        if species["id"] == species_id:
            return species
    return None

def get_species(kingdom: Optional[str] = None):
    non_favorites = [s for s in species_db if not s.get("isFavorite")]
    if kingdom:
        non_favorites = [s for s in non_favorites if s.get("kingdom") == kingdom]
    return sorted(non_favorites, key=lambda s: s["name"].lower())

def get_favorite_species(kingdom: Optional[str] = None):
    favorites = [s for s in species_db if s.get("isFavorite")]
    if kingdom:
        favorites = [s for s in favorites if s.get("kingdom") == kingdom]
    return sorted(favorites, key=lambda s: s["name"].lower())

def toggle_species_favorite(species_id: int):
    for species in species_db:
        if species["id"] == species_id:
            species["isFavorite"] = not species["isFavorite"]
            return species
    return None
