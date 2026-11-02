from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


class Species(BaseModel):
    id: int
    name: str
    scientificName: str
    region: List[str]
    image: str
    isFavorite: bool
    kingdom: str
    avgLength: str
    lengthUnits: Optional[str] = None
    lifespan: str
    depthRange: str

class SpeciesListResponse(BaseModel):
    species: List[Species]
    favoriteSpecies: List[Species]


class SpeciesCatchHistoryItem(BaseModel):
    id: int
    dateTime: datetime
    length: Optional[float] = None
    weight: Optional[float] = None


class SpeciesCatchHistory(BaseModel):
    totalCatches: int
    largestLength: Optional[float] = None
    mostRecentCatchDate: Optional[datetime] = None
    catches: List[SpeciesCatchHistoryItem] = []


class LatLng(BaseModel):
    latitude: float
    longitude: float


class RangePolygon(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    coordinates: List[LatLng]
    occurrence_probability: float = Field(alias="occurrenceProbability")


class RangeData(BaseModel):
    polygons: List[RangePolygon]
    centerLatitude: float = 0.0
    centerLongitude: float = 0.0
    latDelta: float = 0.0
    lngDelta: float = 0.0
