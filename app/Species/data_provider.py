from app.mock_database.mock_db import species_db

def get_species():
    return sorted(species_db, key=lambda s: s["name"].lower())
