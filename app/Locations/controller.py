from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import app.Locations.service as service
from app.Auth.database import get_db
from app.Auth.dependencies import get_current_user
from app.Auth.models import User
from app.models.log import SavedLocationCreate

router = APIRouter()


def _validate_create(body: SavedLocationCreate) -> None:
    if not (body.location.name and body.location.name.strip()):
        raise HTTPException(
            status_code=400, detail="Location name is required",
        )
    if body.notes is not None and len(body.notes) > service.SAVED_LOCATION_NOTES_MAX_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Notes must be at most {service.SAVED_LOCATION_NOTES_MAX_LENGTH} characters",
        )


@router.get("/")
def get_saved_locations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.list_saved_locations(db, current_user.id)


@router.post("/")
def save_location(
    body: SavedLocationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_create(body)
    saved = service.create_saved_location(db, body, current_user.id)
    return {
        "message": "Location saved",
        "location": saved.model_dump(mode="json"),
    }