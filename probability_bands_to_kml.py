#!/usr/bin/env python3
"""
Read a CSV with lat, lon, probability (e.g. Center Lat, Center Long, Overall Probability)
and write a KML with 3 colored polygon bands:
  Band 1: 0.00–0.33 (low)   – blue
  Band 2: 0.34–0.65 (mid)   – yellow
  Band 3: 0.66–1.00 (high)  – red
Lower probability bands are drawn first so higher probability shows on top.
Requires scipy for alpha shape: pip install scipy
"""

import argparse
import csv
import sys

# Reuse hull logic from points_to_polygon
from points_to_polygon import (
    convex_hull,
    _alpha_shape_boundary,
    _closed_ring,
    HAS_SCIPY,
)

# KML color format: AABBGGRR (alpha, blue, green, red), hex. 80 = ~50% opacity.
BAND_COLORS = [
    "80ff0000",  # blue  – low (0.00–0.33)
    "8000ffff",  # yellow – mid (0.34–0.65)
    "800000ff",  # red   – high (0.66–1.00)
]

BANDS = [
    (0.00, 0.33, "Low (0.00–0.33)"),
    (0.34, 0.65, "Mid (0.34–0.65)"),
    (0.66, 1.00, "High (0.66–1.00)"),
]


def read_points_with_probability(csv_path):
    """Read (lat, lon, probability) from CSV. Returns list of (lat, lon, prob)."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row or len(row) < 3:
                continue
            if i == 0 and not _is_number(row[0]):
                continue
            try:
                lat = float(row[0].strip())
                lon = float(row[1].strip())
                prob = float(row[2].strip())
                if not (0 <= prob <= 1):
                    continue
                rows.append((lat, lon, prob))
            except ValueError:
                continue
    return rows


def _is_number(s):
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def _hull_for_points(points, method, alpha):
    """Return polygon vertices for a list of (lat, lon) points."""
    if len(points) < 3:
        return None
    if method == "alpha" and HAS_SCIPY:
        hull = _alpha_shape_boundary(points, alpha)
        if hull is None and alpha > 0.02:
            hull = _alpha_shape_boundary(points, alpha / 2)
        if hull is None:
            hull = convex_hull(points)
    else:
        hull = convex_hull(points)
    return hull if len(hull) >= 3 else None


def write_bands_kml(band_vertices, kml_path, name="Range"):
    """Write a KML with one Placemark per band, each with its color. Draw low first."""
    placemarks = []
    for i, (low, high, label) in enumerate(BANDS):
        vertices = band_vertices[i]
        if not vertices or len(vertices) < 3:
            continue
        color = BAND_COLORS[i]
        ring = _closed_ring(vertices)
        coords = " ".join(f"{lon},{lat},0" for lat, lon in ring)
        placemarks.append(f'''    <Placemark>
      <name>{name} – {label}</name>
      <Style>
        <PolygonStyle>
          <color>{color}</color>
          <outline>0</outline>
        </PolygonStyle>
      </Style>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>{coords}</coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>''')

    body = "\n".join(placemarks)
    kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{name}</name>
{body}
  </Document>
</kml>'''
    with open(kml_path, "w", encoding="utf-8") as f:
        f.write(kml)


def main():
    parser = argparse.ArgumentParser(
        description="Create a 3-band probability KML from CSV (lat, lon, probability)."
    )
    parser.add_argument("input", help="Input CSV: Center Lat, Center Long, Overall Probability")
    parser.add_argument("output", help="Output KML file (3 colored polygon bands)")
    parser.add_argument(
        "--name",
        default="Range",
        help="Name for the layer in KML (default: Range)",
    )
    parser.add_argument(
        "--method",
        choices=("convex", "alpha"),
        default="alpha",
        help="Polygon per band: convex or alpha shape (default: alpha, requires scipy)",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.15,
        help="Alpha for alpha shape (default: 0.15). Larger = tighter.",
    )
    args = parser.parse_args()

    rows = read_points_with_probability(args.input)
    if not rows:
        print("No valid (lat, lon, probability) rows found. Exiting.", file=sys.stderr)
        return 1

    band_points = [[] for _ in BANDS]
    for (lat, lon, prob) in rows:
        for i, (low, high, _) in enumerate(BANDS):
            if low <= prob <= high:
                band_points[i].append((lat, lon))
                break

    band_vertices = []
    for i, (low, high, label) in enumerate(BANDS):
        pts = band_points[i]
        hull = _hull_for_points(pts, args.method, args.alpha) if pts else None
        band_vertices.append(hull or [])
        n = len(hull) if hull else 0
        print(f"Band {label}: {len(pts)} points -> {n} polygon vertices")

    write_bands_kml(band_vertices, args.output, name=args.name)
    print(f"Wrote 3-band KML to {args.output} (import in Google My Maps).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
