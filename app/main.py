from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
# from app.controllers import root_controller
import app.Catch.controller as catch_controller
import app.Trips.controller as trips_controller
import app.Species.controller as species_controller


app = FastAPI()

# Mount static files directory for serving images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include your controller routes
# app.include_router(root_controller.router)
app.include_router(catch_controller.router, prefix="/catch", tags=["catch"])
app.include_router(trips_controller.router, prefix="/trips", tags=["trips"])
app.include_router(species_controller.router, prefix="/species", tags=["species"])

