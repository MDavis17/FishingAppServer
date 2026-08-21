from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class LatLong(BaseModel):
    latitude: float
    longitude: float

class Location(BaseModel):
    coordinates: LatLong
    name: str

class TripSpecies(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str

class Catch(BaseModel):
    id: Optional[int] = None
    trip_id: Optional[int] = None
    dateTime: datetime
    species: str
    waterType: str
    bait: Optional[str] = None
    location: Optional[Location] = None

class Trip(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = None
    date: datetime
    location: Location
    status: str = "Planned"
    targetSpecies: List[TripSpecies] = []
