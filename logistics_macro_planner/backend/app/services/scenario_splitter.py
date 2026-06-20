from copy import deepcopy
from .plausibility_engine import calculate_plausibility_score

def split_by_outlier(origin: dict, stops: list[dict]) -> dict:
    """
    Tenta separar o destino mais distante para ver se melhora muito a rota principal.
    """
    if len(stops) < 3:
        return {
            "should_split": False,
            "reason": "not_enough_stops"
        }

    full = calculate_plausibility_score(origin, stops)

    distances = []
    for idx, stop in enumerate(stops):
        d = ((origin["lat"] - stop["lat"]) ** 2 + (origin["lon"] - stop["lon"]) ** 2) ** 0.5
        distances.append((idx, d))

    outlier_index = sorted(distances, key=lambda x: x[1], reverse=True)[0][0]

    main_route = deepcopy(stops)
    isolated = main_route.pop(outlier_index)

    main_score = calculate_plausibility_score(origin, main_route)

    gain = main_score["score"] - full["score"]

    return {
        "should_split": gain >= 12.0,
        "full_route_score": full["score"],
        "main_route_score": main_score["score"],
        "gain": round(gain, 2),
        "isolated_stop": isolated,
        "remaining_route": main_route,
    }
