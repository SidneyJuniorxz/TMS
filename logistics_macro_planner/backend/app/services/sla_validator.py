def validate_sla(route_distance_km: float, deadline_days: int, avg_km_per_day: float = 600.0) -> bool:
    """
    Simple SLA validation based on average distance traveled per day.
    """
    if deadline_days <= 0:
        return False
        
    estimated_days = route_distance_km / avg_km_per_day
    
    return estimated_days <= deadline_days

def check_route_sla(route_distance_km: float, deliveries: list[dict]) -> bool:
    """
    Checks if the entire route distance satisfies the tightest SLA in the delivery list.
    """
    if not deliveries:
        return True
        
    min_deadline = min(d.get("deadline_days", 999) for d in deliveries)
    
    return validate_sla(route_distance_km, min_deadline)
