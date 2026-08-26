from pydantic import BaseModel, ConfigDict, Field
from typing import List


class Species(BaseModel):
    id: int
    name: str
    region: List[str]
    image: str
    isFavorite: bool


class SpeciesListResponse(BaseModel):
    species: List[Species]
    favoriteSpecies: List[Species]


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
