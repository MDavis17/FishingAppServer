from fastapi import APIRouter, HTTPException
import app.Catch.service as service
from typing import List

router = APIRouter()

@router.delete("/{catch_id}")
def delete_catch(catch_id: int):
    status = service.delete_catch(catch_id)
    if not status:
        raise HTTPException(status_code=404, detail="Catch not found")
    return {"message": f"Catch {catch_id} deleted"}
