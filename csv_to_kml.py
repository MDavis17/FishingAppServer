import argparse
import csv
from xml.etree.ElementTree import Element, SubElement, ElementTree


def find_header_start(file_path):
    """
    Finds the line number where the actual CSV header begins.
    """
    with open(file_path, "r", encoding="latin-1") as f:
        for i, line in enumerate(f):
            if line.strip().startswith("Genus,Species"):
                return i
    raise ValueError("Could not find AquaMaps CSV header.")


def csv_to_kml(input_csv, output_kml, min_probability=None):
    print(f"Reading AquaMaps CSV: {input_csv}")

    header_line = find_header_start(input_csv)

    # Create KML structure
    kml = Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    document = SubElement(kml, "Document")

    count = 0

    with open(input_csv, newline="", encoding="latin-1") as csvfile:
        # Skip metadata lines
        for _ in range(header_line):
            next(csvfile)

        reader = csv.DictReader(csvfile)

        skipped = 0

        for row in reader:
            try:
                lat = float(row["Center Lat"])
                lon = float(row["Center Long"])
            except (ValueError, KeyError, TypeError):
                skipped += 1
                continue

            # Probability is optional -- default to 0 if missing or unparseable
            try:
                probability = float(row.get("Overall Probability", 0))
            except (ValueError, TypeError):
                probability = 0.0

            # Optional probability filter
            if min_probability is not None:
                if probability < min_probability:
                    continue

            placemark = SubElement(document, "Placemark")

            genus = row.get("Genus", "Unknown")
            species = row.get("Species", "Unknown")

            name = SubElement(placemark, "name")
            name.text = f"{genus} {species} ({probability:.2f})"

            description = SubElement(placemark, "description")
            description.text = f"Probability: {probability}"

            point = SubElement(placemark, "Point")
            coordinates = SubElement(point, "coordinates")
            coordinates.text = f"{lon},{lat},0"

            count += 1

    ElementTree(kml).write(output_kml, encoding="utf-8", xml_declaration=True)

    print(f"Created {count} placemarks")
    if skipped:
        print(f"Skipped {skipped} rows with missing/invalid coordinates")
    print(f"KML saved to: {output_kml}")


def main():
    parser = argparse.ArgumentParser(description="Convert AquaMaps HSPEC CSV to KML")
    parser.add_argument("input", help="Path to AquaMaps CSV file")
    parser.add_argument("output", help="Output KML file")
    parser.add_argument(
        "--min_prob",
        type=float,
        default=None,
        help="Minimum Overall Probability threshold (e.g., 0.3)",
    )

    args = parser.parse_args()

    csv_to_kml(args.input, args.output, args.min_prob)


if __name__ == "__main__":
    main()
