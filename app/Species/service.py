import app.Species.data_provider as data_provider

def get_species():
    return data_provider.get_species()

def get_saltwater_species():
    return data_provider.get_saltwater_species()

def get_freshwater_species():
    return data_provider.get_freshwater_species()