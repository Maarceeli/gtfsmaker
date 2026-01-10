import csv
import os
import tempfile
import zipfile
from datetime import date
from dataclasses import fields
from api.KpApiClient import KpApiClient

carriers = ["koszalin", "gorlice", "strzelceopolskie", "tomaszow"]


def save_to_csv(rows: list, filename: str, output_dir: str):
    if not rows:
        return

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    # Handle both dicts and dataclasses
    if isinstance(rows[0], dict):
        field_names = list(rows[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=field_names)
            writer.writeheader()
            writer.writerows(rows)
    else:
        field_names = [f.name for f in fields(rows[0])]
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=field_names)
            writer.writeheader()
            for item in rows:
                writer.writerow({f.name: getattr(item, f.name) for f in fields(item)})


def generate_agency(carrier: str) -> list[dict]:
    return [
        {
            "agency_id": carrier,
            "agency_name": carrier.capitalize(),
            "agency_url": f"https://{carrier}.kiedyprzyjedzie.pl",
            "agency_timezone": "Europe/Warsaw",
            "agency_lang": "pl",
        }
    ]


def generate_calendar_today() -> list[dict]:
    today = date.today()
    date_str = today.strftime("%Y%m%d")
    weekday = today.weekday()

    days = [0, 0, 0, 0, 0, 0, 0]
    days[weekday] = 1

    return [
        {
            "service_id": "0",
            "monday": days[0],
            "tuesday": days[1],
            "wednesday": days[2],
            "thursday": days[3],
            "friday": days[4],
            "saturday": days[5],
            "sunday": days[6],
            "start_date": date_str,
            "end_date": date_str,
        }
    ]


def create_gtfs_zip(carrier: str, temp_dir: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    zip_path = os.path.join(output_dir, f"{carrier}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            zipf.write(filepath, filename)

    return zip_path


for carrier in carriers:
    client = KpApiClient(carrier)

    # Create temp directory for CSV files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate static files
        agency = generate_agency(carrier)
        calendar = generate_calendar_today()
        stops = client.fetchStops()
        routes = client.fetchRoutes(stops)
        trips = client.fetchTrips(stops)
        times = client.fetchTimes(trips)

        print(f"\nCarrier/city: {carrier}")
        print(f"Stops: {len(stops)}")
        print(f"Routes: {len(routes)}")
        print(f"Trips: {len(trips)}")
        print(f"Times: {len(times)}")

        # Save CSV files to temp directory
        save_to_csv(stops, "stops.txt", temp_dir)
        save_to_csv(routes, "routes.txt", temp_dir)
        save_to_csv(trips, "trips.txt", temp_dir)
        save_to_csv(times, "stop_times.txt", temp_dir)
        save_to_csv(agency, "agency.txt", temp_dir)
        save_to_csv(calendar, "calendar.txt", temp_dir)

        # Create zip file in gtfs directory
        gtfs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gtfs")
        zip_path = create_gtfs_zip(carrier, temp_dir, gtfs_dir)

        print(f"Generated GTFS zip for {carrier}: {zip_path}")
