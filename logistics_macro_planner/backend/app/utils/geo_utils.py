from math import radians, sin, cos, sqrt, atan2

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    r = 6371.0 # Earth radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c

def route_total_distance(origin: dict, stops: list[dict]) -> float:
    """
    Calculates total distance for a route starting from origin and passing through all stops.
    """
    if not stops:
        return 0.0

    total = 0.0
    current = origin

    for stop in stops:
        total += haversine_km(current["lat"], current["lon"], stop["lat"], stop["lon"])
        current = stop

    return total
