from typing import Optional

from sqlalchemy.orm import Session

from app.models.db_models import SavedLocation as SavedLocationRow
from app.models.log import LatLong, Location, SavedLocation, SavedLocationCreate, TripType


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
    db.commit()
    db.refresh(row)
    return _row_to_schema(row)