from fastapi import APIRouter
from app.models.log import LogEntry

router = APIRouter()

# In-memory DB for now
log_db = []

@router.get("/")
def get_logs():
    return log_db

@router.post("/")
def create_log(entry: LogEntry):
    new_id = len(log_db) + 1
    entry_with_id = entry.copy(update={"id": new_id})
    log_db.append(entry_with_id)
    return {"message": "Log entry added", "entry": entry_with_id}