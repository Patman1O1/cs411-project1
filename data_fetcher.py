# ── Imports ──────────────────────────────────────────────────────────────────
# Builtin Imports
import json
import math
import time
from typing import Any, Final, Optional, TypeAlias

# Third-Party Imports
import requests

# ── Aliases ──────────────────────────────────────────────────────────────────
LatLon: TypeAlias = tuple[float, float]
Coordinates: TypeAlias = dict[str, float]
Locations: TypeAlias = dict[str, Coordinates]
Graph: TypeAlias = dict[str, dict[str, float]]
Edge: TypeAlias = tuple[str, str]
MapData: TypeAlias = dict[str, Any]

# ── Constants ────────────────────────────────────────────────────────────────
REGION_NAME: Final[str] = "Illinois, USA"
OUTPUT_FILE: Final[str] = "map_data.json"
USER_AGENT: Final[str] = \
    "CS411-Search-Visualizer/1.0 (uic-cs411-student-project)"

NOMINATIM_URL: Final[str] = "https://nominatim.openstreetmap.org/search"
OSRM_URL: Final[str] = "http://router.project-osrm.org/route/v1/driving"
REQUEST_TIMEOUT_SECONDS: Final[float] = 10.0
NOMINATIM_DELAY_SECONDS: Final[float] = 1.0
OSRM_DELAY_SECONDS: Final[float] = 0.2

EARTH_RADIUS_MILES: Final[float] = 3_958.8
MILES_PER_METER: Final[float] = 0.000_621_371

CITIES: Final[list[str]] = [
    "Chicago, IL",
    "Aurora, IL",
    "Naperville, IL",
    "Joliet, IL",
    "Rockford, IL",
    "Springfield, IL",
    "Peoria, IL",
    "Elgin, IL",
    "Waukegan, IL",
    "Champaign, IL",
    "Bloomington, IL",
    "Decatur, IL",
    "Evanston, IL",
    "Schaumburg, IL",
    "Arlington Heights, IL",
    "Bolingbrook, IL",
    "Palatine, IL",
    "Skokie, IL",
    "Des Plaines, IL",
    "Orland Park, IL",
    "Kankakee, IL",
    "DeKalb, IL"
]

ROAD_CONNECTIONS: Final[list[Edge]] = [
    ("Chicago, IL", "Evanston, IL"),
    ("Chicago, IL", "Skokie, IL"),
    ("Chicago, IL", "Des Plaines, IL"),
    ("Chicago, IL", "Naperville, IL"),
    ("Chicago, IL", "Joliet, IL"),
    ("Chicago, IL", "Orland Park, IL"),
    ("Evanston, IL", "Skokie, IL"),
    ("Skokie, IL", "Des Plaines, IL"),
    ("Des Plaines, IL", "Arlington Heights, IL"),
    ("Arlington Heights, IL", "Palatine, IL"),
    ("Palatine, IL", "Schaumburg, IL"),
    ("Schaumburg, IL", "Elgin, IL"),
    ("Elgin, IL", "DeKalb, IL"),
    ("DeKalb, IL", "Rockford, IL"),
    ("Rockford, IL", "Elgin, IL"),
    ("Arlington Heights, IL", "Waukegan, IL"),
    ("Evanston, IL", "Waukegan, IL"),
    ("Schaumburg, IL", "Naperville, IL"),
    ("Naperville, IL", "Aurora, IL"),
    ("Aurora, IL", "DeKalb, IL"),
    ("Aurora, IL", "Joliet, IL"),
    ("Naperville, IL", "Bolingbrook, IL"),
    ("Bolingbrook, IL", "Joliet, IL"),
    ("Joliet, IL", "Orland Park, IL"),
    ("Joliet, IL", "Kankakee, IL"),
    ("Kankakee, IL", "Champaign, IL"),
    ("Joliet, IL", "Bloomington, IL"),
    ("Rockford, IL", "Peoria, IL"),
    ("Peoria, IL", "Bloomington, IL"),
    ("Bloomington, IL", "Champaign, IL"),
    ("Bloomington, IL", "Decatur, IL"),
    ("Bloomington, IL", "Springfield, IL"),
    ("Peoria, IL", "Springfield, IL"),
    ("Springfield, IL", "Decatur, IL"),
    ("Decatur, IL", "Champaign, IL")
]

# ── Distance ─────────────────────────────────────────────────────────────────
def haversine_distance(coord1: LatLon, coord2: LatLon) -> float:
    lat1: float
    lon1: float
    lat1, lon1 = coord1

    lat2: float
    lon2: float
    lat2, lon2 = coord2

    phi1: float = math.radians(lat1)
    phi2: float = math.radians(lat2)

    dphi: float = math.radians(lat2 - lat1)
    dlambda: float = math.radians(lon2 - lon1)

    a: float =                        \
        math.sin(dphi / 2.0) ** 2.0 + \
        math.cos(phi1) *              \
        math.cos(phi2) *              \
        math.sin(dlambda / 2.0) ** 2.0

    c: float = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return round(EARTH_RADIUS_MILES * c, 2)

# ── API Fetching ─────────────────────────────────────────────────────────────
def fetch_coordinates(city_name: str) -> Optional[Coordinates]:
    params: dict[str, Any] = {
        "q": city_name,
        "format": "json",
        "limit": 1
    }
    headers: dict[str, str] = {"User-Agent": USER_AGENT}

    try:
        response: requests.Response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS
        )

        if response.status_code == 200:
            data: Any = response.json()
            if data:
                lat: float = float(data[0]["lat"])
                lon: float = float(data[0]["lon"])
                return {"lat": lat, "lon": lon}
    except Exception as e:
        print(f"  [Warning] Failed to fetch coordinates for {city_name}: {e}")

    return None


def fetch_road_distance(coord1: LatLon, coord2: LatLon) -> float:
    lat1: float
    lon1: float
    lat1, lon1 = coord1

    lat2: float
    lon2: float
    lat2, lon2 = coord2

    url: str = f"{OSRM_URL}/{lon1},{lat1};{lon2},{lat2}"
    params: dict[str, str] = {"overview": "false"}

    try:
        response: requests.Response = requests.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS
        )

        if response.status_code == 200:
            data: Any = response.json()
            if data.get("code") == "Ok" and len(data.get("routes", [])) > 0:
                distance_meters: float = data["routes"][0]["distance"]
                distance_miles: float = distance_meters * MILES_PER_METER
                return round(distance_miles, 2)
    except Exception as e:
        print(f"  [Warning] OSRM routing failed ({coord1} -> {coord2}): {e}")

    return haversine_distance(coord1, coord2)

# ── Graph Construction ───────────────────────────────────────────────────────
def build_graph() -> None:
    print(f"Building map graph for region: {REGION_NAME}")
    print(f"Total locations to geocode: {len(CITIES)}")

    locations: Locations = {}

    idx: int
    city: str
    for idx, city in enumerate(CITIES, 1):
        print(f"[{idx}/{len(CITIES)}] Geocoding: {city} ...")

        coords: Optional[Coordinates] = fetch_coordinates(city)
        if coords: locations[city] = coords
        else: print(f"  [Error] Could not find coordinates for {city}")

        time.sleep(NOMINATIM_DELAY_SECONDS)

    graph: Graph = {city: {} for city in locations}

    print(
        f"\nFetching road distances for "
        f"{len(ROAD_CONNECTIONS)} connections ..."
    )
    total_edges: int = 0

    u: str
    v: str
    for u, v in ROAD_CONNECTIONS:
        if u not in locations or v not in locations:
            print(
                f"  [Warning] Skipping edge ({u}, {v}) - "
                f"missing location coordinates."
            )
            continue

        c1: LatLon = (locations[u]["lat"], locations[u]["lon"])
        c2: LatLon = (locations[v]["lat"], locations[v]["lon"])
        dist: float = fetch_road_distance(c1, c2)

        graph[u][v] = dist
        graph[v][u] = dist
        total_edges += 1

        print(f"  Connection: {u} <---> {v} : {dist} miles")
        time.sleep(OSRM_DELAY_SECONDS)

    map_data: MapData = {
        "region": REGION_NAME,
        "total_cities": len(locations),
        "total_edges": total_edges,
        "locations": locations,
        "graph": graph
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(map_data, f, indent=2)

    print("\nGraph construction complete!")
    print(
        f"Saved to {OUTPUT_FILE} with {len(locations)} cities "
        f"and {total_edges} connections."
    )

# ── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__": build_graph()
