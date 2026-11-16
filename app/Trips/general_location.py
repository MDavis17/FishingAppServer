import logging
import os
from typing import Any, List, Optional

import httpx

from app.models.log import Location

logger = logging.getLogger(__name__)

PLACE_TYPE_PRIORITY = (
    "locality",
    "postal_town",
    "administrative_area_level_3",
    "sublocality_level_1",
    "administrative_area_level_2",
)


def _component_with_type(
    components: List[dict[str, Any]], type_name: str
) -> Optional[dict[str, Any]]:
    for component in components:
        types = component.get("types") or []
        if type_name in types:
            return component
    return None


def general_location_from_address_components(
    components: Optional[List[dict[str, Any]]],
) -> Optional[str]:
    if not components:
        return None

    place_name: Optional[str] = None
    for type_name in PLACE_TYPE_PRIORITY:
        match = _component_with_type(components, type_name)
        if match:
            place_name = match.get("long_name")
            break

    if not place_name:
        return None

    state = _component_with_type(components, "administrative_area_level_1")
    state_short = state.get("short_name") if state else None
    if state_short:
        return f"{place_name}, {state_short}"
    return place_name


def _reverse_geocode(latitude: float, longitude: float) -> Optional[str]:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        logger.debug("GOOGLE_MAPS_API_KEY not set; skipping reverse geocode")
        return None

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"latlng": f"{latitude},{longitude}", "language": "en", "key": api_key}

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as err:
        logger.warning("Reverse geocode failed: %s", err)
        return None

    if data.get("status") != "OK" or not data.get("results"):
        return None

    components = data["results"][0].get("address_components") or []
    return general_location_from_address_components(components)


def ensure_general_location_name(location: Location) -> Location:
    if location.generalLocationName:
        return location

    resolved = _reverse_geocode(
        location.coordinates.latitude,
        location.coordinates.longitude,
    )
    if not resolved:
        return location

    return location.model_copy(update={"generalLocationName": resolved})