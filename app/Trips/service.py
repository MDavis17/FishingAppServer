from collections import Counter
from app.models.log import Trip, Catch
import app.Trips.data_provider as data_provider
from typing import List

def get_trips():
    trips = data_provider.get_trips()
    trips_with_catches = []
    for trip in trips:
        catch_list = data_provider.get_catch_list(trip.id)
        catch_summary = get_catch_summary(catch_list)
        trip_with_catches = trip.dict()
        trip_with_catches["catchList"] = catch_list
        trip_with_catches["catchSummary"] = catch_summary
        trips_with_catches.append(trip_with_catches)
    return trips_with_catches

def get_catch_summary(catchList: List[Catch]) -> str:
    species_counts = Counter(catch.species for catch in catchList)
    formatted_species = [
        f"{species}" if count == 1 else f"{species} ({count})"
        for species, count in species_counts.items()
    ]
    return ", ".join(formatted_species)

def get_catch_list(trip_id: int):
    return data_provider.get_catch_list(trip_id)

def create_trip(trip: Trip):
    new_trip = data_provider.create_trip(trip)
    return new_trip

def delete_trip(trip_id: int):
    return data_provider.delete_trip(trip_id)

def add_catch(trip_id: int, catch: Catch):
    return data_provider.add_catch(trip_id, catch)

def update_catch_list(trip_id: int, catch_list):
    trip = data_provider.get_trip_by_id(trip_id)
    if not trip:
        raise ValueError("Trip not found")
    
    trip.catchList = catch_list
    trip.catchSummary = get_catch_summary(trip)
    
    updated_trip = data_provider.update_trip(trip)
    return updated_trip.catchList