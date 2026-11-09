from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
)
from sqlalchemy.orm import relationship

from app.Auth.database import Base
from app.models.log import TripType

species_regions = Table(
    "species_regions",
    Base.metadata,
    Column("species_id", ForeignKey("species.id", ondelete="CASCADE"), primary_key=True),
    Column("region_id", ForeignKey("regions.id", ondelete="CASCADE"), primary_key=True),
)

trip_target_species = Table(
    "trip_target_species",
    Base.metadata,
    Column("trip_id", ForeignKey("trips.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "species_id",
        ForeignKey("species.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)

    species = relationship(
        "Species",
        secondary=species_regions,
        back_populates="regions",
    )


class Species(Base):
    __tablename__ = "species"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    scientific_name = Column(String, nullable=True)
    avg_length = Column(String, nullable=True, default="")
    length_units = Column(String, nullable=True)
    lifespan = Column(String, nullable=True, default="")
    depth_range = Column(String, nullable=True, default="")
    image = Column(String, nullable=False, default="")
    images = Column(JSON, nullable=True)
    kingdom = Column(String, nullable=False, default="animal", index=True)

    regions = relationship(
        "Region",
        secondary=species_regions,
        back_populates="species",
    )
    targeted_trips = relationship(
        "Trip",
        secondary=trip_target_species,
        back_populates="target_species",
    )


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, nullable=False, default="Planned")
    trip_type = Column(
        SAEnum(
            TripType,
            name="trip_type",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=TripType.Surf,
    )
    location_name = Column(String, nullable=False, default="")
    location_lat = Column(Float, nullable=False)
    location_lng = Column(Float, nullable=False)
    notes = Column(String(800), nullable=True)

    catches = relationship(
        "CatchEntry",
        back_populates="trip",
        cascade="all, delete-orphan",
    )
    target_species = relationship(
        "Species",
        secondary=trip_target_species,
        back_populates="targeted_trips",
    )


class ObservedConditions(Base):
    __tablename__ = "observed_conditions"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    observed_hour = Column(DateTime, nullable=False)
    air_temp_f = Column(Float, nullable=True)
    weather_description = Column(String, nullable=True)
    water_temp_f = Column(Float, nullable=True)
    wind_speed_mph = Column(Float, nullable=True)
    wind_direction_deg = Column(Float, nullable=True)
    wind_gusts_mph = Column(Float, nullable=True)
    pressure_inhg = Column(Float, nullable=True)
    surf_height_ft = Column(Float, nullable=True)
    captured_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CatchEntry(Base):
    __tablename__ = "catches"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date_time = Column(DateTime, nullable=False)
    species = Column(String, nullable=False)
    water_type = Column(String, nullable=False)
    bait = Column(String, nullable=True)
    location_name = Column(String, nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    length = Column(Float, nullable=True)

    trip = relationship("Trip", back_populates="catches")
