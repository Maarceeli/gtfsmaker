from dataclasses import dataclass


@dataclass
class Stop:
    stop_id: str
    stop_code: str
    stop_name: str
    stop_lat: float
    stop_lon: float


@dataclass
class Route:
    route_id: str
    route_short_name: str
    route_type: int


@dataclass
class Trip:
    route_id: str
    service_id: str
    trip_id: str


@dataclass
class StopTime:
    trip_id: str
    arrival_time: str
    departure_time: str
    stop_id: str
    stop_sequence: int
    stop_headsign: str | None = None
    pickup_type: int = 0
    drop_off_type: int = 0
    shape_dist_traveled: float | None = None
    timepoint: int = 1
