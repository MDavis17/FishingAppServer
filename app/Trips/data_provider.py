from app.mock_database.mock_db import trips_db, catches_db
from app.models.log import Trip


def _trip_owned_by_user(trip, user_id: int) -> bool:
    return trip.user_id == user_id


def get_trips(user_id: int):
    return [trip for trip in trips_db if _trip_owned_by_user(trip, user_id)]


def get_upcoming_trip(user_id: int):
    upcoming_trip = None
    for trip in trips_db:
        if not _trip_owned_by_user(trip, user_id):
            continue
        if trip.status == "Planned" and (
            upcoming_trip is None or trip.date < upcoming_trip.date
        ):
            upcoming_trip = trip
    return upcoming_trip


def get_most_recent_trip(user_id: int):
    most_recent_trip = None
    for trip in trips_db:
        if not _trip_owned_by_user(trip, user_id):
            continue
        if trip.status == "Completed" and (
            most_recent_trip is None or trip.date > most_recent_trip.date
        ):
            most_recent_trip = trip
    return most_recent_trip


def get_catch_list(trip_id: int, user_id: int):
    trip = get_trip_by_id(trip_id, user_id)
    if trip is None:
        return None
    catch_list = []
    for catch in catches_db:
        if catch.trip_id == trip_id and catch.user_id == user_id:
            catch_list.append(catch)
    return catch_list


def create_trip(trip, user_id: int):
    new_id = len(trips_db) + 1
    trip_with_id = trip.model_copy(update={"id": new_id, "user_id": user_id})
    trips_db.append(trip_with_id)
    return trip_with_id


def delete_trip(trip_id: int, user_id: int):
    global trips_db
    for i, trip in enumerate(trips_db):
        if trip.id == trip_id and _trip_owned_by_user(trip, user_id):
            del trips_db[i]
            return True
    return False


def delete_catches_for_trip(trip_id: int, user_id: int):
    global catches_db
    catches_db = [
        catch
        for catch in catches_db
        if not (catch.trip_id == trip_id and catch.user_id == user_id)
    ]
    return True


def get_trip_by_id(trip_id: int, user_id: int):
    for trip in trips_db:
        if trip.id == trip_id and _trip_owned_by_user(trip, user_id):
            return trip
    return None


def update_trip(trip_to_update: Trip, user_id: int):
    if trip_to_update.user_id != user_id:
        return None
    for i, trip in enumerate(trips_db):
        if trip.id == trip_to_update.id and _trip_owned_by_user(trip, user_id):
            trips_db[i] = trip_to_update
            return trips_db[i]
    return None


def add_catch(trip_id: int, catch, user_id: int):
    trip = get_trip_by_id(trip_id, user_id)
    if trip is None:
        return None
    new_id = len(catches_db) + 1
    catch_with_id = catch.model_copy(update={"id": new_id, "trip_id": trip_id, "user_id": user_id})
    catches_db.append(catch_with_id)
    return catch_with_id
