from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class Location(BaseModel):
    latitude: float
    longitude: float

class Catch(BaseModel):
    id: Optional[int] = None
    dateTime: datetime
    species: str
    weight: Optional[float]
    length: Optional[float]
    waterType: str
    location: Optional[Location] = None

class Trip(BaseModel):
    id: Optional[int] = None
    date: datetime
    waterType: str
    location: Location
    catchList: List[Catch]
