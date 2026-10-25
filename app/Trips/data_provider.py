from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.db_models import CatchEntry as CatchRow
from app.models.db_models import Species as SpeciesRow
from app.models.db_models import Trip as TripRow
from app.models.log import Catch, LatLong, Location, Species, Trip, TripStatus


def _trip_row_to_schema(row: TripRow) -> Trip:
    return Trip(
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
        ),
        status=TripStatus(row.status),
        targetSpecies=[
            Species(id=s.id, name=s.name) for s in (row.target_species or [])
        ],
    )


def _catch_row_to_schema(row: CatchRow) -> Catch:
    location = None
    if row.location_lat is not None and row.location_lng is not None:
        location = Location(
            name=row.location_name or "",
            coordinates=LatLong(
                latitude=row.location_lat,
                longitude=row.location_lng,
            ),
        )
    elif row.location_name:
        location = Location(
            name=row.location_name,
            coordinates=LatLong(latitude=0.0, longitude=0.0),
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
    )


def _apply_trip_fields(row: TripRow, trip: Trip) -> None:
    row.date = trip.date
    row.status = trip.status.value if isinstance(trip.status, TripStatus) else trip.status
    row.location_name = trip.location.name
    row.location_lat = trip.location.coordinates.latitude
    row.location_lng = trip.location.coordinates.longitude
    if trip.createdAt is not None:
        row.created_at = trip.createdAt


def _resolve_target_species(db: Session, trip: Trip) -> List[SpeciesRow]:
    if not trip.targetSpecies:
        return []
    ids = [s.id for s in trip.targetSpecies]
    return db.query(SpeciesRow).filter(SpeciesRow.id.in_(ids)).all()


def get_trips(db: Session, user_id: int):
    rows = (
        db.query(TripRow)
        .options(joinedload(TripRow.target_species))
        .filter(TripRow.user_id == user_id)
        .all()
    )
    return [_trip_row_to_schema(row) for row in rows]


def get_upcoming_trip(db: Session, user_id: int):
    rows = (
        db.query(TripRow)
        .options(joinedload(TripRow.target_species))
        .filter(TripRow.user_id == user_id, TripRow.status == TripStatus.Planned.value)
        .order_by(TripRow.date.asc())
        .all()
    )
    if not rows:
        return None
    return _trip_row_to_schema(rows[0])


def get_most_recent_trip(db: Session, user_id: int):
    rows = (
        db.query(TripRow)
        .options(joinedload(TripRow.target_species))
        .filter(TripRow.user_id == user_id, TripRow.status == TripStatus.Completed.value)
        .order_by(TripRow.date.desc())
        .all()
    )
    if not rows:
        return None
    return _trip_row_to_schema(rows[0])


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
    db.query(CatchRow).filter(
        CatchRow.trip_id == trip_id,
        CatchRow.user_id == user_id,
    ).delete(synchronize_session=False)
    db.commit()
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
    )
    if catch.location is not None:
        row.location_name = catch.location.name
        row.location_lat = catch.location.coordinates.latitude
        row.location_lng = catch.location.coordinates.longitude

    db.add(row)
    db.commit()
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
