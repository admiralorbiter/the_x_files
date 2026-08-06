import math
import requests
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

from ovon.routing.routing_provider import RoutingProvider, Coordinate, RouteGeometry

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate geodesic distance between two points in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def fallback_geodesic_route(
    start_lat: float, start_lon: float, end_lat: float, end_lon: float,
    speed_kmh: float = 40.0, winding_factor: float = 1.3,
    profile: str = "driving"
) -> Dict[str, Any]:
    """Fallback route estimation if OSRM service is unreachable."""
    if profile in ["walking", "foot"]:
        speed_kmh = 4.5
        winding_factor = 1.25
        action_verb = "Walk"
    else:
        action_verb = "Drive"

    dist_direct = haversine_distance_km(start_lat, start_lon, end_lat, end_lon)
    dist_road = dist_direct * winding_factor
    duration_min = (dist_road / speed_kmh) * 60.0

    lats = np.linspace(start_lat, end_lat, 10)
    lons = np.linspace(start_lon, end_lon, 10)
    polyline = [[float(la), float(lo)] for la, lo in zip(lats, lons)]

    return {
        "duration_min": duration_min,
        "distance_km": dist_road,
        "polyline_coords": polyline,
        "steps": [
            f"{action_verb} from ({start_lat:.4f}, {start_lon:.4f}) to ({end_lat:.4f}, {end_lon:.4f}) via path network (~{dist_road:.1f} km)"
        ],
        "is_fallback": True
    }

def fetch_osrm_route(
    start_lat: float, start_lon: float, end_lat: float, end_lon: float,
    profile: str = "driving",
    timeout: int = 5
) -> Dict[str, Any]:
    """
    Fetch exact route from OSRM API for driving or walking profile.
    """
    osrm_profile = "walking" if profile in ["walking", "foot"] else "driving"
    url = f"https://router.project-osrm.org/route/v1/{osrm_profile}/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson&steps=true"
    
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            routes = data.get("routes", [])
            if routes:
                route0 = routes[0]
                duration_min = float(route0.get("duration", 0.0)) / 60.0
                distance_km = float(route0.get("distance", 0.0)) / 1000.0
                
                raw_coords = route0.get("geometry", {}).get("coordinates", [])
                polyline_coords = [[pt[1], pt[0]] for pt in raw_coords]

                steps_list = []
                legs = route0.get("legs", [])
                for leg in legs:
                    for step in leg.get("steps", []):
                        name = step.get("name", "trail/path")
                        maneuver = step.get("maneuver", {}).get("type", "walk" if osrm_profile == "walking" else "drive")
                        step_dist_mi = (step.get("distance", 0.0) / 1000.0) * 0.621371
                        if step_dist_mi > 0.02:
                            instruction = f"{maneuver.title()} on {name if name else 'connecting path'} ({step_dist_mi:.2f} mi)"
                            steps_list.append(instruction)

                if not steps_list:
                    steps_list = [f"Walk {distance_km:.1f} km along pedestrian path network." if osrm_profile == "walking" else f"Drive {distance_km:.1f} km along primary road network."]

                return {
                    "duration_min": duration_min,
                    "distance_km": distance_km,
                    "polyline_coords": polyline_coords,
                    "steps": steps_list,
                    "is_fallback": False
                }
    except Exception:
        pass

    fallback_speed = 4.5 if osrm_profile == "walking" else 40.0
    return fallback_geodesic_route(start_lat, start_lon, end_lat, end_lon, speed_kmh=fallback_speed, profile=profile)

def fetch_osrm_multistop_route(
    coords: List[Tuple[float, float]],
    profile: str = "driving",
    timeout: int = 6
) -> Dict[str, Any]:
    """
    Fetch multi-stop driving or walking itinerary polyline across a sequence of stops.
    """
    if len(coords) < 2:
        return {"duration_min": 0.0, "distance_km": 0.0, "polyline_coords": [], "steps": [], "is_fallback": False}

    osrm_profile = "walking" if profile in ["walking", "foot"] else "driving"
    coord_str = ";".join([f"{lon},{lat}" for lat, lon in coords])
    url = f"https://router.project-osrm.org/route/v1/{osrm_profile}/{coord_str}?overview=full&geometries=geojson&steps=true"

    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            routes = data.get("routes", [])
            if routes:
                route0 = routes[0]
                duration_min = float(route0.get("duration", 0.0)) / 60.0
                distance_km = float(route0.get("distance", 0.0)) / 1000.0
                
                raw_coords = route0.get("geometry", {}).get("coordinates", [])
                polyline_coords = [[pt[1], pt[0]] for pt in raw_coords]

                steps_list = []
                for leg_idx, leg in enumerate(route0.get("legs", [])):
                    steps_list.append(f"--- Leg {leg_idx+1}: Stop {leg_idx+1} to Stop {leg_idx+2} ---")
                    for step in leg.get("steps", []):
                        name = step.get("name", "road")
                        maneuver = step.get("maneuver", {}).get("type", "walk" if osrm_profile == "walking" else "drive")
                        dist_mi = (step.get("distance", 0.0) / 1000.0) * 0.621371
                        if dist_mi > 0.05:
                            steps_list.append(f"  • {maneuver.title()} on {name if name else 'connecting route'} ({dist_mi:.1f} mi)")

                return {
                    "duration_min": duration_min,
                    "distance_km": distance_km,
                    "polyline_coords": polyline_coords,
                    "steps": steps_list,
                    "is_fallback": False
                }
    except Exception:
        pass

    # Fallback to leg-by-leg geodesic interpolation
    total_dur = 0.0
    total_dist = 0.0
    all_polylines = []
    all_steps = []

    for i in range(len(coords) - 1):
        leg_res = fallback_geodesic_route(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1], profile=profile)
        total_dur += leg_res["duration_min"]
        total_dist += leg_res["distance_km"]
        all_polylines.extend(leg_res["polyline_coords"])
        action = "Walk" if profile in ["walking", "foot"] else "Drive"
        all_steps.append(f"Leg {i+1}: {action} {leg_res['distance_km']:.1f} km")

    return {
        "duration_min": total_dur,
        "distance_km": total_dist,
        "polyline_coords": all_polylines,
        "steps": all_steps,
        "is_fallback": True
    }

class OSRMProvider:
    """Implementation of RoutingProvider protocol backed by OSRM API."""

    def duration_matrix(
        self,
        coordinates: List[Coordinate],
        mode: str = "walking"
    ) -> np.ndarray:
        n = len(coordinates)
        matrix = np.zeros((n, n), dtype=float)
        speed_kmh = 4.5 if mode in ["walking", "foot"] else 40.0
        winding = 1.25 if mode in ["walking", "foot"] else 1.3

        for i in range(n):
            for j in range(n):
                if i != j:
                    d_km = haversine_distance_km(coordinates[i].lat, coordinates[i].lon, coordinates[j].lat, coordinates[j].lon) * winding
                    matrix[i, j] = (d_km / speed_kmh) * 60.0
        return matrix

    def route_geometry(
        self,
        ordered_coordinates: List[Coordinate],
        mode: str = "walking"
    ) -> RouteGeometry:
        pts = [(c.lat, c.lon) for c in ordered_coordinates]
        res = fetch_osrm_multistop_route(pts, profile=mode)
        return RouteGeometry(
            coordinates=[(pt[0], pt[1]) for pt in res.get("polyline_coords", [])],
            distance_meters=res.get("distance_km", 0.0) * 1000.0,
            duration_seconds=res.get("duration_min", 0.0) * 60.0,
            instructions=res.get("steps", [])
        )
