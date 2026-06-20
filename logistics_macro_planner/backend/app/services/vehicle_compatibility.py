def is_vehicle_compatible(vehicle: dict, delivery: dict) -> tuple[bool, list[str]]:
    """
    Checks if a delivery fits within the vehicle's capacity.
    Returns (compatible: bool, alerts: list[str]).
    """
    alerts = []
    compatible = True

    # Weight check
    peso = delivery.get("peso_kg", delivery.get("weight", 0))
    if peso > vehicle.get("max_weight", 0):
        alerts.append(f"Peso ({peso}kg) excede max ({vehicle.get('max_weight', 0)}kg)")
        compatible = False

    # Volume check
    vol = delivery.get("volume_m3", delivery.get("volume", 0))
    if vol > vehicle.get("max_volume", 0):
        alerts.append(f"Volume ({vol}m³) excede max ({vehicle.get('max_volume', 0)}m³)")
        compatible = False

    # Dimensional checks (delivery in cm, vehicle in meters)
    dim_map = [
        ("comprimento_cm", "max_length", "Comprimento"),
        ("largura_cm", "max_width", "Largura"),
        ("altura_cm", "max_height", "Altura"),
    ]

    for del_key, veh_key, label in dim_map:
        del_val = delivery.get(del_key, 0)
        veh_val = vehicle.get(veh_key, 0)
        if del_val and veh_val:
            veh_val_cm = veh_val * 100  # Convert meters to cm
            if del_val > veh_val_cm:
                alerts.append(f"{label} ({del_val}cm) excede max ({veh_val_cm}cm)")
                compatible = False

    return compatible, alerts


def can_vehicle_handle_route(vehicle: dict, deliveries: list[dict]) -> bool:
    """
    Checks if the total weight and volume of all deliveries in a route
    fit within the vehicle's total capacity.
    """
    total_weight = sum(d.get("peso_kg", d.get("weight", 0)) for d in deliveries)
    total_volume = sum(d.get("volume_m3", d.get("volume", 0)) for d in deliveries)

    if total_weight > vehicle.get("max_weight", 0):
        return False

    if total_volume > vehicle.get("max_volume", 0):
        return False

    return True


def get_compatibility_level(vehicle: dict, deliveries: list[dict]) -> str:
    """
    Returns compatibility level: 'ok', 'warn', or 'fail'.
    - ok: < 80% capacity used
    - warn: 80-100% capacity used
    - fail: exceeds capacity
    """
    total_weight = sum(d.get("peso_kg", d.get("weight", 0)) for d in deliveries)
    total_volume = sum(d.get("volume_m3", d.get("volume", 0)) for d in deliveries)

    max_weight = vehicle.get("max_weight", 1)
    max_volume = vehicle.get("max_volume", 1)

    weight_pct = (total_weight / max_weight) * 100 if max_weight else 0
    volume_pct = (total_volume / max_volume) * 100 if max_volume else 0

    if weight_pct > 100 or volume_pct > 100:
        return "fail"
    if weight_pct > 80 or volume_pct > 80:
        return "warn"
    return "ok"
