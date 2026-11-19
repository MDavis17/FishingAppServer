"""Seed regions and species reference data from mock_db into PostgreSQL/SQLite."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.Auth.database import SessionLocal
from app.mock_database.mock_db import species_db
from app.models.db_models import Region, Species, SpeciesGroup
from scripts.species_images import load_uploaded_url_map, resolve_species_image_url

REGION_NAMES = ("North Coast", "Central Coast", "South Coast")


def seed() -> None:
    url_map = load_uploaded_url_map()
    db = SessionLocal()
    try:
        region_by_name: dict[str, Region] = {}
        for name in REGION_NAMES:
            region = db.query(Region).filter(Region.name == name).first()
            if region is None:
                region = Region(name=name)
                db.add(region)
                db.flush()
            region_by_name[name] = region

        group_by_name: dict[str, SpeciesGroup] = {}
        for entry in species_db:
            group_name = entry.get("group")
            if not group_name or group_name in group_by_name:
                continue
            group_row = (
                db.query(SpeciesGroup).filter(SpeciesGroup.name == group_name).first()
            )
            if group_row is None:
                group_row = SpeciesGroup(name=group_name)
                db.add(group_row)
                db.flush()
            group_by_name[group_name] = group_row

        seen_names: set[str] = set()
        for entry in species_db:
            name = entry["name"]
            if name in seen_names:
                continue
            seen_names.add(name)

            row = db.query(Species).filter(Species.name == name).first()
            if row is None:
                row = Species()
                db.add(row)

            row.name = name
            row.scientific_name = entry.get("scientificName") or ""
            row.avg_length = entry.get("avgLength") or ""
            row.length_units = entry.get("lengthUnits")
            row.lifespan = entry.get("lifespan") or ""
            row.depth_range = entry.get("depthRange") or ""
            row.image = resolve_species_image_url(entry.get("image") or "", url_map)
            row.kingdom = entry.get("kingdom") or "animal"

            group_name = entry.get("group")
            if group_name:
                group_row = group_by_name.get(group_name)
                if group_row is None:
                    group_row = (
                        db.query(SpeciesGroup)
                        .filter(SpeciesGroup.name == group_name)
                        .first()
                    )
                row.group_id = group_row.id if group_row else None
            else:
                row.group_id = None

            gallery = entry.get("images")
            if gallery:
                resolved_gallery = []
                for item in gallery:
                    if not isinstance(item, dict):
                        continue
                    label = item.get("label")
                    source = item.get("image") or item.get("url") or ""
                    url = resolve_species_image_url(source, url_map)
                    if url and label:
                        resolved_gallery.append({"url": url, "label": label})
                row.images = resolved_gallery if resolved_gallery else None
            else:
                row.images = None

            row.regions.clear()
            for region_name in entry.get("region") or []:
                region = region_by_name.get(region_name)
                if region is not None:
                    row.regions.append(region)

        db.commit()
        species_count = db.query(Species).count()
        group_count = db.query(SpeciesGroup).count()
        print(
            f"Seeded {species_count} species, {group_count} groups, "
            f"and {len(REGION_NAMES)} regions."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()