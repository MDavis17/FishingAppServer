from fastapi import APIRouter, HTTPException
from app.models.log import Trip
import app.Trips.service as service

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