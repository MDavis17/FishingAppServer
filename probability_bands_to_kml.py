#!/usr/bin/env python3
"""
Read a CSV with lat, lon, probability (e.g. Center Lat, Center Long, Overall Probability)
and write a KML with 3 colored polygon bands:
  Band 1: 0.00–0.33 (low)   – blue
  Band 2: 0.34–0.65 (mid)   – yellow
  Band 3: 0.66–1.00 (high)  – red
Points in each band are clustered by spatial proximity; each cluster becomes one polygon,
so spread-out data produces multiple polygons per band (density-based).
Requires scipy for alpha shape and clustering: pip install scipy
"""

import argparse
import csv
import sys

try:
    import numpy as np
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import pdist
    HAS_CLUSTERING = True
except ImportError:
    HAS_CLUSTERING = False

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


def _cluster_points_by_distance(points, distance_degrees):
    """
    Group points into clusters by spatial proximity.
    points: list of (lat, lon). distance_degrees: max distance (in degree units) within a cluster.
    Returns list of lists of (lat, lon), one per cluster.
    """
    if not points or distance_degrees <= 0 or not HAS_CLUSTERING:
        return [points] if len(points) >= 3 else []
    if len(points) < 3:
        return []
    arr = np.array(points)
    if len(arr) == 3:
        return [points]
    try:
        dists = pdist(arr, metric="euclidean")
        Z = linkage(dists, method="average")
        labels = fcluster(Z, t=distance_degrees, criterion="distance")
    except Exception:
        return [points]
    clusters = {}
    for pt, lab in zip(points, labels):
        clusters.setdefault(lab, []).append(pt)
    return [pts for pts in clusters.values() if len(pts) >= 3]


def write_bands_kml(band_polygons, kml_path, name="Range"):
    """Write KML with one Placemark per polygon. band_polygons[i] = list of polygons (each polygon = list of vertices)."""
    placemarks = []
    for i, (low, high, label) in enumerate(BANDS):
        polygons = band_polygons[i] or []
        color = BAND_COLORS[i]
        for k, vertices in enumerate(polygons):
            if not vertices or len(vertices) < 3:
                continue
            ring = _closed_ring(vertices)
            coords = " ".join(f"{lon},{lat},0" for lat, lon in ring)
            pm_name = f"{name} – {label}" if len(polygons) <= 1 else f"{name} – {label} ({k + 1})"
            placemarks.append(f'''    <Placemark>
      <name>{pm_name}</name>
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
    parser.add_argument(
        "--cluster-distance",
        type=float,
        default=5.0,
        metavar="DEGREES",
        help="Cluster distance for all bands (degrees). Overridden by per-band args if set (default: 5.0). Use 0 for one polygon per band.",
    )
    parser.add_argument(
        "--cluster-distance-low",
        type=float,
        default=None,
        metavar="DEGREES",
        help="Cluster distance for low band only (0.00–0.33). Overrides --cluster-distance for this band.",
    )
    parser.add_argument(
        "--cluster-distance-mid",
        type=float,
        default=None,
        metavar="DEGREES",
        help="Cluster distance for mid band only (0.34–0.65). Overrides --cluster-distance for this band.",
    )
    parser.add_argument(
        "--cluster-distance-high",
        type=float,
        default=None,
        metavar="DEGREES",
        help="Cluster distance for high band only (0.66–1.00). Overrides --cluster-distance for this band.",
    )
    args = parser.parse_args()

    # Per-band cluster distance: use band-specific if set, else the single --cluster-distance
    cluster_distances = [
        args.cluster_distance_low if args.cluster_distance_low is not None else args.cluster_distance,
        args.cluster_distance_mid if args.cluster_distance_mid is not None else args.cluster_distance,
        args.cluster_distance_high if args.cluster_distance_high is not None else args.cluster_distance,
    ]

    if any(d > 0 for d in cluster_distances) and not HAS_CLUSTERING:
        print("Warning: numpy/scipy not available; using one polygon per band (install scipy for clustering).", file=sys.stderr)
        cluster_distances = [0.0, 0.0, 0.0]

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

    band_polygons = []
    for i, (low, high, label) in enumerate(BANDS):
        pts = band_points[i]
        if not pts:
            band_polygons.append([])
            print(f"Band {label}: 0 points")
            continue
        dist = cluster_distances[i]
        if dist > 0:
            clusters = _cluster_points_by_distance(pts, dist)
        else:
            clusters = [pts] if len(pts) >= 3 else []
        polygons = []
        for cluster in clusters:
            hull = _hull_for_points(cluster, args.method, args.alpha)
            if hull:
                polygons.append(hull)
        band_polygons.append(polygons)
        print(f"Band {label}: {len(pts)} points -> {len(polygons)} polygon(s) (cluster dist={dist})")

    write_bands_kml(band_polygons, args.output, name=args.name)
    print(f"Wrote 3-band KML to {args.output} (import in Google My Maps).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
