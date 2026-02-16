from app.mock_database.mock_db import species_db

def get_species():
    return sorted(species_db, key=lambda s: s["name"].lower())

def toggle_species_favorite(species_id: int):
    for species in species_db:
        if species["id"] == species_id:
            species["isFavorite"] = not species["isFavorite"]
            return species
    return None
