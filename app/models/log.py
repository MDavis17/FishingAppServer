# app/models/log.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CatchLocation(BaseModel):
    latitude: float
    longitude: float
    latitudeDelta: float
    longitudeDelta: float

class LogEntry(BaseModel):
    id: Optional[int] = None
    dateTime: datetime
    species: str
    waterType: str
    location: CatchLocation
