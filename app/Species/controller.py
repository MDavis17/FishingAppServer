from fastapi import APIRouter, HTTPException
import app.Species.service as service

router = APIRouter()

@router.get("/")
def get_species():
    return service.get_species()

@router.put("/{species_id}/favorite")
def toggle_species_favorite(species_id: int):
    try:
        return service.toggle_species_favorite(species_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

