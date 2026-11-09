from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.MarineData.schemas import TripForecast
from app.models.db_models import ObservedConditions


def round_coords(lat: float, lon: float) -> tuple[float, float]:
    return round(lat, 3), round(lon, 3)


def get_observed_row(
    db: Session,
    lat: float,
    lon: float,
    observed_hour_utc: datetime,
) -> ObservedConditions | None:
    rounded_lat, rounded_lon = round_coords(lat, lon)
    return (
        db.query(ObservedConditions)
        .filter(
            ObservedConditions.latitude == rounded_lat,
            ObservedConditions.longitude == rounded_lon,
            ObservedConditions.observed_hour == observed_hour_utc,
        )
        .first()
    )


def row_to_trip_forecast(row: ObservedConditions) -> TripForecast:
    return TripForecast(
        air_temp_f=row.air_temp_f,
        weather_description=row.weather_description,
        water_temp_f=row.water_temp_f,
        wind_speed_mph=row.wind_speed_mph,
        wind_direction_deg=row.wind_direction_deg,
        wind_gusts_mph=row.wind_gusts_mph,
        pressure_inhg=row.pressure_inhg,
        surf_height_ft=row.surf_height_ft,
    )


def save_observed(
    db: Session,
    lat: float,
    lon: float,
    observed_hour_utc: datetime,
    forecast: TripForecast,
) -> ObservedConditions:
    rounded_lat, rounded_lon = round_coords(lat, lon)
    row = ObservedConditions(
        latitude=rounded_lat,
        longitude=rounded_lon,
        observed_hour=observed_hour_utc,
        air_temp_f=forecast.air_temp_f,
        weather_description=forecast.weather_description,
        water_temp_f=forecast.water_temp_f,
        wind_speed_mph=forecast.wind_speed_mph,
        wind_direction_deg=forecast.wind_direction_deg,
        wind_gusts_mph=forecast.wind_gusts_mph,
        pressure_inhg=forecast.pressure_inhg,
        surf_height_ft=forecast.surf_height_ft,
        captured_at=datetime.utcnow(),
    )
    db.add(row)
    try:
        db.commit()
        db.refresh(row)
        return row
    except IntegrityError:
        db.rollback()
        existing = get_observed_row(db, lat, lon, observed_hour_utc)
        if existing is None:
            raise
        return existing
