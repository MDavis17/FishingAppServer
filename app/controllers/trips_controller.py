from fastapi import APIRouter
from app.models.log import Trip
import  app.services.trips_service as service
from app.mock_database.mock_db import trips_db

router = APIRouter()

@router.get("/")
def get_trips():
    return service.get_trips()

@router.post("/")
def create_trip(trip: Trip):
    new_id = len(trips_db) + 1
    catch_summary = service.get_catch_summary(trip)
    new_trip = trip.copy(update={"id": new_id, "catchSummary": catch_summary})    
    trips_db.append(new_trip)
    return {"message": "Trip added", "trip": new_trip}

@router.delete("/{trip_id}")
def delete_trip(trip_id: int):
    global trips_db
    for i, trip in enumerate(trips_db):
        if trip.id == trip_id:
            del trips_db[i]
            return {"message": f"Trip {trip_id} deleted"}
    raise HTTPException(status_code=404, detail="Trip not found")