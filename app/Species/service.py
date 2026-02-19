import app.Species.data_provider as data_provider

def get_species():
    return data_provider.get_species()

def get_favorite_species():
    return data_provider.get_favorite_species()

def toggle_species_favorite(species_id: int):
    updated = data_provider.toggle_species_favorite(species_id)
    if updated is None:
        raise ValueError("Species not found")
    return updated
