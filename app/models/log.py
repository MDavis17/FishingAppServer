from enum import Enum
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional


class TripStatus(str, Enum):
    Planned = "Planned"
    Completed = "Completed"


class TripType(str, Enum):
    Surf = "Surf"
    Kayak = "Kayak"
    Boat = "Boat"
    Spearfishing = "Spearfishing"
    Pier = "Pier"
    FreeDiving = "Free Diving"
    Crabbing = "Crabbing"
    RockJetty = "Rock/Jetty"
    FlyFishing = "Fly Fishing"


class LatLong(BaseModel):
    latitude: float
    longitude: float

class Location(BaseModel):
    coordinates: LatLong
    name: str

class Species(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str

class Catch(BaseModel):
    id: Optional[int] = None
    trip_id: Optional[int] = None
    user_id: Optional[int] = None
    dateTime: datetime
    species: str
    waterType: str
    bait: Optional[str] = None
    location: Optional[Location] = None
    length: Optional[float] = None

class Trip(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = None
    user_id: Optional[int] = None
    date: datetime
    createdAt: Optional[datetime] = None
    location: Location
    status: Optional[TripStatus] = None
    tripType: TripType
    targetSpecies: List[Species] = []
    notes: Optional[str] = None


class TripNotesUpdate(BaseModel):
    notes: Optional[str] = None


class CatchStat(BaseModel):
    type: str
    value: int | float | bool


class IndividualCatch(BaseModel):
    id: int
    time: str
    length: Optional[float] = None
    bait: Optional[str] = None


class SpeciesGroup(BaseModel):
    species: str
    speciesImage: Optional[str] = None
    count: int
    largestLength: Optional[float] = None
    catches: List[IndividualCatch]


class TripCatchListResponse(BaseModel):
    stats: List[CatchStat]
    speciesGroups: List[SpeciesGroup]
