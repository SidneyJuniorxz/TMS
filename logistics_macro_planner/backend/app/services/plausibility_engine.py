from statistics import mean
import math
from ..utils.geo_utils import haversine_km, route_total_distance

def distances_from_origin(origin: dict, stops: list[dict]) -> list[float]:
    return [
        haversine_km(origin["lat"], origin["lon"], stop["lat"], stop["lon"])
        for stop in stops
    ]

def calculate_direction_changes(origin: dict, stops: list[dict]) -> int:
    """
    Measures abrupt direction changes using the angle of the origin->destination vector.
    """
    if len(stops) < 3:
        return 0

    angles = []
    for stop in stops:
        dy = stop["lat"] - origin["lat"]
        dx = stop["lon"] - origin["lon"]
        angle = math.degrees(math.atan2(dy, dx))
        angles.append(angle)

    changes = 0
    for i in range(1, len(angles)):
        delta = abs(angles[i] - angles[i - 1])
        if delta > 180:
            delta = 360 - delta
        if delta > 45:
            changes += 1

    return changes

def outlier_penalty(origin: dict, stops: list[dict]) -> float:
    """
    Penalizes a point that is too isolated compared to the average.
    """
    if len(stops) < 3:
        return 0.0

    dists = distances_from_origin(origin, stops)
    avg = mean(dists)
    max_dist = max(dists)

    if avg == 0:
        return 0.0

    ratio = max_dist / avg

    if ratio >= 2.2:
        return 30.0
    if ratio >= 1.8:
        return 20.0
    if ratio >= 1.5:
        return 10.0
    return 0.0

def route_spread_penalty(origin: dict, stops: list[dict]) -> float:
    """
    Measures radial dispersion of points.
    """
    if len(stops) < 3:
        return 0.0

    dists = distances_from_origin(origin, stops)
    avg = mean(dists)
    spread = max(dists) - min(dists)

    if avg == 0:
        return 0.0

    spread_ratio = spread / avg

    if spread_ratio > 1.2:
        return 20.0
    if spread_ratio > 0.8:
        return 10.0
    return 0.0

def detour_penalty(origin: dict, ordered_stops: list[dict]) -> float:
    """
    Compares the ordered route with a version ordered by radial distance.
    If the real route is much worse, penalize.
    """
    if len(ordered_stops) < 3:
        return 0.0

    actual = route_total_distance(origin, ordered_stops)
    radial_sorted = sorted(
        ordered_stops,
        key=lambda s: haversine_km(origin["lat"], origin["lon"], s["lat"], s["lon"])
    )
    baseline = route_total_distance(origin, radial_sorted)

    if baseline == 0:
        return 0.0

    ratio = actual / baseline

    if ratio > 1.5:
        return 30.0
    if ratio > 1.25:
        return 15.0
    return 0.0

def progression_score(origin: dict, stops: list[dict]) -> float:
    """
    Rewards routes that progressively move further away.
    """
    if len(stops) < 2:
        return 20.0

    dists = distances_from_origin(origin, stops)

    good_steps = 0
    for i in range(1, len(dists)):
        if dists[i] >= dists[i - 1] * 0.9:
            good_steps += 1
    
    return (good_steps / (len(dists) - 1)) * 30.0

def calculate_plausibility_score(origin: dict, stops: list[dict]) -> dict:
    """
    Calculates the final plausibility score for a scenario.
    """
    if not stops:
        return {"score": 0.0, "details": "No stops"}

    # Base score
    base_score = 100.0
    
    # Penalties
    outlier = outlier_penalty(origin, stops)
    spread = route_spread_penalty(origin, stops)
    detour = detour_penalty(origin, stops)
    dir_changes = calculate_direction_changes(origin, stops) * 5.0 # 5 points per change > 45 deg
    
    # Bonuses
    progression = progression_score(origin, stops)
    
    final_score = base_score + progression - (outlier + spread + detour + dir_changes)
    
    return {
        "score": max(0.0, final_score),
        "details": {
            "base": base_score,
            "progression": progression,
            "penalties": {
                "outlier": outlier,
                "spread": spread,
                "detour": detour,
                "direction_changes": dir_changes
            }
        }
    }
