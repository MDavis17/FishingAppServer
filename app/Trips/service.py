from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

import app.Trips.data_provider as data_provider
from app.models.log import (
    Catch,
    CatchStat,
    IndividualCatch,
    Species,
    SpeciesGroup,
    Trip,
    TripCatchListResponse,
    TripStatus,
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _infer_trip_status(trip_date: datetime) -> TripStatus:
    now = datetime.now(timezone.utc)
    trip_dt = _ensure_utc(trip_date)
    return TripStatus.Completed if trip_dt < now else TripStatus.Planned


def get_trips(db: Session, user_id: int):
    trips = data_provider.get_trips(db, user_id)
    trips_with_catches = []
    for trip in trips:
        catch_list = data_provider.get_catch_list(db, trip.id, user_id) or []
        catch_summary = get_catch_summary(catch_list)
        trip_with_catches = trip.model_dump()
        trip_with_catches["catchList"] = catch_list
        trip_with_catches["catchSummary"] = catch_summary
        trips_with_catches.append(trip_with_catches)
    return trips_with_catches


def get_upcoming_trip(db: Session, user_id: int):
    upcoming_trip = data_provider.get_upcoming_trip(db, user_id)
    if not upcoming_trip:
        return None

    catch_list = data_provider.get_catch_list(db, upcoming_trip.id, user_id) or []
    catch_summary = get_catch_summary(catch_list)
    upcoming_trip_with_catches = upcoming_trip.model_dump()
    upcoming_trip_with_catches["catchList"] = catch_list
    upcoming_trip_with_catches["catchSummary"] = catch_summary
    return upcoming_trip_with_catches


def get_most_recent_trip(db: Session, user_id: int):
    most_recent_trip = data_provider.get_most_recent_trip(db, user_id)
    if not most_recent_trip:
        return None

    catch_list = data_provider.get_catch_list(db, most_recent_trip.id, user_id) or []
    catch_summary = get_catch_summary(catch_list)
    most_recent_trip_with_catches = most_recent_trip.model_dump()
    most_recent_trip_with_catches["catchList"] = catch_list
    most_recent_trip_with_catches["catchSummary"] = catch_summary
    return most_recent_trip_with_catches


def get_catch_summary(catchList: List[Catch]) -> str:
    species_counts = Counter(catch.species for catch in catchList)
    formatted_species = [
        f"{species}" if count == 1 else f"{species} ({count})"
        for species, count in species_counts.items()
    ]
    return ", ".join(formatted_species)


def _format_catch_time(dt: datetime) -> str:
    hour = dt.strftime("%I").lstrip("0") or "12"
    return f"{hour}:{dt.strftime('%M %p')}"


def build_trip_catch_list(
    db: Session,
    trip_id: int,
    user_id: int,
) -> Optional[TripCatchListResponse]:
    trip = data_provider.get_trip_by_id(db, trip_id, user_id)
    if trip is None:
        return None
    catch_list = data_provider.get_catch_list(db, trip_id, user_id) or []
    return _assemble_trip_catch_list(db, catch_list, trip.targetSpecies)


def _assemble_trip_catch_list(
    db: Session,
    catch_list: List[Catch],
    target_species: List[Species],
) -> TripCatchListResponse:
    species_names = list({c.species for c in catch_list})
    image_by_name = data_provider.get_species_images_by_name(db, species_names)

    grouped: dict[str, list[Catch]] = defaultdict(list)
    for catch in catch_list:
        grouped[catch.species].append(catch)

    species_groups: List[SpeciesGroup] = []
    for species, catches in sorted(
        grouped.items(), key=lambda item: len(item[1]), reverse=True
    ):
        catches_sorted = sorted(catches, key=lambda c: c.dateTime)
        lengths = [c.length for c in catches_sorted if c.length is not None]
        largest = max(lengths) if lengths else None
        individual = [
            IndividualCatch(
                id=catch.id or 0,
                time=_format_catch_time(catch.dateTime),
                length=catch.length,
                bait=catch.bait,
            )
            for catch in catches_sorted
            if catch.id is not None
        ]
        species_groups.append(
            SpeciesGroup(
                species=species,
                speciesImage=image_by_name.get(species) or None,
                count=len(catches_sorted),
                largestLength=largest,
                catches=individual,
            )
        )

    stats: List[CatchStat] = [
        CatchStat(type="totalCaught", value=len(catch_list))
    ]

    if target_species:
        target_names = {s.name for s in target_species}
        caught_names = {c.species for c in catch_list}
        achieved = target_names.issubset(caught_names)
        stats.append(CatchStat(type="targetAchieved", value=achieved))

    lengths_all = [c.length for c in catch_list if c.length is not None]
    if lengths_all:
        largest_overall = max(lengths_all)
        stats.append(CatchStat(type="largestCatch", value=largest_overall))

    return TripCatchListResponse(stats=stats, speciesGroups=species_groups)


def get_catch_list(db: Session, trip_id: int, user_id: int):
    return build_trip_catch_list(db, trip_id, user_id)


def create_trip(db: Session, trip: Trip, user_id: int):
    now = datetime.now(timezone.utc)
    updates: dict = {"createdAt": now, "user_id": user_id}

    if trip.status is None:
        updates["status"] = _infer_trip_status(trip.date)

    trip_to_create = trip.model_copy(update=updates)
    new_trip = data_provider.create_trip(db, trip_to_create, user_id)
    return new_trip


def delete_trip(db: Session, trip_id: int, user_id: int):
    data_provider.delete_catches_for_trip(db, trip_id, user_id)
    return data_provider.delete_trip(db, trip_id, user_id)


def add_catch(db: Session, trip_id: int, catch: Catch, user_id: int):
    return data_provider.add_catch(db, trip_id, catch, user_id)


TRIP_NOTES_MAX_LENGTH = 800


def update_trip_notes(db: Session, trip_id: int, user_id: int, notes: Optional[str]):
    if notes is not None and len(notes) > TRIP_NOTES_MAX_LENGTH:
        raise ValueError(
            f"Notes must be at most {TRIP_NOTES_MAX_LENGTH} characters"
        )
    existing_trip = data_provider.get_trip_by_id(db, trip_id, user_id)
    if not existing_trip:
        raise ValueError("Trip not found")
    updated_trip_model = existing_trip.model_copy(update={"notes": notes})
    updated_trip = data_provider.update_trip(db, updated_trip_model, user_id)
    if not updated_trip:
        raise ValueError("Failed to update trip notes")
    return updated_trip


def mark_trip_as_completed(db: Session, trip_id: int, user_id: int):
    existing_trip = data_provider.get_trip_by_id(db, trip_id, user_id)
    if not existing_trip:
        raise ValueError("Trip not found")
    completed_existing_trip = existing_trip.model_copy(
        update={"status": TripStatus.Completed}
    )
    updated_trip = data_provider.update_trip(db, completed_existing_trip, user_id)
    if not updated_trip:
        raise ValueError("Failed to mark trip as complete")
    return updated_trip


def update_catch_list(db: Session, trip_id: int, catch_list, user_id: int):
    result = data_provider.replace_catch_list(db, trip_id, user_id, catch_list)
    if result is None:
        raise ValueError("Trip not found")
    return result
