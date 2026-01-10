import requests
import json
import base64
import csv
import os
from dataclasses import fields
from datetime import date
from api.models import Stop, Route, Trip, StopTime


class KpApiClient:
    def __init__(self, carrierSymbol: str) -> None:
        self.baseUrl = f"https://{carrierSymbol}.kiedyprzyjedzie.pl"

    def _parseCords(self, cords: str):
        a = list(str(cords))

        a.insert(2, ".")

        return float("".join(a))

    def _getTodayDate(self):
        return date.today().strftime("%Y-%m-%d")

    def _encodeLineName(self, line: str) -> str:
        utf8_bytes = line.encode("utf-8")
        base64_encoded = base64.b64encode(utf8_bytes).decode("ascii")
        url_safe = base64_encoded.replace("+", "-").replace("/", "_").rstrip("=")

        return url_safe

    def fetchStops(self) -> Stop:
        stops = []
        url = f"{self.baseUrl}/stops"

        # Make the POST request
        response = requests.get(url)

        # Check if the request was successful
        response.raise_for_status()

        jsondata = json.loads(response.text)

        for stop in jsondata["stops"]:
            stops.append(
                Stop(
                    stop_id=stop[0],
                    stop_code=stop[1],
                    stop_name=stop[2],
                    stop_lat=self._parseCords(stop[4]),
                    stop_lon=self._parseCords(stop[3]),
                )
            )

        return stops

    def fetchRoutes(self, stops: list[Stop]) -> list[Route]:
        routes = []
        date = self._getTodayDate()
        url = f"{self.baseUrl}/api/directions"

        for stop in stops:
            request = requests.get(f"{url}/{stop.stop_id}?date={date}")

            if not request.text:
                continue

            try:
                jsondata = json.loads(request.text)
            except json.JSONDecodeError:
                continue

            if "directions" not in jsondata:
                continue

            for dir in jsondata["directions"]:
                line = str(dir["line"])
                if any(r.route_id == line for r in routes):
                    continue
                routes.append(
                    Route(
                        route_id=line,
                        route_short_name=line,
                        route_type=3,
                    )
                )

        return routes

    def fetchTrips(self, stops: list[Stop]) -> list[Trip]:
        timetableUrl = f"{self.baseUrl}/api/timetable"
        directionsUrl = f"{self.baseUrl}/api/directions"
        date = self._getTodayDate()

        trips = []

        for stop in stops:
            request = requests.get(f"{directionsUrl}/{stop.stop_id}?date={date}")

            if not request.text:
                continue

            try:
                jsondata = json.loads(request.text)
            except json.JSONDecodeError:
                continue

            if "directions" not in jsondata:
                continue

            for dir in jsondata["directions"]:
                request = requests.get(
                    f"{timetableUrl}/{stop.stop_id}/{self._encodeLineName(dir['line'])}?date={date}"
                )

                if not request.text:
                    continue

                try:
                    timetable_data = json.loads(request.text)
                except json.JSONDecodeError:
                    continue

                if "departures" not in timetable_data:
                    continue

                for entry in timetable_data["departures"]:  # stop times parsing
                    trip_id = entry["trip_id"]
                    if any(t.trip_id == trip_id for t in trips):
                        continue
                    trips.append(
                        Trip(
                            route_id=entry["line"],
                            service_id="0",
                            trip_id=trip_id,
                        )
                    )

        return trips

    def fetchTimes(self, trips: list[Trip]) -> list[StopTime]:
        url = f"{self.baseUrl}/api/trip"

        times = []

        for trip in trips:
            request = requests.get(f"{url}/{trip.trip_id}/0")

            if not request.text:
                continue

            try:
                jsondata = json.loads(request.text)
            except json.JSONDecodeError:
                continue

            if "times" not in jsondata:
                continue

            for departure in jsondata["times"]:
                times.append(
                    StopTime(
                        trip_id=trip.trip_id,
                        arrival_time=f"{departure['departure_time']}:00",
                        departure_time=f"{departure['departure_time']}:00",
                        stop_id=departure["place_id"],
                        stop_sequence=departure["index"],
                    )
                )

        return times


def save_to_csv(data: list, filename: str, output_dir: str):
    if not data:
        return

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    field_names = [f.name for f in fields(data[0])]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        for item in data:
            writer.writerow({f.name: getattr(item, f.name) for f in fields(item)})
