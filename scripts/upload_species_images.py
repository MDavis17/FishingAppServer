"""Upload species PNGs to Neon Object Storage (S3-compatible)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.species_images import (  # noqa: E402
    DEFAULT_BUCKET,
    SPECIES_IMAGES_DIR,
    load_dotenv,
    save_uploaded_url_map,
    storage_public_url,
)


def upload_all() -> dict[str, str]:
    load_dotenv()

    endpoint = os.getenv("AWS_ENDPOINT_URL_S3")
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    bucket = os.getenv("SPECIES_IMAGES_BUCKET", DEFAULT_BUCKET)
    region = os.getenv("AWS_REGION", "us-east-1")

    if not endpoint or not access_key or not secret_key:
        print(
            "Skipping upload: Neon Object Storage credentials are not configured "
            "(AWS_ENDPOINT_URL_S3, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY). "
            "Run `npx neon@latest env pull` after Object Storage is available in your project region."
        )
        return {}

    try:
        import boto3
        from botocore.config import Config
    except ImportError as exc:
        raise SystemExit("Install boto3: pip install boto3") from exc

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )

    mapping: dict[str, str] = {}
    files = sorted(SPECIES_IMAGES_DIR.glob("*.png"))
    if not files:
        print(f"No PNG files found in {SPECIES_IMAGES_DIR}")
        return {}

    for path in files:
        key = path.name
        client.upload_file(
            str(path),
            bucket,
            key,
            ExtraArgs={
                "ContentType": "image/png",
                "CacheControl": "public, max-age=31536000, immutable",
            },
        )
        mapping[key] = storage_public_url(key)

    save_uploaded_url_map(mapping)
    print(f"Uploaded {len(mapping)} images to bucket '{bucket}'.")
    return mapping


if __name__ == "__main__":
    upload_all()
