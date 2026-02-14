from fastapi import APIRouter
import app.Species.service as service

router = APIRouter()

@router.get("/")
def get_species():
    return service.get_species()