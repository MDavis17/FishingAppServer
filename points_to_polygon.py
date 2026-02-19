#!/usr/bin/env python3
"""
Read a CSV of lat/long points (column 0 = latitude, column 1 = longitude)
and write a CSV of lat/long polygon vertices that enclose the points.
Supports convex hull or alpha shape (tighter fit, more vertices).
For alpha shape, install scipy: pip install scipy
"""

import argparse
import csv
import math

try:
    from scipy.spatial import Delaunay
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def cross(o, a, b):
    """2D cross product of vectors o->a and o->b. Positive if a is counterclockwise from b."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull(points):
    """
    Graham scan: return vertices of the convex hull in counterclockwise order.
    points: list of (lat, lon) or (x, y) tuples.
    """
    if len(points) < 3:
        return list(points)

    # Sort by (lat, lon) and remove duplicates
    points = sorted(set(points), key=lambda p: (p[0], p[1]))

    def build_hull(hull_points):
        hull = []
        for p in hull_points:
            while len(hull) >= 2 and cross(hull[-2], hull[-1], p) <= 0:
                hull.pop()
            hull.append(p)
        return hull

    # Lower hull
    lower = build_hull(points)
    # Upper hull (reverse and skip first/last to avoid duplicates)
    upper = build_hull(reversed(points))

    # Remove duplicate endpoint and return counterclockwise order
    if len(lower) + len(upper) <= 2:
        return lower + upper
    return lower[:-1] + upper[:-1]


def _circumradius(a, b, c):
    """Circumradius of triangle with vertices a, b, c (each (x,y) or (lat,lon))."""
    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]
    cx, cy = c[0], c[1]
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-10:
        return float("inf")
    ab = math.hypot(bx - ax, by - ay)
    bc = math.hypot(cx - bx, cy - by)
    ca = math.hypot(ax - cx, ay - cy)
    return (ab * bc * ca) / abs(d)


def _alpha_shape_boundary(points, alpha):
    """
    Alpha shape: boundary of the union of Delaunay triangles with circumradius < 1/alpha.
    Returns a single closed ring of (lat, lon) vertices, or None if alpha shape fails.
    Larger alpha = tighter fit (more vertices). Requires scipy.
    """
    if not HAS_SCIPY or len(points) < 3:
        return None
    pts = list(points)
    pts = sorted(set(pts), key=lambda p: (p[0], p[1]))
    try:
        tri = Delaunay(pts)
    except Exception:
        return None
    threshold = 1.0 / alpha if alpha > 0 else float("inf")
    # Find boundary edges: (i, j) such that edge is in exactly one "in" triangle
    edge_count = {}
    for simplex in tri.simplices:
        i, j, k = simplex[0], simplex[1], simplex[2]
        a, b, c = pts[i], pts[j], pts[k]
        r = _circumradius(a, b, c)
        if r < threshold:
            for (pi, pj) in [(i, j), (j, k), (k, i)]:
                edge = (min(pi, pj), max(pi, pj))
                edge_count[edge] = edge_count.get(edge, 0) + 1
    boundary_edges = [e for e, c in edge_count.items() if c == 1]
    if not boundary_edges:
        return None
    # Chain edges into ordered boundary (one or more loops)
    from_idx_to_point = {i: pts[i] for i in range(len(pts))}
    # Build adjacency: for each vertex, which other vertex (or two) via boundary edge
    adj = {}
    for (i, j) in boundary_edges:
        adj.setdefault(i, []).append(j)
        adj.setdefault(j, []).append(i)
    # Find longest boundary cycle (in case of multiple components)
    seen_edges = set()
    best_ring = []

    def walk_cycle(start):
        ring = [start]
        cur = start
        prev = -1
        while True:
            neibs = [
                n for n in adj.get(cur, [])
                if n != prev and (min(cur, n), max(cur, n)) not in seen_edges
            ]
            if not neibs:
                break
            next_node = neibs[0]
            seen_edges.add((min(cur, next_node), max(cur, next_node)))
            if next_node == start:
                break
            ring.append(next_node)
            prev, cur = cur, next_node
        return ring

    for (i, j) in boundary_edges:
        if (min(i, j), max(i, j)) in seen_edges:
            continue
        ring = walk_cycle(i)
        if len(ring) > len(best_ring):
            best_ring = ring

    if len(best_ring) < 3:
        return None
    return [pts[i] for i in best_ring]


def read_points(csv_path):
    """Read (lat, lon) points from CSV. First column = latitude, second = longitude."""
    points = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row or len(row) < 2:
                continue
            # Skip header if it looks like one
            if i == 0 and (row[0].lower() in ("center lat", "latitude", "lat") or not _is_number(row[0])):
                continue
            try:
                lat = float(row[0].strip())
                lon = float(row[1].strip())
                points.append((lat, lon))
            except ValueError:
                continue
    return points


def _is_number(s):
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def write_polygon_csv(vertices, csv_path, close_polygon=True):
    """Write polygon vertices to CSV. Optionally close the polygon by repeating the first point."""
    if close_polygon and len(vertices) > 1 and vertices[0] != vertices[-1]:
        vertices = list(vertices) + [vertices[0]]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["latitude", "longitude"])
        writer.writerows(vertices)


def _closed_ring(vertices):
    """Return vertices as a closed ring (first point repeated at end)."""
    if len(vertices) < 2:
        return list(vertices)
    if vertices[0] == vertices[-1]:
        return list(vertices)
    return list(vertices) + [vertices[0]]


def write_polygon_kml(vertices, kml_path, name="Range"):
    """
    Write a filled polygon to KML for import into Google Maps / My Maps.
    KML coordinates are lon,lat,altitude (space-separated in the file).
    """
    ring = _closed_ring(vertices)
    # KML: lon,lat,altitude (altitude 0 for flat polygon)
    coords = " ".join(f"{lon},{lat},0" for lat, lon in ring)
    kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>{name}</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>{coords}</coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>'''
    with open(kml_path, "w", encoding="utf-8") as f:
        f.write(kml)


def main():
    parser = argparse.ArgumentParser(
        description="Create a lat/long polygon from a CSV of points (convex hull or tighter alpha shape)."
    )
    parser.add_argument("input", help="Input CSV: first column latitude, second longitude")
    parser.add_argument("output", help="Output CSV: polygon vertices (latitude, longitude)")
    parser.add_argument(
        "--method",
        choices=("convex", "alpha"),
        default="alpha",
        help="convex = convex hull (fewer vertices). alpha = tighter fit, more vertices (default)",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.15,
        help="Tightness for alpha shape (--method alpha). Larger = tighter fit, more vertices (default: 0.15). Try 0.05–0.5 for large ranges.",
    )
    parser.add_argument(
        "--kml",
        metavar="FILE",
        help="Also write a KML file for Google Maps (filled polygon; import in My Maps)",
    )
    parser.add_argument(
        "--name",
        default="Range",
        help="Name for the polygon in KML (default: Range)",
    )
    parser.add_argument(
        "--no-close",
        action="store_true",
        help="Do not close the polygon in CSV (omit repeating the first point at the end)",
    )
    args = parser.parse_args()

    points = read_points(args.input)
    if len(points) < 2:
        print("Need at least 2 points to form a polygon. Exiting.")
        return 1

    if args.method == "alpha" and HAS_SCIPY:
        hull = _alpha_shape_boundary(points, args.alpha)
        if hull is None and args.alpha > 0.02:
            hull = _alpha_shape_boundary(points, args.alpha / 2)
        if hull is None:
            print("Alpha shape produced no boundary, falling back to convex hull.")
            hull = convex_hull(points)
        else:
            print(f"Alpha shape: {len(hull)} boundary vertices (tighter than convex hull).")
    elif args.method == "alpha" and not HAS_SCIPY:
        print("scipy not installed; using convex hull. Install scipy for tighter alpha shape: pip install scipy")
        hull = convex_hull(points)
    else:
        hull = convex_hull(points)

    write_polygon_csv(hull, args.output, close_polygon=not args.no_close)
    print(f"Read {len(points)} points, wrote polygon with {len(hull)} vertices to {args.output}")

    if args.kml:
        write_polygon_kml(hull, args.kml, name=args.name)
        print(f"Wrote KML (filled polygon) to {args.kml} — import in Google My Maps for a filled polygon.")

    return 0


if __name__ == "__main__":
    exit(main())
