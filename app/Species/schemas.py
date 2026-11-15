from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


class SpeciesImage(BaseModel):
    url: str
    label: str


class Species(BaseModel):
    id: int
    name: str
    scientificName: str
    region: List[str]
    image: str
    images: Optional[List[SpeciesImage]] = None
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


class MonthlyCatchCount(BaseModel):
    month: int
    label: str
    count: int


class SpeciesCatchHistory(BaseModel):
    totalCatches: int
    personalBest: Optional[SpeciesCatchHistoryItem] = None
    mostRecentCatch: Optional[SpeciesCatchHistoryItem] = None
    catches: List[SpeciesCatchHistoryItem] = []
    monthlyCounts: List[MonthlyCatchCount] = []


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
