from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.Auth.database import Base

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
    location_name = Column(String, nullable=False, default="")
    location_lat = Column(Float, nullable=False)
    location_lng = Column(Float, nullable=False)

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
