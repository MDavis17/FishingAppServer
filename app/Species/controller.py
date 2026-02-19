from fastapi import APIRouter, HTTPException
import app.Species.service as service

router = APIRouter()

@router.get("/")
def get_species():
    all_species = service.get_species()
    favorite_species = service.get_favorite_species()
    return {"species": all_species, "favoriteSpecies": favorite_species}

@router.put("/{species_id}/favorite")
def toggle_species_favorite(species_id: int):
    try:
        return service.toggle_species_favorite(species_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

