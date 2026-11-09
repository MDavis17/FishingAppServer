import asyncio
from datetime import datetime, timedelta, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

import app.MarineData.data_provider as data_provider
from app.MarineData.observed_store import (
    get_observed_row,
    row_to_trip_forecast,
    save_observed,
)
from app.MarineData.schemas import (
    AstronomyData,
    BathymetryData,
    HourlyDataPoint,
    HourlyWaterTempPoint,
    KelpBed,
    KelpData,
    MarineConditions,
    MoonPhase,
    TideData,
    TidePrediction,
    TripConditions,
    TripForecast,
    WeatherConditions,
)

_C_TO_F = lambda c: round(c * 9 / 5 + 32, 1)
_MS_TO_MPH = lambda ms: round(ms * 2.237, 1)
_MS_TO_KNOTS = lambda ms: round(ms * 1.944, 2)
_MM_TO_IN = lambda mm: round(mm / 25.4, 3)
_HPA_TO_INHG = lambda hpa: round(hpa * 0.02953, 2)
_M_TO_FT = lambda m: round(m * 3.28084, 1)

_LA = ZoneInfo("America/Los_Angeles")
_FORECAST_MAX_DAYS = 7
_OBSERVED_RECENT_MAX_DAYS = 92

_WMO_DESCRIPTIONS: dict[int, str] = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _weather_code_description(code: int | None) -> str | None:
    if code is None:
        return None
    return _WMO_DESCRIPTIONS.get(code, "Unknown")


def floor_trip_hour_local(dt: datetime) -> str:
    """Floor an instant to the hour in America/Los_Angeles for Open-Meteo."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(_LA)
    floored = local.replace(minute=0, second=0, microsecond=0)
    return floored.strftime("%Y-%m-%dT%H:00")


def floor_trip_hour_utc(dt: datetime) -> datetime:
    """Floor to the Pacific hour, stored as naive UTC for the database."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(_LA)
    floored = local.replace(minute=0, second=0, microsecond=0)
    return floored.astimezone(timezone.utc).replace(tzinfo=None)


def classify_trip_conditions_mode(
    dt: datetime,
) -> Literal["forecast", "observed", "too_far"]:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if dt < now:
        return "observed"
    if dt > now + timedelta(days=_FORECAST_MAX_DAYS):
        return "too_far"
    return "forecast"


def _trip_is_recent_observed(trip_dt: datetime) -> bool:
    if trip_dt.tzinfo is None:
        trip_dt = trip_dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return (now - trip_dt) <= timedelta(days=_OBSERVED_RECENT_MAX_DAYS)


def validate_forecast_datetime(dt: datetime) -> None:
    """Raise ValueError if datetime is outside the allowed forecast window."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if dt < now:
        raise ValueError("Trip time is in the past")
    if dt > now + timedelta(days=_FORECAST_MAX_DAYS):
        raise ValueError(
            f"Forecast is only available within {_FORECAST_MAX_DAYS} days"
        )


def _current_hour_index(hourly_times: list) -> int:
    """Return the index closest to the current hour in Open-Meteo hourly arrays."""
    now_str = datetime.now().strftime("%Y-%m-%dT%H:00")
    try:
        return hourly_times.index(now_str)
    except ValueError:
        return 0


async def get_conditions(lat: float, lon: float) -> MarineConditions:
    station = await data_provider.find_nearest_station(lat, lon)
    station_id = station["id"]

    marine_raw, visibility_raw = await asyncio.gather(
        data_provider.fetch_open_meteo_marine(lat, lon),
        data_provider.fetch_noaa_visibility(station_id),
    )

    result = MarineConditions(
        nearest_station_id=station_id,
        nearest_station_name=station["name"],
    )

    # Build hourly SST series first so water_temp_f is always derived from it,
    # keeping the displayed current value consistent with the chart.
    if marine_raw:
        try:
            times = marine_raw["hourly"]["time"]
            sst_array = marine_raw["hourly"]["sea_surface_temperature"]
            hourly_points = []
            for t, sst_c in zip(times, sst_array):
                point = HourlyWaterTempPoint(time=t)
                if sst_c is not None:
                    point.temperature_f = _C_TO_F(sst_c)
                hourly_points.append(point)
            # Only keep the array if at least one value is non-null
            if any(p.temperature_f is not None for p in hourly_points):
                result.hourly = hourly_points

            # Derive current water temp from the current hour in the same array
            current_idx = _current_hour_index(times)
            if 0 <= current_idx < len(result.hourly):
                result.water_temp_f = result.hourly[current_idx].temperature_f
                result.water_temp_source = "Open-Meteo (satellite SST)"
        except (KeyError, TypeError):
            pass

    # Ocean currents from Open-Meteo
    if marine_raw:
        try:
            times = marine_raw["hourly"]["time"]
            idx = _current_hour_index(times)
            vel_ms = marine_raw["hourly"]["ocean_current_velocity"][idx]
            dir_deg = marine_raw["hourly"]["ocean_current_direction"][idx]
            if vel_ms is not None:
                result.current_velocity_knots = _MS_TO_KNOTS(vel_ms)
            if dir_deg is not None:
                result.current_direction_deg = round(dir_deg, 1)
        except (KeyError, IndexError, TypeError):
            pass

    # Visibility from NOAA
    if visibility_raw and "data" in visibility_raw and visibility_raw["data"]:
        try:
            latest = visibility_raw["data"][-1]["v"]
            result.visibility_nm = float(latest)
        except (KeyError, IndexError, ValueError):
            pass

    return result


async def get_weather(lat: float, lon: float) -> WeatherConditions:
    weather_raw = await data_provider.fetch_open_meteo_weather(lat, lon)

    result = WeatherConditions()
    if not weather_raw:
        return result

    try:
        times = weather_raw["hourly"]["time"]
        idx = _current_hour_index(times)
        hourly = weather_raw["hourly"]

        temp_c = hourly["temperature_2m"][idx]
        if temp_c is not None:
            result.air_temp_f = _C_TO_F(temp_c)

        wind_ms = hourly["wind_speed_10m"][idx]
        if wind_ms is not None:
            result.wind_speed_mph = _MS_TO_MPH(wind_ms)

        gusts_ms = hourly["wind_gusts_10m"][idx]
        if gusts_ms is not None:
            result.wind_gusts_mph = _MS_TO_MPH(gusts_ms)

        wind_dir = hourly["wind_direction_10m"][idx]
        if wind_dir is not None:
            result.wind_direction_deg = round(wind_dir, 1)

        precip_mm = hourly["precipitation"][idx]
        if precip_mm is not None:
            result.precipitation_in = _MM_TO_IN(precip_mm)

        hourly_points = []
        for i, t in enumerate(times):
            point = HourlyDataPoint(time=t)
            try:
                tc = hourly["temperature_2m"][i]
                if tc is not None:
                    point.temperature_f = _C_TO_F(tc)
            except (IndexError, TypeError):
                pass
            try:
                wms = hourly["wind_speed_10m"][i]
                if wms is not None:
                    point.wind_speed_mph = _MS_TO_MPH(wms)
            except (IndexError, TypeError):
                pass
            try:
                gms = hourly["wind_gusts_10m"][i]
                if gms is not None:
                    point.wind_gusts_mph = _MS_TO_MPH(gms)
            except (IndexError, TypeError):
                pass
            try:
                wd = hourly["wind_direction_10m"][i]
                if wd is not None:
                    point.wind_direction_deg = round(wd, 1)
            except (IndexError, TypeError):
                pass
            try:
                pmm = hourly["precipitation"][i]
                if pmm is not None:
                    point.precipitation_in = _MM_TO_IN(pmm)
            except (IndexError, TypeError):
                pass
            hourly_points.append(point)
        result.hourly = hourly_points

    except (KeyError, IndexError, TypeError):
        pass

    try:
        daily = weather_raw["daily"]
        result.sunrise = daily["sunrise"][0]
        result.sunset = daily["sunset"][0]
        temp_max_c = daily["temperature_2m_max"][0]
        temp_min_c = daily["temperature_2m_min"][0]
        if temp_max_c is not None:
            result.air_temp_f_max = _C_TO_F(temp_max_c)
        if temp_min_c is not None:
            result.air_temp_f_min = _C_TO_F(temp_min_c)
    except (KeyError, IndexError):
        pass

    return result


def _parse_trip_hour_from_raws(
    weather_raw: dict,
    marine_raw: dict | None,
    hour_iso: str,
) -> TripForecast:
    result = TripForecast()

    try:
        hourly = weather_raw["hourly"]
        times = hourly["time"]
        idx = 0
        if hour_iso in times:
            idx = times.index(hour_iso)

        temp_c = hourly["temperature_2m"][idx]
        if temp_c is not None:
            result.air_temp_f = _C_TO_F(temp_c)

        codes = hourly.get("weather_code")
        if codes and idx < len(codes):
            result.weather_description = _weather_code_description(codes[idx])

        wind_ms = hourly["wind_speed_10m"][idx]
        if wind_ms is not None:
            result.wind_speed_mph = _MS_TO_MPH(wind_ms)

        gusts_ms = hourly.get("wind_gusts_10m")
        if gusts_ms and idx < len(gusts_ms) and gusts_ms[idx] is not None:
            result.wind_gusts_mph = _MS_TO_MPH(gusts_ms[idx])

        wind_dir = hourly["wind_direction_10m"][idx]
        if wind_dir is not None:
            result.wind_direction_deg = round(wind_dir, 1)

        pressure = hourly.get("pressure_msl")
        if pressure and idx < len(pressure) and pressure[idx] is not None:
            result.pressure_inhg = _HPA_TO_INHG(pressure[idx])
    except (KeyError, IndexError, TypeError):
        pass

    if marine_raw:
        try:
            hourly = marine_raw["hourly"]
            times = hourly["time"]
            idx = 0
            if hour_iso in times:
                idx = times.index(hour_iso)

            sst_c = hourly.get("sea_surface_temperature")
            if sst_c and idx < len(sst_c) and sst_c[idx] is not None:
                result.water_temp_f = _C_TO_F(sst_c[idx])

            wave_m = hourly.get("wave_height")
            if wave_m and idx < len(wave_m) and wave_m[idx] is not None:
                result.surf_height_ft = _M_TO_FT(wave_m[idx])
        except (KeyError, IndexError, TypeError):
            pass

    return result


async def _fetch_trip_hour(
    lat: float,
    lon: float,
    trip_datetime: datetime,
    *,
    observed: bool,
) -> TripForecast:
    hour_iso = floor_trip_hour_local(trip_datetime)

    if observed and not _trip_is_recent_observed(trip_datetime):
        day_iso = hour_iso[:10]
        weather_raw, marine_raw = await asyncio.gather(
            data_provider.fetch_open_meteo_weather_archive_day(lat, lon, day_iso),
            data_provider.fetch_open_meteo_marine_archive_day(lat, lon, day_iso),
        )
    else:
        weather_raw, marine_raw = await asyncio.gather(
            data_provider.fetch_open_meteo_weather_for_hour(lat, lon, hour_iso),
            data_provider.fetch_open_meteo_marine_for_hour(lat, lon, hour_iso),
        )

    if not weather_raw:
        raise RuntimeError("Weather forecast unavailable")

    return _parse_trip_hour_from_raws(weather_raw, marine_raw, hour_iso)


async def get_trip_forecast(
    lat: float, lon: float, trip_datetime: datetime
) -> TripForecast:
    validate_forecast_datetime(trip_datetime)
    return await _fetch_trip_hour(lat, lon, trip_datetime, observed=False)


async def get_trip_conditions(
    lat: float,
    lon: float,
    trip_datetime: datetime,
    db: Session,
) -> TripConditions:
    mode = classify_trip_conditions_mode(trip_datetime)
    if mode == "too_far":
        raise ValueError(
            f"Forecast is only available within {_FORECAST_MAX_DAYS} days"
        )

    if mode == "forecast":
        validate_forecast_datetime(trip_datetime)
        forecast = await _fetch_trip_hour(lat, lon, trip_datetime, observed=False)
        return TripConditions(**forecast.model_dump(), source="forecast")

    hour_utc = floor_trip_hour_utc(trip_datetime)
    cached = get_observed_row(db, lat, lon, hour_utc)
    if cached:
        payload = row_to_trip_forecast(cached)
        return TripConditions(**payload.model_dump(), source="observed")

    forecast = await _fetch_trip_hour(lat, lon, trip_datetime, observed=True)
    save_observed(db, lat, lon, hour_utc, forecast)
    return TripConditions(**forecast.model_dump(), source="observed")


async def get_tides(lat: float, lon: float) -> TideData:
    station = await data_provider.find_nearest_station(lat, lon)
    raw = await data_provider.fetch_noaa_tides(station["id"])

    predictions = []
    if raw and "predictions" in raw:
        for p in raw["predictions"]:
            try:
                predictions.append(
                    TidePrediction(
                        time=p["t"],
                        height_ft=round(float(p["v"]), 2),
                        type=p["type"],
                    )
                )
            except (KeyError, ValueError):
                continue

    return TideData(
        station_id=station["id"],
        station_name=station["name"],
        predictions=predictions,
    )


async def get_astronomy(lat: float, lon: float) -> AstronomyData:
    raw = await data_provider.fetch_usno_astronomy(lat, lon)

    result = AstronomyData()
    if not raw:
        return result

    try:
        sun_data = raw.get("properties", {}).get("data", {})

        result.sunrise = sun_data.get("sundata", [{}])[0].get("time") if sun_data.get("sundata") else None
        result.sunset = None

        # Parse sundata array for specific phenomena
        for item in sun_data.get("sundata", []):
            phen = item.get("phen", "")
            t = item.get("time")
            if phen == "Rise":
                result.sunrise = t
            elif phen == "Set":
                result.sunset = t

        # Moon data
        moon_phase = sun_data.get("curphase")
        moon_illum = sun_data.get("fracillum")
        moonrise = None
        moonset = None
        for item in sun_data.get("moondata", []):
            phen = item.get("phen", "")
            t = item.get("time")
            if phen == "Rise":
                moonrise = t
            elif phen == "Set":
                moonset = t

        result.moon = MoonPhase(
            phase_name=moon_phase,
            illumination_pct=float(moon_illum.strip("%")) if moon_illum else None,
            moonrise=moonrise,
            moonset=moonset,
        )
    except (KeyError, IndexError, AttributeError, ValueError):
        pass

    return result


async def get_bathymetry(lat: float, lon: float) -> BathymetryData:
    raw = await data_provider.fetch_bathymetry(lat, lon)

    depth_m = None
    if raw and raw.get("status") == "OK":
        try:
            elev = raw["results"][0]["elevation"]
            # GEBCO returns negative values for ocean depth
            if elev is not None and elev <= 0:
                depth_m = abs(elev)
        except (KeyError, IndexError):
            pass

    return BathymetryData(latitude=lat, longitude=lon, depth_m=depth_m)


async def get_kelp(lat: float, lon: float, radius_deg: float = 0.05) -> KelpData:
    raw = await data_provider.fetch_kelp_beds(lat, lon, radius_deg)

    beds = []
    if raw and "features" in raw:
        for feature in raw["features"]:
            try:
                attrs = feature["attributes"]
                beds.append(KelpBed(
                    bed_number=int(attrs["KelpBed"]),
                    status=attrs["Status"],
                ))
            except (KeyError, ValueError):
                continue

    return KelpData(kelp_beds=beds, search_radius_deg=radius_deg)
