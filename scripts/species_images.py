"""Helpers for species image paths and Neon Object Storage URLs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPECIES_IMAGES_DIR = PROJECT_ROOT / "static" / "images" / "species"
URL_MAP_PATH = Path(__file__).resolve().parent / "species_image_urls.json"
DEFAULT_BUCKET = "species-images"


def load_dotenv() -> None:
    from dotenv import load_dotenv as _load

    env_local = PROJECT_ROOT / ".env.local"
    env_file = PROJECT_ROOT / ".env"
    if env_local.exists():
        _load(env_local)
    elif env_file.exists():
        _load(env_file)


def filename_from_image_field(image: str) -> str:
    if not image:
        return ""
    if image.startswith("http://") or image.startswith("https://"):
        path = urlparse(image).path
    else:
        path = image if image.startswith("/") else f"/{image}"
    return Path(path).name


def storage_public_url(object_key: str) -> str:
    endpoint = os.getenv("AWS_ENDPOINT_URL_S3", "").rstrip("/")
    bucket = os.getenv("SPECIES_IMAGES_BUCKET", DEFAULT_BUCKET)
    if not endpoint:
        return ""
    return f"{endpoint}/{bucket}/{object_key}"


def static_image_path(filename: str) -> str:
    if not filename:
        return ""
    return f"/static/images/species/{filename}"


def load_uploaded_url_map() -> dict[str, str]:
    if not URL_MAP_PATH.exists():
        return {}
    with URL_MAP_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    return {str(k): str(v) for k, v in data.items()}


def save_uploaded_url_map(mapping: dict[str, str]) -> None:
    with URL_MAP_PATH.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, sort_keys=True)
        f.write("\n")


def resolve_species_image_url(image_field: str, url_map: dict[str, str] | None = None) -> str:
    filename = filename_from_image_field(image_field)
    if not filename:
        return ""
    mapping = url_map if url_map is not None else load_uploaded_url_map()
    if filename in mapping:
        return mapping[filename]
    storage_url = storage_public_url(filename)
    if storage_url and os.getenv("AWS_ENDPOINT_URL_S3"):
        return storage_url
    return static_image_path(filename)
