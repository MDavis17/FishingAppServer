import logging
from typing import Any, List, Optional

import httpx

from app.Auth.config import GOOGLE_MAPS_API_KEY
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


def _places_get(client: httpx.Client, path: str, params: dict[str, Any]) -> dict[str, Any]:
    response = client.get(
        f"https://maps.googleapis.com/maps/api/place/{path}",
        params={**params, "key": GOOGLE_MAPS_API_KEY, "language": "en"},
    )
    response.raise_for_status()
    return response.json()


def _reverse_geocode(latitude: float, longitude: float) -> Optional[str]:
    if not GOOGLE_MAPS_API_KEY:
        logger.warning(
            "GOOGLE_MAPS_API_KEY is not set; map pins will not get a city name"
        )
        return None

    try:
        with httpx.Client(timeout=10.0) as client:
            nearby = _places_get(
                client,
                "nearbysearch/json",
                {
                    "location": f"{latitude},{longitude}",
                    "rankby": "distance",
                    "type": "locality",
                },
            )
            if nearby.get("status") != "OK" or not nearby.get("results"):
                logger.warning(
                    "City lookup failed: %s %s",
                    nearby.get("status"),
                    nearby.get("error_message"),
                )
                return None

            nearest = nearby["results"][0]
            fallback_name = nearest.get("name")
            place_id = nearest.get("place_id")
            if not place_id:
                return fallback_name

            details = _places_get(
                client,
                "details/json",
                {"place_id": place_id, "fields": "address_components,name"},
            )
    except (httpx.HTTPError, ValueError) as err:
        logger.warning("City lookup failed: %s", err)
        return None

    if details.get("status") != "OK":
        logger.warning(
            "Place details for city lookup failed: %s %s",
            details.get("status"),
            details.get("error_message"),
        )
        return fallback_name

    components = (details.get("result") or {}).get("address_components") or []
    return general_location_from_address_components(components) or fallback_name


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