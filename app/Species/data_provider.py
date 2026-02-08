from app.mock_database.mock_db import species_db

def get_species():
    return species_db

def get_saltwater_species():
    return [species for species in species_db if species["waterType"] == "Saltwater"]

def get_freshwater_species():
    return [species for species in species_db if species["waterType"] == "Freshwater"]