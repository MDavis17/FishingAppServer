from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import app.Catch.service as service
from app.Auth.database import get_db
from app.Auth.dependencies import get_current_user
from app.Auth.models import User

router = APIRouter()


@router.delete("/{catch_id}")
def delete_catch(
    catch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    status = service.delete_catch(db, catch_id, current_user.id)
    if not status:
        raise HTTPException(status_code=404, detail="Catch not found")
    return {"message": f"Catch {catch_id} deleted"}
