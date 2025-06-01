from fastapi import FastAPI
# from app.controllers import root_controller
from app.controllers import logs_controller
from app.controllers import trips_controller


app = FastAPI()

# Include your controller routes
# app.include_router(root_controller.router)
app.include_router(logs_controller.router, prefix="/catchLog", tags=["catchLog"])
app.include_router(trips_controller.router, prefix="/trips", tags=["trips"])

