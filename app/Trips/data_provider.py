from app.mock_database.mock_db import trips_db, catches_db
from app.models.log import Trip

def get_trips():
    return trips_db

def get_catch_list(trip_id: int):
    catch_list = []
    for catch in catches_db:
        if catch.trip_id == trip_id:
            catch_list.append(catch)
    return catch_list

def create_trip(trip):
    new_id = len(trips_db) + 1
    trip_with_id = trip.copy(update={"id": new_id})
    trips_db.append(trip_with_id)
    return trip_with_id

def delete_trip(trip_id: int):
    global trips_db
    for i, trip in enumerate(trips_db):
        if trip.id == trip_id:
            del trips_db[i]
            return True
    return False

def get_trip_by_id(trip_id: int):
    for trip in trips_db:
        if trip.id == trip_id:
            return trip
    return None

def update_trip(trip_to_update: Trip):
    for trip in trips_db:
        if trip.id == trip_to_update.id:
            trip = trip_to_update
            return trip
    return None

def add_catch(trip_id: int, catch):
    print("Adding catch to trip ID:", trip_id)
    new_id = len(catches_db) + 1
    catch_with_id = catch.copy(update={"id": new_id, "trip_id": trip_id})
    catches_db.append(catch_with_id)
    print("Catch added:", catch_with_id)
    print("Current catches DB:", catches_db)
    return catch_with_id