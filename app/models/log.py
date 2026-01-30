from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class LatLong(BaseModel):
    latitude: float
    longitude: float

class Location(BaseModel):
    coordinates: LatLong
    name: str

class Catch(BaseModel):
    id: Optional[int] = None
    trip_id: Optional[int] = None
    dateTime: datetime
    species: str
    waterType: str
    location: Optional[Location] = None

class Trip(BaseModel):
    id: Optional[int] = None
    date: datetime
    waterType: str
    location: Location
    status: str
