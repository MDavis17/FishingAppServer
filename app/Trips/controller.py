from fastapi import APIRouter, Depends, HTTPException
from app.models.log import Trip, Catch
import app.Trips.service as service
from app.Auth.dependencies import get_current_user
from app.Auth.models import User
from typing import List

router = APIRouter()


@router.get("/")
def get_trips(current_user: User = Depends(get_current_user)):
    return service.get_trips(current_user.id)


@router.post("/")
def create_trip(trip: Trip, current_user: User = Depends(get_current_user)):
    new_trip = service.create_trip(trip, current_user.id)
    return {"message": "Trip added", "trip": new_trip.model_dump(mode="json")}


@router.delete("/{trip_id}")
def delete_trip(trip_id: int, current_user: User = Depends(get_current_user)):
    status = service.delete_trip(trip_id, current_user.id)
    if not status:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"message": f"Trip {trip_id} deleted"}


@router.put("/{trip_id}/markAsCompleted")
def mark_trip_as_completed(
    trip_id: int, current_user: User = Depends(get_current_user)
):
    try:
        updated_trip = service.mark_trip_as_completed(trip_id, current_user.id)
        return {
            "message": f"Trip {trip_id} marked as completed",
            "trip": updated_trip,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{trip_id}/catchList")
def update_catch_list(
    trip_id: int,
    catch_list: List[Catch],
    current_user: User = Depends(get_current_user),
):
    try:
        response = service.update_catch_list(trip_id, catch_list, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not response:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"message": "Catch list updated", "catchList": response}


@router.post("/{trip_id}/addCatch")
def add_catch(
    trip_id: int,
    catch: Catch,
    current_user: User = Depends(get_current_user),
):
    response = service.add_catch(trip_id, catch, current_user.id)
    if not response:
        raise HTTPException(status_code=404, detail="Trip not found")
    return response


@router.get("/{trip_id}/catchList")
def get_catch_list(trip_id: int, current_user: User = Depends(get_current_user)):
    response = service.get_catch_list(trip_id, current_user.id)
    if response is None:
        raise HTTPException(status_code=404, detail="Catch list not found")
    return response


@router.get("/upcomingTrip")
def get_upcoming_trip(current_user: User = Depends(get_current_user)):
    response = service.get_upcoming_trip(current_user.id)
    if response is None or response == []:
        return None
    return response


@router.get("/mostRecentTrip")
def get_most_recent_trip(current_user: User = Depends(get_current_user)):
    response = service.get_most_recent_trip(current_user.id)
    if response is None or response == []:
        return None
    return response
