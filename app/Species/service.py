import re
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

import app.Species.data_provider as data_provider
from app.Species.range_reader import kml_to_range_data
from app.Species.schemas import RangeData


def _species_name_to_slug(name: str) -> str:
    """Convert species name to KML filename slug (e.g. 'Acadian Redfish' -> 'acadian_redfish')."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def get_species_range(db: Session, species_id: int) -> RangeData:
    species = data_provider.get_species_by_id(db, species_id)
    if species is None:
        raise ValueError("Species not found")
    slug = _species_name_to_slug(species["name"])
    project_root = Path(__file__).resolve().parent.parent.parent
    kml_path = project_root / "rangeData" / f"{slug}_range.kml"
    if not kml_path.exists():
        raise ValueError("Range data not found for this species")
    content = kml_path.read_text(encoding="utf-8")
    range_data = kml_to_range_data(content)
    if range_data is None or not range_data.polygons:
        raise ValueError("Range data not found for this species")
    return range_data


def get_species(db: Session, user_id: int, kingdom: Optional[str] = None):
    return data_provider.get_species(db, user_id, kingdom=kingdom)


def get_species_by_id(db: Session, species_id: int):
    return data_provider.get_species_by_id(db, species_id)


def get_favorite_species(db: Session, user_id: int, kingdom: Optional[str] = None):
    return data_provider.get_favorite_species(db, user_id, kingdom=kingdom)


def toggle_species_favorite(species_id: int, user_id: int, db: Session):
    species = data_provider.get_species_by_id(db, species_id)
    if species is None:
        raise ValueError("Species not found")
    data_provider.toggle_user_favorite(db, user_id, species_id)
    return data_provider.get_species_by_id(db, species_id, user_id=user_id)
