from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import app.Species.service as service
from app.Auth.database import get_db
from app.Auth.dependencies import get_current_user
from app.Auth.models import User
from app.Species.schemas import RangeData, Species, SpeciesListResponse

router = APIRouter()


@router.get("/", response_model=SpeciesListResponse)
def get_species(
    kingdom: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    all_species = service.get_species(db, current_user.id, kingdom=kingdom)
    favorite_species = service.get_favorite_species(db, current_user.id, kingdom=kingdom)
    return {"species": all_species, "favoriteSpecies": favorite_species}


@router.get("/{species_id}/range", response_model=RangeData)
def get_species_range(species_id: int, db: Session = Depends(get_db)):
    try:
        return service.get_species_range(db, species_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{species_id}/favorite", response_model=Species)
def toggle_species_favorite(
    species_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return service.toggle_species_favorite(species_id, current_user.id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{species_id}", response_model=Species)
def get_species_by_id(species_id: int, db: Session = Depends(get_db)):
    species = service.get_species_by_id(db, species_id)
    if species is None:
        raise HTTPException(status_code=404, detail="Species not found")
    return species
