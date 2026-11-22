from sqlalchemy.orm import Session

import app.Locations.data_provider as data_provider
from app.Trips.general_location import ensure_general_location_name
from app.models.log import SavedLocation, SavedLocationCreate

SAVED_LOCATION_NOTES_MAX_LENGTH = 800


def list_saved_locations(db: Session, user_id: int) -> list[SavedLocation]:
    return data_provider.get_saved_locations(db, user_id)


def create_saved_location(
    db: Session, payload: SavedLocationCreate, user_id: int
) -> SavedLocation:
    location = ensure_general_location_name(payload.location)
    payload = payload.model_copy(
        update={"location": location},
    )
    return data_provider.create_saved_location(db, payload, user_id)


def delete_saved_location(
    db: Session,
    location_id: int,
    user_id: int,
    latitude: float | None = None,
    longitude: float | None = None,
    trip_id: int | None = None,
) -> bool:
    return data_provider.delete_saved_location(
        db, location_id, user_id, latitude, longitude, trip_id
    )