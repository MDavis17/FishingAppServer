import httpx
import math
import time
import asyncio
import logging
from datetime import date, datetime
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# NOAA station cache
# ---------------------------------------------------------------------------

_station_cache: List[Dict[str, Any]] = []
_station_cache_timestamp: float = 0.0
_STATION_CACHE_TTL_SECONDS = 86400  # 24 hours

# Fallback CA stations if the metadata API is unavailable
_FALLBACK_STATIONS = [
    {"id": "9418767", "name": "North Spit, Humboldt Bay", "lat": 40.7697, "lng": -124.2172},
    {"id": "9415020", "name": "Point Reyes", "lat": 37.9953, "lng": -122.9764},
    {"id": "9414290", "name": "San Francisco", "lat": 37.8063, "lng": -122.4659},
    {"id": "9413450", "name": "Monterey", "lat": 36.6050, "lng": -121.8883},
    {"id": "9412110", "name": "Port San Luis", "lat": 35.1693, "lng": -120.7542},
    {"id": "9411340", "name": "Santa Barbara", "lat": 34.4046, "lng": -119.6886},
    {"id": "9410660", "name": "Los Angeles", "lat": 33.7200, "lng": -118.2717},
    {"id": "9410230", "name": "La Jolla, San Diego", "lat": 32.8670, "lng": -117.2570},
    {"id": "9410170", "name": "San Diego", "lat": 32.7142, "lng": -117.1736},
]

_station_cache_lock = asyncio.Lock()


async def _load_station_cache() -> None:
    global _station_cache, _station_cache_timestamp
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json",
                params={"type": "waterlevels", "state": "CA"},
            )
            resp.raise_for_status()
            data = resp.json()
            stations = data.get("stations", [])
            _station_cache = [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "lat": s["lat"],
                    "lng": s["lng"],
                }
                for s in stations
                if "lat" in s and "lng" in s and "id" in s
            ]
            _station_cache_timestamp = time.time()
            logger.info("Loaded %d CA NOAA stations into cache", len(_station_cache))
    except Exception as exc:
        logger.warning("Failed to load NOAA station cache, using fallback: %s", exc)
        if not _station_cache:
            _station_cache = _FALLBACK_STATIONS
            _station_cache_timestamp = time.time()


async def _get_stations() -> List[Dict[str, Any]]:
    async with _station_cache_lock:
        if not _station_cache or (time.time() - _station_cache_timestamp) > _STATION_CACHE_TTL_SECONDS:
            await _load_station_cache()
    return _station_cache


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def find_nearest_station(lat: float, lon: float) -> Dict[str, Any]:
    stations = await _get_stations()
    nearest = min(stations, key=lambda s: _haversine_km(lat, lon, s["lat"], s["lng"]))
    return nearest


# ---------------------------------------------------------------------------
# Simple in-memory response cache
# ---------------------------------------------------------------------------

_response_cache: Dict[str, Any] = {}
_RESPONSE_TTL: Dict[str, int] = {
    "marine": 1800,      # 30 min
    "weather": 1800,
    "tides": 3600,       # 1 hour
    "water_temp": 1800,
    "visibility": 1800,
    "astronomy": 86400,  # 24 hours (changes daily)
    "bathymetry": 604800, # 1 week (static data)
    "kelp": 86400,
}


def _cache_get(key: str) -> Optional[Any]:
    entry = _response_cache.get(key)
    if entry and (time.time() - entry["ts"]) < entry["ttl"]:
        return entry["data"]
    return None


def _cache_set(key: str, data: Any, ttl: int) -> None:
    _response_cache[key] = {"data": data, "ts": time.time(), "ttl": ttl}


# ---------------------------------------------------------------------------
# Open-Meteo: Marine (SST + currents)
# ---------------------------------------------------------------------------

async def fetch_open_meteo_marine(lat: float, lon: float) -> Optional[Dict]:
    cache_key = f"marine:{lat:.3f}:{lon:.3f}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://marine-api.open-meteo.com/v1/marine",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "hourly": "sea_surface_temperature,ocean_current_velocity,ocean_current_direction",
                    "timezone": "America/Los_Angeles",
                    "forecast_days": 1,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            _cache_set(cache_key, data, _RESPONSE_TTL["marine"])
            return data
    except Exception as exc:
        logger.warning("Open-Meteo marine fetch failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Open-Meteo: Weather (air temp, wind, rain, sunrise/sunset)
# ---------------------------------------------------------------------------

async def fetch_open_meteo_weather(lat: float, lon: float) -> Optional[Dict]:
    cache_key = f"weather:{lat:.3f}:{lon:.3f}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "hourly": "temperature_2m,precipitation,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                    "daily": "sunrise,sunset",
                    "timezone": "America/Los_Angeles",
                    "forecast_days": 1,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            _cache_set(cache_key, data, _RESPONSE_TTL["weather"])
            return data
    except Exception as exc:
        logger.warning("Open-Meteo weather fetch failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# NOAA CO-OPS: Tide predictions
# ---------------------------------------------------------------------------

async def fetch_noaa_tides(station_id: str, start_date: Optional[str] = None) -> Optional[Dict]:
    today = start_date or date.today().strftime("%Y%m%d")
    cache_key = f"tides:{station_id}:{today}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
                params={
                    "begin_date": today,
                    "range": 48,
                    "station": station_id,
                    "product": "predictions",
                    "datum": "MLLW",
                    "time_zone": "lst_ldt",
                    "interval": "hilo",
                    "units": "english",
                    "format": "json",
                    "application": "CAFishingApp",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            _cache_set(cache_key, data, _RESPONSE_TTL["tides"])
            return data
    except Exception as exc:
        logger.warning("NOAA tides fetch failed for station %s: %s", station_id, exc)
        return None


# ---------------------------------------------------------------------------
# NOAA CO-OPS: Water temperature (observed)
# ---------------------------------------------------------------------------

async def fetch_noaa_water_temp(station_id: str) -> Optional[Dict]:
    cache_key = f"water_temp:{station_id}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
                params={
                    "date": "today",
                    "station": station_id,
                    "product": "water_temperature",
                    "units": "english",
                    "time_zone": "lst_ldt",
                    "format": "json",
                    "application": "CAFishingApp",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" not in data:
                _cache_set(cache_key, data, _RESPONSE_TTL["water_temp"])
                return data
            return None
    except Exception as exc:
        logger.warning("NOAA water_temperature fetch failed for station %s: %s", station_id, exc)
        return None


# ---------------------------------------------------------------------------
# NOAA CO-OPS: Visibility (atmospheric, nautical miles)
# ---------------------------------------------------------------------------

async def fetch_noaa_visibility(station_id: str) -> Optional[Dict]:
    cache_key = f"visibility:{station_id}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
                params={
                    "date": "today",
                    "station": station_id,
                    "product": "visibility",
                    "units": "english",
                    "time_zone": "lst_ldt",
                    "format": "json",
                    "application": "CAFishingApp",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" not in data:
                _cache_set(cache_key, data, _RESPONSE_TTL["visibility"])
                return data
            return None
    except Exception as exc:
        logger.warning("NOAA visibility fetch failed for station %s: %s", station_id, exc)
        return None


# ---------------------------------------------------------------------------
# USNO: Moon phase + sunrise/sunset
# ---------------------------------------------------------------------------

async def fetch_usno_astronomy(lat: float, lon: float, query_date: Optional[str] = None) -> Optional[Dict]:
    today = query_date or date.today().strftime("%Y-%m-%d")
    cache_key = f"astronomy:{lat:.3f}:{lon:.3f}:{today}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://aa.usno.navy.mil/api/rstt/oneday",
                params={
                    "date": today,
                    "coords": f"{lat},{lon}",
                    "tz": -8,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            _cache_set(cache_key, data, _RESPONSE_TTL["astronomy"])
            return data
    except Exception as exc:
        logger.warning("USNO astronomy fetch failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Open Topo Data: Bathymetry (GEBCO)
# ---------------------------------------------------------------------------

async def fetch_bathymetry(lat: float, lon: float) -> Optional[Dict]:
    cache_key = f"bathymetry:{lat:.4f}:{lon:.4f}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.opentopodata.org/v1/gebco2020",
                params={"locations": f"{lat},{lon}"},
            )
            resp.raise_for_status()
            data = resp.json()
            _cache_set(cache_key, data, _RESPONSE_TTL["bathymetry"])
            return data
    except Exception as exc:
        logger.warning("Open Topo Data bathymetry fetch failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# CDFW: Kelp beds (Administrative Kelp Beds FeatureServer)
# ---------------------------------------------------------------------------

async def fetch_kelp_beds(lat: float, lon: float, radius_deg: float = 0.05) -> Optional[Dict]:
    cache_key = f"kelp:{lat:.3f}:{lon:.3f}:{radius_deg}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    bbox = f"{lon - radius_deg},{lat - radius_deg},{lon + radius_deg},{lat + radius_deg}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://services2.arcgis.com/Uq9r85Potqm3MfRV/arcgis/rest/services/biosds3135_fpu/FeatureServer/0/query",
                params={
                    "where": "1=1",
                    "geometry": bbox,
                    "geometryType": "esriGeometryEnvelope",
                    "inSR": "4326",
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "KelpBed,Status",
                    "returnGeometry": "false",
                    "f": "json",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            _cache_set(cache_key, data, _RESPONSE_TTL["kelp"])
            return data
    except Exception as exc:
        logger.warning("CDFW kelp beds fetch failed: %s", exc)
        return None
