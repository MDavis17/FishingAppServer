from typing import Optional

from fastapi import APIRouter, HTTPException
import app.Species.service as service
from app.Species.schemas import RangeData, Species, SpeciesListResponse

router = APIRouter()

@router.get("/", response_model=SpeciesListResponse)
def get_species(kingdom: Optional[str] = None):
    all_species = service.get_species(kingdom=kingdom)
    favorite_species = service.get_favorite_species(kingdom=kingdom)
    return {"species": all_species, "favoriteSpecies": favorite_species}


@router.get("/{species_id}/range", response_model=RangeData)
def get_species_range(species_id: int):
    try:
        return service.get_species_range(species_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{species_id}/favorite", response_model=Species)
def toggle_species_favorite(species_id: int):
    try:
        return service.toggle_species_favorite(species_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{species_id}", response_model=Species)
def get_species_by_id(species_id: int):
    species = service.get_species_by_id(species_id)
    if species is None:
        raise HTTPException(status_code=404, detail="Species not found")
    return species
