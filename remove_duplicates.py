import argparse
import csv


def remove_duplicates(input_csv, output_csv):
    print(f"Reading: {input_csv}")

    seen = set()
    unique_rows = []
    duplicate_count = 0

    with open(input_csv, newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)

        if "Center Lat" not in reader.fieldnames or "Center Long" not in reader.fieldnames:
            raise ValueError("CSV must contain 'Center Lat' and 'Center Long' columns")

        for row in reader:
            lat = row["Center Lat"].strip()
            lon = row["Center Long"].strip()

            key = (lat, lon)

            if key not in seen:
                seen.add(key)
                unique_rows.append((lat, lon))
            else:
                duplicate_count += 1

    print(f"Found {duplicate_count} duplicate rows")
    print(f"Writing {len(unique_rows)} unique rows to: {output_csv}")

    with open(output_csv, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["Center Lat", "Center Long"])

        for lat, lon in unique_rows:
            writer.writerow([lat, lon])

    print("Done.")


def main():
    parser = argparse.ArgumentParser(description="Remove duplicate coordinate rows from CSV")
    parser.add_argument("input", help="Path to input CSV")
    parser.add_argument("output", help="Path to output CSV")

    args = parser.parse_args()
    remove_duplicates(args.input, args.output)


if __name__ == "__main__":
    main()