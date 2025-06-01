from fastapi import APIRouter
from app.models.log import Catch

router = APIRouter()

# In-memory DB for now
log_db = []

@router.get("/")
def get_logs():
    return log_db

@router.post("/")
def create_log(entry: Catch):
    new_id = len(log_db) + 1
    entry_with_id = entry.copy(update={"id": new_id})
    log_db.append(entry_with_id)
    return {"message": "Log entry added", "entry": entry_with_id}

@router.delete("/{entry_id}")
def delete_log(entry_id: int):
    global log_db
    for i, entry in enumerate(log_db):
        if entry.id == entry_id:
            del log_db[i]
            return {"message": f"Log entry {entry_id} deleted"}
    raise HTTPException(status_code=404, detail="Log entry not found")