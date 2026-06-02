import asyncio
import logging
from datetime import datetime
from typing import Optional

import app.MarineData.data_provider as data_provider
from app.MarineData.schemas import (
    AstronomyData,
    BathymetryData,
    HourlyDataPoint,
    KelpBed,
    KelpData,
    MarineConditions,
    MoonPhase,
    TideData,
    TidePrediction,
    WeatherConditions,
)

logger = logging.getLogger(__name__)

_C_TO_F = lambda c: round(c * 9 / 5 + 32, 1)
_MS_TO_MPH = lambda ms: round(ms * 2.237, 1)
_MS_TO_KNOTS = lambda ms: round(ms * 1.944, 2)
_MM_TO_IN = lambda mm: round(mm / 25.4, 3)


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

    marine_raw, water_temp_raw, visibility_raw = await asyncio.gather(
        data_provider.fetch_open_meteo_marine(lat, lon),
        data_provider.fetch_noaa_water_temp(station_id),
        data_provider.fetch_noaa_visibility(station_id),
    )

    result = MarineConditions(
        nearest_station_id=station_id,
        nearest_station_name=station["name"],
    )

    # Water temp: prefer NOAA observed, fall back to Open-Meteo SST
    if water_temp_raw and "data" in water_temp_raw and water_temp_raw["data"]:
        try:
            latest = water_temp_raw["data"][-1]["v"]
            result.water_temp_f = float(latest)
            result.water_temp_source = f"NOAA {station['name']}"
        except (KeyError, IndexError, ValueError):
            pass

    if result.water_temp_f is None and marine_raw:
        try:
            times = marine_raw["hourly"]["time"]
            idx = _current_hour_index(times)
            sst_c = marine_raw["hourly"]["sea_surface_temperature"][idx]
            if sst_c is not None:
                result.water_temp_f = _C_TO_F(sst_c)
                result.water_temp_source = "Open-Meteo (satellite SST)"
        except (KeyError, IndexError, TypeError):
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
