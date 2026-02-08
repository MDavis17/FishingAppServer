from fastapi import APIRouter
import app.Species.service as service

router = APIRouter()

@router.get("/")
def get_species():
    return service.get_species()

@router.get("/saltwater")
def get_saltwater_species():
    return service.get_saltwater_species()

@router.get("/freshwater")
def get_freshwater_species():
    return service.get_freshwater_species()