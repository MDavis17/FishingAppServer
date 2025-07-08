from app.mock_database.mock_db import trips_db, catches_db

def getTrips():
    return trips_db

def get_catch_list(trip_id):
    catch_list = []
    for catch in catches_db:
        if catch.get("tripId") is trip_id
        catches_list.append(catch)
    return catch_list
