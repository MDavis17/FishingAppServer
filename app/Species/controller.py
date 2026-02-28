from fastapi import APIRouter, HTTPException
import app.Species.service as service
from app.Species.schemas import RangeData

router = APIRouter()

@router.get("/")
def get_species():
    all_species = service.get_species()
    favorite_species = service.get_favorite_species()
    return {"species": all_species, "favoriteSpecies": favorite_species}


@router.get("/{species_id}/range", response_model=RangeData)
def get_species_range(species_id: int):
    try:
        return service.get_species_range(species_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{species_id}/favorite")
def toggle_species_favorite(species_id: int):
    try:
        return service.toggle_species_favorite(species_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{species_id}")
def get_species_by_id(species_id: int):
    species = service.get_species_by_id(species_id)
    if species is None:
        raise HTTPException(status_code=404, detail="Species not found")
    return species
