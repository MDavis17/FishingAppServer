import re
from pathlib import Path
from typing import Optional

import app.Species.data_provider as data_provider
from app.Species.range_reader import kml_to_range_data
from app.Species.schemas import RangeData


def _species_name_to_slug(name: str) -> str:
    """Convert species name to KML filename slug (e.g. 'Acadian Redfish' -> 'acadian_redfish')."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def get_species_range(species_id: int) -> RangeData:
    species = data_provider.get_species_by_id(species_id)
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


def get_species(kingdom: Optional[str] = None):
    return data_provider.get_species(kingdom=kingdom)

def get_species_by_id(species_id: int):
    return data_provider.get_species_by_id(species_id)

def get_favorite_species(kingdom: Optional[str] = None):
    return data_provider.get_favorite_species(kingdom=kingdom)

def toggle_species_favorite(species_id: int):
    updated = data_provider.toggle_species_favorite(species_id)
    if updated is None:
        raise ValueError("Species not found")
    return updated
