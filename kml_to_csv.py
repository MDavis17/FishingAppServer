import argparse
import csv
import xml.etree.ElementTree as ET


def extract_points_from_kml(input_kml):
    print(f"Loading KML: {input_kml}")

    tree = ET.parse(input_kml)
    root = tree.getroot()

    # KML namespace handling
    ns = {"kml": "http://www.opengis.net/kml/2.2"}

    points = []

    # Find all Point elements
    for point in root.findall(".//kml:Point", ns):
        coords = point.find("kml:coordinates", ns)
        if coords is not None and coords.text:
            coord_text = coords.text.strip()

            # KML format: lon,lat[,alt]
            parts = coord_text.split(",")

            if len(parts) >= 2:
                lon = float(parts[0])
                lat = float(parts[1])
                points.append((lat, lon))

    print(f"Found {len(points)} points")
    return points


def write_csv(points, output_csv):
    print(f"Writing CSV: {output_csv}")

    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Center Lat", "Center Long"])

        for lat, lon in points:
            writer.writerow([lat, lon])

    print("Done.")


def main():
    parser = argparse.ArgumentParser(description="Extract Point coordinates from KML to CSV")
    parser.add_argument("input", help="Path to input KML file")
    parser.add_argument("output", help="Path to output CSV file")

    args = parser.parse_args()

    points = extract_points_from_kml(args.input)
    write_csv(points, args.output)


if __name__ == "__main__":
    main()