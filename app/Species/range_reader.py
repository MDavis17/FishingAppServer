from typing import Optional

import xml.etree.ElementTree as ET

from app.Species.schemas import LatLng, RangeData, RangePolygon

KML_NS = "http://www.opengis.net/kml/2.2"


def _tag(local: str) -> str:
    return f"{{{KML_NS}}}{local}"


def _probability_from_placemark_name(name: Optional[str]) -> float:
    """Map Placemark name (e.g. '... – Low (0.00–0.33)') to occurrence probability."""
    if not name:
        return 0.5
    name_lower = name.lower()
    if "low" in name_lower and "0.00" in name_lower:
        return 0.165
    if "mid" in name_lower and "0.34" in name_lower:
        return 0.5
    if "high" in name_lower and "0.66" in name_lower:
        return 0.83
    return 0.5


def _parse_coordinates(text: str) -> list[LatLng]:
    """Parse KML coordinates string 'lon,lat,alt lon,lat,alt ...' into list of LatLng."""
    points: list[LatLng] = []
    for part in text.split():
        part = part.strip()
        if not part:
            continue
        vals = part.split(",")
        if len(vals) >= 2:
            try:
                lon = float(vals[0])
                lat = float(vals[1])
                points.append(LatLng(latitude=lat, longitude=lon))
            except ValueError:
                continue
    return points


def _bounding_window(polygons: list) -> tuple:
    """
    Compute center and deltas from all polygon coordinates.
    Handles ranges that span the Pacific (date line): uses the smaller longitude arc
    so the map center stays in the ocean where the data is, not in Europe/Atlantic.
    Returns (center_lat, center_lon, lat_delta, lng_delta).
    """
    if not polygons:
        return (0.0, 0.0, 0.0, 0.0)
    min_lat = min_lon = float("inf")
    max_lat = max_lon = float("-inf")
    lons = []
    for poly in polygons:
        for pt in poly.coordinates:
            min_lat = min(min_lat, pt.latitude)
            max_lat = max(max_lat, pt.latitude)
            min_lon = min(min_lon, pt.longitude)
            max_lon = max(max_lon, pt.longitude)
            lons.append(pt.longitude)

    center_lat = (min_lat + max_lat) / 2.0
    lat_delta = max(max_lat - min_lat, 0.01)

    # Longitude: work in [0, 360) so we can detect date-line crossing. When the
    # span > 180°, the data wraps the Pacific; use the smaller arc so the map
    # center stays where the data is (e.g. Pacific), not the wrong side (e.g. Europe).
    lon_360 = [(lon % 360) for lon in lons]
    lo, hi = min(lon_360), max(lon_360)
    raw_span = hi - lo
    if raw_span <= 180:
        # Data in one arc [lo, hi]; center is its midpoint
        center_360 = (lo + hi) / 2.0
        lng_delta = max(raw_span, 0.01)
    else:
        # Data wraps: it lies in the arc [hi, lo+360]. Use that arc’s length and center.
        lng_delta = max(360.0 - raw_span, 0.01)
        center_360 = hi + lng_delta / 2.0
        if center_360 >= 360:
            center_360 -= 360
    # Convert to [-180, 180] for the API
    center_lon = center_360 - 360.0 if center_360 > 180 else center_360

    return (center_lat, center_lon, lat_delta, lng_delta)


def kml_to_range_data(kml_content: str) -> Optional[RangeData]:
    """
    Convert KML content (already broken into polygon Placemarks) to RangeData.
    Returns None if no polygon Placemarks are found.
    """
    root = ET.fromstring(kml_content)
    placemarks = root.findall(f".//{_tag('Placemark')}")

    polygons: list[RangePolygon] = []
    for pm in placemarks:
        poly = pm.find(_tag("Polygon"))
        if poly is None:
            continue
        outer = poly.find(f"{_tag('outerBoundaryIs')}/{_tag('LinearRing')}/{_tag('coordinates')}")
        if outer is None or not (outer.text and outer.text.strip()):
            continue
        coords = _parse_coordinates(outer.text)
        if len(coords) < 3:
            continue
        name_el = pm.find(_tag("name"))
        name = name_el.text if name_el is not None else None
        prob = _probability_from_placemark_name(name)
        polygons.append(
            RangePolygon(coordinates=coords, occurrence_probability=prob)
        )

    if not polygons:
        return None
    center_lat, center_lon, lat_delta, lng_delta = _bounding_window(polygons)
    return RangeData(
        polygons=polygons,
        centerLatitude=center_lat,
        centerLongitude=center_lon,
        latDelta=lat_delta,
        lngDelta=lng_delta,
    )
