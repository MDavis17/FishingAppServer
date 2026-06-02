from pydantic import BaseModel
from typing import List, Optional


class MarineConditions(BaseModel):
    water_temp_f: Optional[float] = None
    water_temp_source: Optional[str] = None
    current_velocity_knots: Optional[float] = None
    current_direction_deg: Optional[float] = None
    visibility_nm: Optional[float] = None
    nearest_station_id: Optional[str] = None
    nearest_station_name: Optional[str] = None


class HourlyDataPoint(BaseModel):
    time: str
    temperature_f: Optional[float] = None
    wind_speed_mph: Optional[float] = None
    wind_gusts_mph: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    precipitation_in: Optional[float] = None


class WeatherConditions(BaseModel):
    air_temp_f: Optional[float] = None
    air_temp_f_min: Optional[float] = None
    air_temp_f_max: Optional[float] = None
    wind_speed_mph: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    wind_gusts_mph: Optional[float] = None
    precipitation_in: Optional[float] = None
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    hourly: List[HourlyDataPoint] = []


class TidePrediction(BaseModel):
    time: str
    height_ft: float
    type: str  # "H" or "L"


class TideData(BaseModel):
    station_id: str
    station_name: str
    predictions: List[TidePrediction]


class MoonPhase(BaseModel):
    phase_name: Optional[str] = None
    illumination_pct: Optional[float] = None
    moonrise: Optional[str] = None
    moonset: Optional[str] = None


class AstronomyData(BaseModel):
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    moon: Optional[MoonPhase] = None


class BathymetryData(BaseModel):
    latitude: float
    longitude: float
    depth_m: Optional[float] = None


class KelpBed(BaseModel):
    bed_number: int
    status: str


class KelpData(BaseModel):
    kelp_beds: List[KelpBed]
    search_radius_deg: float = 0.05
