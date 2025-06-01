from fastapi import APIRouter
from app.models.log import Trip

router = APIRouter()

# In-memory DB for now
log_db = []

@router.get("/")
def get_trip():
    return log_db

@router.post("/")
def create_trip(trip: Trip):
    new_id = len(log_db) + 1
    trip_with_id = trip.copy(update={"id": new_id})
    log_db.append(trip_with_id)
    return {"message": "Trip added", "trip": trip_with_id}

@router.delete("/{trip_id}")
def delete_trip(trip_id: int):
    global log_db
    for i, trip in enumerate(log_db):
        if trip.id == trip_id:
            del log_db[i]
            return {"message": f"Trip {trip_id} deleted"}
    raise HTTPException(status_code=404, detail="Trip not found")