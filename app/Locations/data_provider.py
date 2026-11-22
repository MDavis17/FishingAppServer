from typing import Optional

from sqlalchemy.orm import Session

from app.models.db_models import SavedLocation as SavedLocationRow
from app.models.db_models import Trip as TripRow
from app.models.log import LatLong, Location, SavedLocation, SavedLocationCreate, TripType

COORD_MATCH_EPSILON = 0.00001


def _coordinates_match(
    lat_a: float, lng_a: float, lat_b: float, lng_b: float
) -> bool:
    return (
        abs(lat_a - lat_b) < COORD_MATCH_EPSILON
        and abs(lng_a - lng_b) < COORD_MATCH_EPSILON
    )


def _trip_type_value(trip_type) -> Optional[TripType]:
    if trip_type is None:
        return None
    raw = trip_type.value if hasattr(trip_type, "value") else trip_type
    return TripType(raw)


def _row_to_schema(row: SavedLocationRow) -> SavedLocation:
    return SavedLocation(
        id=row.id,
        location=Location(
            name=row.location_name,
            coordinates=LatLong(
                latitude=row.location_lat,
                longitude=row.location_lng,
            ),
            generalLocationName=row.general_location_name,
        ),
        didCatchFishHere=row.did_catch_fish_here,
        notes=row.notes,
        tripType=_trip_type_value(row.trip_type),
        lastFishedAt=row.last_fished_at,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )


def _apply_create_fields(row: SavedLocationRow, payload: SavedLocationCreate) -> None:
    row.location_name = payload.location.name
    row.location_lat = payload.location.coordinates.latitude
    row.location_lng = payload.location.coordinates.longitude
    row.general_location_name = payload.location.generalLocationName
    row.did_catch_fish_here = payload.didCatchFishHere
    row.notes = payload.notes
    if payload.tripType is not None:
        row.trip_type = payload.tripType.value


def _link_trips(
    db: Session,
    user_id: int,
    saved_location_id: int,
    saved_lat: float,
    saved_lng: float,
    trip_id: Optional[int],
) -> None:
    trips = db.query(TripRow).filter(TripRow.user_id == user_id).all()
    for trip in trips:
        if trip.id == trip_id or _coordinates_match(
            trip.location_lat, trip.location_lng, saved_lat, saved_lng
        ):
            trip.location_id = saved_location_id
    db.flush()


def _unlink_trips(
    db: Session,
    user_id: int,
    saved_ids: set[int],
    targets: list[tuple[float, float]],
    trip_id: Optional[int],
) -> None:
    trips = db.query(TripRow).filter(TripRow.user_id == user_id).all()
    for trip in trips:
        should_unlink = False
        if trip_id is not None and trip.id == trip_id:
            should_unlink = True
        elif trip.location_id is not None and trip.location_id in saved_ids:
            should_unlink = True
        elif any(
            _coordinates_match(trip.location_lat, trip.location_lng, lat, lng)
            for lat, lng in targets
        ):
            should_unlink = True
        if should_unlink:
            trip.location_id = None
    db.flush()


def get_saved_locations(db: Session, user_id: int) -> list[SavedLocation]:
    rows = (
        db.query(SavedLocationRow)
        .filter(SavedLocationRow.user_id == user_id)
        .order_by(SavedLocationRow.created_at.desc())
        .all()
    )
    return [_row_to_schema(row) for row in rows]


def create_saved_location(
    db: Session, payload: SavedLocationCreate, user_id: int
) -> SavedLocation:
    row = SavedLocationRow(user_id=user_id)
    _apply_create_fields(row, payload)
    db.add(row)
    db.flush()
    _link_trips(
        db,
        user_id,
        row.id,
        row.location_lat,
        row.location_lng,
        payload.tripId,
    )
    db.commit()
    db.refresh(row)
    return _row_to_schema(row)


def delete_saved_location(
    db: Session,
    location_id: int,
    user_id: int,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    trip_id: Optional[int] = None,
) -> bool:
    rows = (
        db.query(SavedLocationRow)
        .filter(SavedLocationRow.user_id == user_id)
        .all()
    )
    targets: list[tuple[float, float]] = []
    if latitude is not None and longitude is not None:
        targets.append((latitude, longitude))

    anchor = next((row for row in rows if row.id == location_id), None)
    if anchor is not None:
        targets.append((anchor.location_lat, anchor.location_lng))

    to_delete = [
        row
        for row in rows
        if row.id == location_id
        or any(
            _coordinates_match(row.location_lat, row.location_lng, lat, lng)
            for lat, lng in targets
        )
    ]
    if not to_delete and trip_id is None:
        return False

    saved_ids = {row.id for row in to_delete}
    _unlink_trips(db, user_id, saved_ids, targets, trip_id)
    for row in to_delete:
        db.delete(row)
    db.commit()
    return True