import math
import requests
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

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
    speed_kmh: float = 40.0, winding_factor: float = 1.3
) -> Dict[str, Any]:
    """Fallback route estimation if OSRM service is unreachable."""
    dist_direct = haversine_distance_km(start_lat, start_lon, end_lat, end_lon)
    dist_road = dist_direct * winding_factor
    duration_min = (dist_road / speed_kmh) * 60.0

    # Linearly interpolate 10 intermediate points
    lats = np.linspace(start_lat, end_lat, 10)
    lons = np.linspace(start_lon, end_lon, 10)
    polyline = [[float(la), float(lo)] for la, lo in zip(lats, lons)]

    return {
        "duration_min": duration_min,
        "distance_km": dist_road,
        "polyline_coords": polyline,
        "steps": [
            f"Drive from ({start_lat:.4f}, {start_lon:.4f}) to ({end_lat:.4f}, {end_lon:.4f}) via local roads (~{dist_road:.1f} km)"
        ],
        "is_fallback": True
    }

def fetch_osrm_route(
    start_lat: float, start_lon: float, end_lat: float, end_lon: float,
    timeout: int = 5
) -> Dict[str, Any]:
    """
    Fetch exact driving route from Open Source Routing Machine (OSRM) public API.
    Returns duration, distance, road-snapped polyline coordinates, and turn-by-turn steps.
    """
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson&steps=true"
    
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            routes = data.get("routes", [])
            if routes:
                route0 = routes[0]
                duration_min = float(route0.get("duration", 0.0)) / 60.0
                distance_km = float(route0.get("distance", 0.0)) / 1000.0
                
                # GeoJSON coordinates format: [[lon, lat], ...] -> convert to [[lat, lon], ...] for Folium
                raw_coords = route0.get("geometry", {}).get("coordinates", [])
                polyline_coords = [[pt[1], pt[0]] for pt in raw_coords]

                # Extract turn-by-turn step instructions
                steps_list = []
                legs = route0.get("legs", [])
                for leg in legs:
                    for step in leg.get("steps", []):
                        name = step.get("name", "road")
                        maneuver = step.get("maneuver", {}).get("type", "drive")
                        step_dist_mi = (step.get("distance", 0.0) / 1000.0) * 0.621371
                        if step_dist_mi > 0.05:
                            instruction = f"{maneuver.title()} on {name if name else 'connecting road'} ({step_dist_mi:.1f} mi)"
                            steps_list.append(instruction)

                if not steps_list:
                    steps_list = [f"Drive {distance_km:.1f} km along primary road network."]

                return {
                    "duration_min": duration_min,
                    "distance_km": distance_km,
                    "polyline_coords": polyline_coords,
                    "steps": steps_list,
                    "is_fallback": False
                }
    except Exception:
        pass

    return fallback_geodesic_route(start_lat, start_lon, end_lat, end_lon)

def fetch_osrm_multistop_route(
    coords: List[Tuple[float, float]],
    timeout: int = 6
) -> Dict[str, Any]:
    """
    Fetch multi-stop driving itinerary polyline and step instructions across a sequence of stops.
    """
    if len(coords) < 2:
        return {"duration_min": 0.0, "distance_km": 0.0, "polyline_coords": [], "steps": [], "is_fallback": False}

    coord_str = ";".join([f"{lon},{lat}" for lat, lon in coords])
    url = f"http://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=geojson&steps=true"

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
                        maneuver = step.get("maneuver", {}).get("type", "drive")
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
        leg_res = fallback_geodesic_route(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1])
        total_dur += leg_res["duration_min"]
        total_dist += leg_res["distance_km"]
        all_polylines.extend(leg_res["polyline_coords"])
        all_steps.append(f"Leg {i+1}: Drive {leg_res['distance_km']:.1f} km")

    return {
        "duration_min": total_dur,
        "distance_km": total_dist,
        "polyline_coords": all_polylines,
        "steps": all_steps,
        "is_fallback": True
    }
