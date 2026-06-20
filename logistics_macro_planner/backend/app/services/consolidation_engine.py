"""
Consolidation Engine — Intelligent Bin Packing for cargo allocation.

Uses a First Fit Decreasing (FFD) heuristic to allocate deliveries into
vehicles while respecting weight, volume, and dimensional constraints.
"""
from copy import deepcopy


def check_dimensional_fit(delivery: dict, vehicle: dict) -> dict:
    """
    Check if a single delivery fits within a vehicle's dimensional limits.
    Returns a dict with 'fits' bool and 'alerts' list.
    """
    alerts = []
    fits = True

    # Weight check (single item)
    if delivery.get("peso_kg", 0) > vehicle.get("max_weight", float("inf")):
        alerts.append(f"Peso ({delivery['peso_kg']}kg) excede capacidade do veículo ({vehicle['max_weight']}kg)")
        fits = False

    # Volume check (single item)
    if delivery.get("volume_m3", 0) > vehicle.get("max_volume", float("inf")):
        alerts.append(f"Volume ({delivery['volume_m3']}m³) excede capacidade do veículo ({vehicle['max_volume']}m³)")
        fits = False

    # Dimensional checks (cm vs meters — vehicle dimensions are in meters)
    max_length_cm = vehicle.get("max_length", 0) * 100 if vehicle.get("max_length", 0) else float("inf")
    max_width_cm = vehicle.get("max_width", 0) * 100 if vehicle.get("max_width", 0) else float("inf")
    max_height_cm = vehicle.get("max_height", 0) * 100 if vehicle.get("max_height", 0) else float("inf")

    if delivery.get("comprimento_cm", 0) > max_length_cm:
        alerts.append(f"Comprimento ({delivery['comprimento_cm']}cm) excede limite ({max_length_cm}cm)")
        fits = False

    if delivery.get("largura_cm", 0) > max_width_cm:
        alerts.append(f"Largura ({delivery['largura_cm']}cm) excede limite ({max_width_cm}cm)")
        fits = False

    if delivery.get("altura_cm", 0) > max_height_cm:
        alerts.append(f"Altura ({delivery['altura_cm']}cm) excede limite ({max_height_cm}cm)")
        fits = False

    return {"fits": fits, "alerts": alerts}


def consolidate(deliveries: list[dict], vehicles: list[dict], route_distance_km: float = 0) -> dict:
    """
    Allocate deliveries into vehicles using First Fit Decreasing (FFD) heuristic.

    Args:
        deliveries: List of delivery dicts with peso_kg, volume_m3, comprimento_cm, etc.
        vehicles: List of vehicle dicts with max_weight, max_volume, max_length, etc.
        route_distance_km: Total route distance for cost estimation.

    Returns:
        Dict with:
        - allocations: list of {vehicle, deliveries, occupation, estimated_cost}
        - unallocated: list of deliveries that didn't fit
        - alerts: list of warning messages
        - total_cost: total estimated cost across all vehicles
    """
    if not deliveries:
        return {
            "allocations": [],
            "unallocated": [],
            "alerts": ["Nenhuma entrega para alocar"],
            "total_cost": 0,
            "summary": {}
        }

    if not vehicles:
        return {
            "allocations": [],
            "unallocated": deliveries,
            "alerts": ["Nenhum veículo disponível"],
            "total_cost": 0,
            "summary": {}
        }

    # Sort deliveries by volume descending (FFD strategy)
    sorted_deliveries = sorted(deliveries, key=lambda d: d.get("volume_m3", 0), reverse=True)

    # Sort vehicles by cost_km ascending (prefer cheaper vehicles first)
    sorted_vehicles = sorted(vehicles, key=lambda v: v.get("cost_km", 0))

    # Each "bin" is a vehicle instance with its remaining capacity
    bins = []  # List of {vehicle, deliveries, remaining_weight, remaining_volume}
    unallocated = []
    alerts = []

    for delivery in sorted_deliveries:
        allocated = False

        # Try to fit into existing bins
        for bin_data in bins:
            vehicle = bin_data["vehicle"]
            remaining_weight = bin_data["remaining_weight"]
            remaining_volume = bin_data["remaining_volume"]

            peso = delivery.get("peso_kg", 0)
            volume = delivery.get("volume_m3", 0)

            # Check remaining capacity
            if peso > remaining_weight:
                continue
            if volume > remaining_volume:
                continue

            # Check dimensional compatibility
            dim_check = check_dimensional_fit(delivery, vehicle)
            if not dim_check["fits"]:
                continue

            # Fits! Allocate
            bin_data["deliveries"].append(delivery)
            bin_data["remaining_weight"] -= peso
            bin_data["remaining_volume"] -= volume
            allocated = True
            break

        if not allocated:
            # Try to open a new bin with the cheapest compatible vehicle
            for vehicle in sorted_vehicles:
                peso = delivery.get("peso_kg", 0)
                volume = delivery.get("volume_m3", 0)

                if peso > vehicle.get("max_weight", 0):
                    continue
                if volume > vehicle.get("max_volume", 0):
                    continue

                dim_check = check_dimensional_fit(delivery, vehicle)
                if not dim_check["fits"]:
                    alerts.extend(dim_check["alerts"])
                    continue

                # Open new bin
                new_bin = {
                    "vehicle": deepcopy(vehicle),
                    "deliveries": [delivery],
                    "remaining_weight": vehicle["max_weight"] - peso,
                    "remaining_volume": vehicle["max_volume"] - volume,
                }
                bins.append(new_bin)
                allocated = True
                break

        if not allocated:
            unallocated.append(delivery)
            desc = delivery.get("descricao", "") or f"Entrega #{delivery.get('id', '?')}"
            alerts.append(
                f"⚠️ Carga '{desc}' ({delivery.get('peso_kg', 0)}kg / "
                f"{delivery.get('volume_m3', 0)}m³) não coube em nenhum veículo disponível"
            )

    # Build result allocations with occupation stats
    allocations = []
    total_cost = 0

    for bin_data in bins:
        vehicle = bin_data["vehicle"]
        bin_deliveries = bin_data["deliveries"]

        total_weight = sum(d.get("peso_kg", 0) for d in bin_deliveries)
        total_volume = sum(d.get("volume_m3", 0) for d in bin_deliveries)

        weight_pct = round((total_weight / vehicle["max_weight"]) * 100, 1) if vehicle["max_weight"] else 0
        volume_pct = round((total_volume / vehicle["max_volume"]) * 100, 1) if vehicle["max_volume"] else 0

        cost = round(route_distance_km * vehicle.get("cost_km", 0), 2)
        total_cost += cost

        # Generate occupation alerts
        if weight_pct > 95:
            alerts.append(f"🔴 Veículo '{vehicle['name']}' com ocupação de peso crítica ({weight_pct}%)")
        elif weight_pct > 80:
            alerts.append(f"🟡 Veículo '{vehicle['name']}' com ocupação de peso alta ({weight_pct}%)")

        if volume_pct > 95:
            alerts.append(f"🔴 Veículo '{vehicle['name']}' com ocupação de volume crítica ({volume_pct}%)")
        elif volume_pct > 80:
            alerts.append(f"🟡 Veículo '{vehicle['name']}' com ocupação de volume alta ({volume_pct}%)")

        allocations.append({
            "vehicle_id": vehicle.get("id"),
            "vehicle_name": vehicle.get("name"),
            "vehicle_tipo": vehicle.get("tipo", "Truck"),
            "deliveries": bin_deliveries,
            "delivery_count": len(bin_deliveries),
            "occupation": {
                "weight_kg": round(total_weight, 2),
                "weight_max_kg": vehicle["max_weight"],
                "weight_pct": weight_pct,
                "volume_m3": round(total_volume, 6),
                "volume_max_m3": vehicle["max_volume"],
                "volume_pct": volume_pct,
            },
            "estimated_cost": cost,
        })

    summary = {
        "total_deliveries": len(deliveries),
        "allocated": len(deliveries) - len(unallocated),
        "unallocated": len(unallocated),
        "vehicles_used": len(allocations),
        "total_cost": round(total_cost, 2),
        "total_weight_kg": round(sum(d.get("peso_kg", 0) for d in deliveries), 2),
        "total_volume_m3": round(sum(d.get("volume_m3", 0) for d in deliveries), 6),
    }

    return {
        "allocations": allocations,
        "unallocated": unallocated,
        "alerts": alerts,
        "total_cost": round(total_cost, 2),
        "summary": summary,
    }
