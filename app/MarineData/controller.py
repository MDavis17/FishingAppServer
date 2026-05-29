from fastapi import APIRouter, HTTPException, Query
import app.MarineData.service as service
from app.MarineData.schemas import (
    AstronomyData,
    BathymetryData,
    KelpData,
    MarineConditions,
    TideData,
    WeatherConditions,
)

router = APIRouter()

CA_LAT_RANGE = (32.5, 42.0)
CA_LON_RANGE = (-124.5, -117.0)


def _validate_ca_coords(lat: float, lon: float) -> None:
    if not (CA_LAT_RANGE[0] <= lat <= CA_LAT_RANGE[1]):
        raise HTTPException(status_code=400, detail=f"Latitude {lat} is outside California coastal range ({CA_LAT_RANGE[0]}–{CA_LAT_RANGE[1]})")
    if not (CA_LON_RANGE[0] <= lon <= CA_LON_RANGE[1]):
        raise HTTPException(status_code=400, detail=f"Longitude {lon} is outside California coastal range ({CA_LON_RANGE[0]}–{CA_LON_RANGE[1]})")


@router.get("/conditions", response_model=MarineConditions)
async def get_conditions(
    latitude: float = Query(..., description="Latitude (California coast: 32.5–42.0)"),
    longitude: float = Query(..., description="Longitude (California coast: -124.5 to -117.0)"),
):
    """Current water temperature, ocean currents, and visibility near the given coordinates."""
    _validate_ca_coords(latitude, longitude)
    try:
        return await service.get_conditions(latitude, longitude)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch marine conditions: {exc}")


@router.get("/weather", response_model=WeatherConditions)
async def get_weather(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
):
    """Air temperature, wind, precipitation, and sunrise/sunset for the given coordinates."""
    _validate_ca_coords(latitude, longitude)
    try:
        return await service.get_weather(latitude, longitude)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch weather: {exc}")


@router.get("/tides", response_model=TideData)
async def get_tides(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
):
    """Tide predictions (high/low) for the nearest NOAA station over the next 48 hours."""
    _validate_ca_coords(latitude, longitude)
    try:
        return await service.get_tides(latitude, longitude)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch tide data: {exc}")


@router.get("/astronomy", response_model=AstronomyData)
async def get_astronomy(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
):
    """Moon phase, illumination, moonrise/moonset, and sunrise/sunset."""
    _validate_ca_coords(latitude, longitude)
    try:
        return await service.get_astronomy(latitude, longitude)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch astronomy data: {exc}")


@router.get("/bathymetry", response_model=BathymetryData)
async def get_bathymetry(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
):
    """Ocean depth (meters) at the given coordinates via GEBCO bathymetry."""
    _validate_ca_coords(latitude, longitude)
    try:
        return await service.get_bathymetry(latitude, longitude)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch bathymetry: {exc}")


@router.get("/kelp", response_model=KelpData)
async def get_kelp(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    radius_deg: float = Query(0.05, description="Search radius in degrees (~3–5 miles)"),
):
    """CDFW administrative kelp beds within the given radius of the coordinates."""
    _validate_ca_coords(latitude, longitude)
    try:
        return await service.get_kelp(latitude, longitude, radius_deg)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch kelp data: {exc}")
