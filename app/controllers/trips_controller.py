from fastapi import APIRouter
from app.models.log import Trip
from app.services.trips_service import get_catch_summary

router = APIRouter()

# In-memory DB for now
log_db = []

@router.get("/")
def get_trip():
    return log_db

@router.post("/")
def create_trip(trip: Trip):
    new_id = len(log_db) + 1
    catch_summary = get_catch_summary(trip)
    new_trip = trip.copy(update={"id": new_id, "catchSummary": catch_summary})    
    log_db.append(new_trip)
    return {"message": "Trip added", "trip": new_trip}

@router.delete("/{trip_id}")
def delete_trip(trip_id: int):
    global log_db
    for i, trip in enumerate(log_db):
        if trip.id == trip_id:
            del log_db[i]
            return {"message": f"Trip {trip_id} deleted"}
    raise HTTPException(status_code=404, detail="Trip not found")