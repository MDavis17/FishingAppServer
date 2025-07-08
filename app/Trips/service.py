from collections import Counter
from app.models.log import Trip
import app.Trips.data_provider as data_provider

def get_trips():
    return data_provider.getTrips()

def get_catch_summary(trip: Trip):
    species_counts = Counter(catch["species"] for catch in trip.catchList)
    formatted_species = [
        f"{species}" if count == 1 else f"{species} ({count})"
        for species, count in species_counts.items()
    ]
    return ", ".join(formatted_species)

def get_catch_list(trip_id):
    return data_provider.get_catch_list(trip_id)

def create_trip(trip: Trip):
    new_trip = data_provider.create_trip(trip)
    return new_trip

def delete_trip(trip_id: int):
    return data_provider.delete_trip(trip_id)
