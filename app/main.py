from fastapi import FastAPI
# from app.controllers import root_controller
import app.Catch.controller as catch_controller
import app.Trips.controller as trips_controller


app = FastAPI()

# Include your controller routes
# app.include_router(root_controller.router)
app.include_router(catch_controller.router, prefix="/catch", tags=["catch"])
app.include_router(trips_controller.router, prefix="/trips", tags=["trips"])

