from collections import Counter
from app.models.log import Trip

def get_catch_summary(trip: Trip):
    species_counts = Counter(catch["species"] for catch in trip.catchList)
    formatted_species = [
        f"{species}" if count == 1 else f"{species} ({count})"
        for species, count in species_counts.items()
    ]
    return ", ".join(formatted_species)