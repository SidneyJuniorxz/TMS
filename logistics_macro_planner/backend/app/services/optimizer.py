def choose_best_scenario(scenarios_with_results: list[dict]) -> dict:
    """
    Selects the best scenario from a list of scenarios that have already been scored.
    Expects each dict in list to have 'total_distance' and 'plausibility_score'.
    """
    if not scenarios_with_results:
        return {}

    # Initial sorting by plausibility score (high to low) and then by distance (low to high)
    # Filter out scenarios with very low plausibility if needed
    viable_scenarios = [s for s in scenarios_with_results if s.get("plausibility_score", 0) > 50]
    
    if not viable_scenarios:
        # Fallback to all if none are above threshold
        viable_scenarios = scenarios_with_results

    # Sort criteria: Highest score first, then lowest distance
    best = sorted(
        viable_scenarios, 
        key=lambda x: (-x.get("plausibility_score", 0), x.get("total_distance", float('inf')))
    )[0]
    
    return best
