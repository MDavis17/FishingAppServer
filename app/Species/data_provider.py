from app.mock_database.mock_db import species_db


def get_species_by_id(species_id: int):
    for species in species_db:
        if species["id"] == species_id:
            return species
    return None

def get_species():
    non_favorites = [s for s in species_db if not s.get("isFavorite")]
    return sorted(non_favorites, key=lambda s: s["name"].lower())

def get_favorite_species():
    favorites = [s for s in species_db if s.get("isFavorite")]
    return sorted(favorites, key=lambda s: s["name"].lower())

def toggle_species_favorite(species_id: int):
    for species in species_db:
        if species["id"] == species_id:
            species["isFavorite"] = not species["isFavorite"]
            return species
    return None
