from fastapi import APIRouter, HTTPException
from app.models.log import Trip, Catch
import app.Trips.service as service
from typing import List

router = APIRouter()

@router.get("/")
def get_trips():
    return service.get_trips()

@router.post("/")
def create_trip(trip: Trip):
    new_trip = service.create_trip(trip)
    return {"message": "Trip added", "trip": new_trip}

@router.delete("/{trip_id}")
def delete_trip(trip_id: int):
    status = service.delete_trip(trip_id)
    if not status:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"message": f"Trip {trip_id} deleted"}

@router.put("/{trip_id}/catchList")
def update_catch_list(trip_id: int, catch_list: List[Catch]):
    response = service.update_catch_list(trip_id, catch_list)
    if not response:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"message": "Catch list updated", "catchList": response}

@router.post("/{trip_id}/addCatch")
def add_catch(trip_id: int, catch: Catch):
    print()
    response = service.add_catch(trip_id, catch)
    if not response:
        raise HTTPException(status_code=404, detail="Trip not found")
    return response

@router.get("/{trip_id}/catchList")
def get_catch_list(trip_id: int):
    response = service.get_catch_list(trip_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Catch list not found")
    return response