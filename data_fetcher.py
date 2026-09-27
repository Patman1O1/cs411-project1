"""
data_fetcher.py
================
Builds a connected road-network graph for a selected USA region.
Uses:
  - Nominatim OpenStreetMap API for geocoding (coordinates)
  - OSRM Routing API for road driving distances

Saves the resulting graph to `map_data.json`.
"""

import json
import time
import math
import requests

# ---------------------------------------------------------
# Configuration: Select USA Region & Locations (>= 20 cities)
# Example Region: Illinois, USA
# ---------------------------------------------------------
REGION_NAME = "Illinois, USA"

# List of at least 20 cities/locations in the selected region
CITIES = [
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

# Road connections between cities (Undirected graph edges)
# Ensure the graph is fully connected (a path exists between any two cities)
ROAD_CONNECTIONS = [
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

USER_AGENT = "CS411-Search-Visualizer/1.0 (uic-cs411-student-project)"


def haversine_distance(coord1, coord2):
    """
    Fallback straight-line (great-circle) distance in miles.
    coord = (lat, lon)
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 3958.8  # Earth radius in miles

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def fetch_coordinates(city_name):
    """
    Fetch latitude and longitude from Nominatim OpenStreetMap API.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city_name,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                return {"lat": lat, "lon": lon}
    except Exception as e:
        print(f"  [Warning] Failed to fetch coordinates for {city_name}: {e}")

    return None


def fetch_road_distance(coord1, coord2):
    """
    Fetch road driving distance in miles from OSRM Routing API.
    coord = (lat, lon)
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
    params = {"overview": "false"}

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "Ok" and len(data.get("routes", [])) > 0:
                distance_meters = data["routes"][0]["distance"]
                distance_miles = distance_meters * 0.000621371
                return round(distance_miles, 2)
    except Exception as e:
        print(f"  [Warning] OSRM routing failed ({coord1} -> {coord2}): {e}")

    # Fallback to straight-line distance if routing API fails
    return haversine_distance(coord1, coord2)


def build_graph():
    """
    Build the map graph and save to map_data.json.
    """
    print(f"Building map graph for region: {REGION_NAME}")
    print(f"Total locations to geocode: {len(CITIES)}")

    locations = {}
    for idx, city in enumerate(CITIES, 1):
        print(f"[{idx}/{len(CITIES)}] Geocoding: {city} ...")
        coords = fetch_coordinates(city)
        if coords:
            locations[city] = coords
        else:
            print(f"  [Error] Could not find coordinates for {city}")
        # Nominatim usage policy requires 1-second delay between requests
        time.sleep(1.0)

    # Initialize adjacency list
    graph = {city: {} for city in locations}

    print(f"\nFetching road distances for {len(ROAD_CONNECTIONS)} connections ...")
    total_edges = 0
    for u, v in ROAD_CONNECTIONS:
        if u in locations and v in locations:
            c1 = (locations[u]["lat"], locations[u]["lon"])
            c2 = (locations[v]["lat"], locations[v]["lon"])
            dist = fetch_road_distance(c1, c2)

            graph[u][v] = dist
            graph[v][u] = dist
            total_edges += 1
            print(f"  Connection: {u} <---> {v} : {dist} miles")
            time.sleep(0.2)
        else:
            print(f"  [Warning] Skipping edge ({u}, {v}) - missing location coordinates.")

    map_data = {
        "region": REGION_NAME,
        "total_cities": len(locations),
        "total_edges": total_edges,
        "locations": locations,
        "graph": graph
    }

    with open("map_data.json", "w") as f:
        json.dump(map_data, f, indent=2)

    print("\nGraph construction complete!")
    print(f"Saved to map_data.json with {len(locations)} cities and {total_edges} connections.")


if __name__ == "__main__":
    build_graph()
