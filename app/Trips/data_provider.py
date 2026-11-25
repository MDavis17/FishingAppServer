from typing import Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

import app.PersonalBests.service as personal_best_service
from app.models.db_models import CatchEntry as CatchRow
from app.models.db_models import SavedLocation as SavedLocationRow
from app.models.db_models import Species as SpeciesRow
from app.models.db_models import Trip as TripRow
from app.models.log import Catch, LatLong, Location, Species, Trip, TripStatus, TripType

COORD_MATCH_EPSILON = 0.00001


def _coordinates_match(
    lat_a: float, lng_a: float, lat_b: float, lng_b: float
) -> bool:
    return (
        abs(lat_a - lat_b) < COORD_MATCH_EPSILON
        and abs(lng_a - lng_b) < COORD_MATCH_EPSILON
    )


def _user_saved_location_coords(
    db: Session, user_id: int
) -> List[tuple[int, float, float]]:
    rows = (
        db.query(
            SavedLocationRow.id,
            SavedLocationRow.location_lat,
            SavedLocationRow.location_lng,
        )
        .filter(SavedLocationRow.user_id == user_id)
        .all()
    )
    return [(row.id, row.location_lat, row.location_lng) for row in rows]


def _resolve_saved_location_id(
    row: TripRow, saved: List[tuple[int, float, float]]
) -> Optional[int]:
    if not saved:
        return None
    saved_ids = {item[0] for item in saved}
    if row.location_id is not None and row.location_id in saved_ids:
        return row.location_id
    for saved_id, lat, lng in saved:
        if _coordinates_match(row.location_lat, row.location_lng, lat, lng):
            return saved_id
    return None


def _trip_row_to_schema(
    row: TripRow,
    saved_locations: Optional[List[tuple[int, float, float]]] = None,
) -> Trip:
    trip = Trip(
        id=row.id,
        user_id=row.user_id,
        date=row.date,
        createdAt=row.created_at,
        location=Location(
            name=row.location_name,
            coordinates=LatLong(
                latitude=row.location_lat,
                longitude=row.location_lng,
            ),
            generalLocationName=row.general_location_name,
        ),
        status=TripStatus(row.status),
        tripType=TripType(row.trip_type.value if hasattr(row.trip_type, "value") else row.trip_type),
        targetSpecies=[
            Species(id=s.id, name=s.name) for s in (row.target_species or [])
        ],
        notes=row.notes,
    )
    if saved_locations is not None:
        return trip.model_copy(
            update={
                "savedLocationId": _resolve_saved_location_id(row, saved_locations),
            }
        )
    return trip


def _catch_row_to_schema(row: CatchRow) -> Catch:
    location = None
    if row.location_lat is not None and row.location_lng is not None:
        location = Location(
            name=row.location_name or "",
            coordinates=LatLong(
                latitude=row.location_lat,
                longitude=row.location_lng,
            ),
            generalLocationName=row.general_location_name,
        )
    elif row.location_name:
        location = Location(
            name=row.location_name,
            coordinates=LatLong(latitude=0.0, longitude=0.0),
            generalLocationName=row.general_location_name,
        )

    return Catch(
        id=row.id,
        trip_id=row.trip_id,
        user_id=row.user_id,
        dateTime=row.date_time,
        species=row.species,
        waterType=row.water_type,
        bait=row.bait,
        location=location,
        length=row.length,
        isCatchPB=bool(row.is_catch_pb),
    )


def _apply_trip_fields(row: TripRow, trip: Trip) -> None:
    row.date = trip.date
    row.status = trip.status.value if isinstance(trip.status, TripStatus) else trip.status
    row.trip_type = (
        trip.tripType.value if isinstance(trip.tripType, TripType) else trip.tripType
    )
    row.location_name = trip.location.name
    row.location_lat = trip.location.coordinates.latitude
    row.location_lng = trip.location.coordinates.longitude
    row.general_location_name = trip.location.generalLocationName
    if trip.createdAt is not None:
        row.created_at = trip.createdAt
    row.notes = trip.notes


def _resolve_target_species(db: Session, trip: Trip) -> List[SpeciesRow]:
    if not trip.targetSpecies:
        return []
    ids = [s.id for s in trip.targetSpecies]
    return db.query(SpeciesRow).filter(SpeciesRow.id.in_(ids)).all()


def get_trips(db: Session, user_id: int):
    saved = _user_saved_location_coords(db, user_id)
    rows = (
        db.query(TripRow)
        .options(joinedload(TripRow.target_species))
        .filter(TripRow.user_id == user_id)
        .all()
    )
    return [_trip_row_to_schema(row, saved) for row in rows]


def get_upcoming_trip(db: Session, user_id: int):
    saved = _user_saved_location_coords(db, user_id)
    rows = (
        db.query(TripRow)
        .options(joinedload(TripRow.target_species))
        .filter(TripRow.user_id == user_id, TripRow.status == TripStatus.Planned.value)
        .order_by(TripRow.date.asc())
        .all()
    )
    if not rows:
        return None
    return _trip_row_to_schema(rows[0], saved)


def get_most_recent_trip(db: Session, user_id: int):
    saved = _user_saved_location_coords(db, user_id)
    rows = (
        db.query(TripRow)
        .options(joinedload(TripRow.target_species))
        .filter(TripRow.user_id == user_id, TripRow.status == TripStatus.Completed.value)
        .order_by(TripRow.date.desc())
        .all()
    )
    if not rows:
        return None
    return _trip_row_to_schema(rows[0], saved)


def get_species_images_by_name(
    db: Session, species_names: List[str]
) -> Dict[str, str]:
    if not species_names:
        return {}
    rows = (
        db.query(SpeciesRow.name, SpeciesRow.image)
        .filter(SpeciesRow.name.in_(species_names))
        .all()
    )
    return {name: image or "" for name, image in rows}


def get_catch_list(db: Session, trip_id: int, user_id: int):
    trip = get_trip_by_id(db, trip_id, user_id)
    if trip is None:
        return None
    rows = (
        db.query(CatchRow)
        .filter(CatchRow.trip_id == trip_id, CatchRow.user_id == user_id)
        .order_by(CatchRow.date_time.asc())
        .all()
    )
    return [_catch_row_to_schema(row) for row in rows]


def create_trip(db: Session, trip: Trip, user_id: int):
    row = TripRow(user_id=user_id)
    _apply_trip_fields(row, trip)
    row.target_species = _resolve_target_species(db, trip)
    db.add(row)
    db.commit()
    db.refresh(row)
    db.refresh(row, attribute_names=["target_species"])
    return _trip_row_to_schema(row)


def delete_trip(db: Session, trip_id: int, user_id: int):
    row = (
        db.query(TripRow)
        .filter(TripRow.id == trip_id, TripRow.user_id == user_id)
        .first()
    )
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def delete_catches_for_trip(db: Session, trip_id: int, user_id: int):
    catch_rows = (
        db.query(CatchRow.id, CatchRow.species)
        .filter(CatchRow.trip_id == trip_id, CatchRow.user_id == user_id)
        .all()
    )
    catch_ids = [row[0] for row in catch_rows]
    species_names = [row[1] for row in catch_rows]
    species_pairs = personal_best_service.species_pairs_for_deleted_pb_catches(
        db, user_id, catch_ids
    )
    db.query(CatchRow).filter(
        CatchRow.trip_id == trip_id,
        CatchRow.user_id == user_id,
    ).delete(synchronize_session=False)
    db.commit()
    personal_best_service.recompute_after_catch_deletes(
        db, user_id, catch_ids, species_pairs
    )
    personal_best_service.recompute_historical_pb_flags_for_species_list(
        db, user_id, species_names
    )
    return True


def get_trip_by_id(db: Session, trip_id: int, user_id: int):
    row = (
        db.query(TripRow)
        .options(joinedload(TripRow.target_species))
        .filter(TripRow.id == trip_id, TripRow.user_id == user_id)
        .first()
    )
    if row is None:
        return None
    return _trip_row_to_schema(row)


def update_trip(db: Session, trip_to_update: Trip, user_id: int):
    if trip_to_update.user_id != user_id:
        return None
    row = (
        db.query(TripRow)
        .options(joinedload(TripRow.target_species))
        .filter(TripRow.id == trip_to_update.id, TripRow.user_id == user_id)
        .first()
    )
    if row is None:
        return None
    _apply_trip_fields(row, trip_to_update)
    row.target_species = _resolve_target_species(db, trip_to_update)
    db.commit()
    db.refresh(row)
    db.refresh(row, attribute_names=["target_species"])
    return _trip_row_to_schema(row)


def add_catch(db: Session, trip_id: int, catch: Catch, user_id: int):
    trip = get_trip_by_id(db, trip_id, user_id)
    if trip is None:
        return None

    row = CatchRow(
        trip_id=trip_id,
        user_id=user_id,
        date_time=catch.dateTime,
        species=catch.species,
        water_type=catch.waterType,
        bait=catch.bait,
        length=catch.length,
    )
    if catch.location is not None:
        row.location_name = catch.location.name
        row.location_lat = catch.location.coordinates.latitude
        row.location_lng = catch.location.coordinates.longitude
        row.general_location_name = catch.location.generalLocationName

    db.add(row)
    db.commit()
    db.refresh(row)
    personal_best_service.record_catch_for_personal_best(db, row)
    personal_best_service.recompute_historical_pb_flags_for_species(
        db, user_id, row.species
    )
    db.refresh(row)
    return _catch_row_to_schema(row)


def replace_catch_list(
    db: Session,
    trip_id: int,
    user_id: int,
    catch_list: List[Catch],
) -> Optional[List[Catch]]:
    if get_trip_by_id(db, trip_id, user_id) is None:
        return None

    delete_catches_for_trip(db, trip_id, user_id)
    created: List[Catch] = []
    for catch in catch_list:
        created.append(add_catch(db, trip_id, catch, user_id))
    return created
