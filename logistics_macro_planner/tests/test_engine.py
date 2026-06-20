import pytest
from backend.app.services import plausibility_engine, consolidation_engine, vehicle_compatibility
from backend.app.utils import geo_utils
from backend.app.api.deliveries import calculate_volume_m3


# ============================================================
# Existing Tests (unchanged)
# ============================================================

def test_haversine():
    # Guarulhos to Curitiba approx distance
    dist = geo_utils.haversine_km(-23.45, -46.53, -25.42, -49.27)
    assert 300 < dist < 450


def test_plausibility_good_route():
    origin = {"lat": -23.4543, "lon": -46.5333, "city": "Guarulhos"}
    stops = [
        {"lat": -23.5505, "lon": -46.6333, "city": "Sao Paulo"},
        {"lat": -25.4284, "lon": -49.2733, "city": "Curitiba"},
        {"lat": -26.3045, "lon": -48.8456, "city": "Joinville"}
    ]
    result = plausibility_engine.calculate_plausibility_score(origin, stops)
    assert result["score"] > 80


def test_plausibility_bad_route_detour():
    origin = {"lat": -23.4543, "lon": -46.5333, "city": "Guarulhos"}
    # Very messy route: Guarulhos -> Curitiba -> Sao Paulo (backtracking) -> Joinville
    stops = [
        {"lat": -25.4284, "lon": -49.2733, "city": "Curitiba"},
        {"lat": -23.5505, "lon": -46.6333, "city": "Sao Paulo"},
        {"lat": -26.3045, "lon": -48.8456, "city": "Joinville"}
    ]
    result = plausibility_engine.calculate_plausibility_score(origin, stops)
    assert result["score"] < 90


def test_clustering_generator():
    from backend.app.services.scenario_generator import generate_scenarios
    deliveries = [
        {"id": i, "lat": -25.0 + i*0.01, "lon": -48.0 + i*0.01, "weight": 10, "volume": 1, "deadline_days": 5, "city": f"City {i}", "city_id": i}
        for i in range(10)
    ]
    scenarios = generate_scenarios(deliveries, max_stops_per_route=6)
    assert len(scenarios) < 200


# ============================================================
# v2 Tests — Cubagem / Volume Calculation
# ============================================================

def test_volume_calculation_basic():
    """Cubagem: 100cm × 60cm × 50cm = 0.3 m³"""
    vol = calculate_volume_m3(100, 60, 50)
    assert vol == pytest.approx(0.3, abs=0.001)


def test_volume_calculation_small():
    """Cubagem: 10cm × 10cm × 10cm = 0.001 m³"""
    vol = calculate_volume_m3(10, 10, 10)
    assert vol == pytest.approx(0.001, abs=0.0001)


def test_volume_calculation_large():
    """Cubagem: 200cm × 150cm × 100cm = 3.0 m³"""
    vol = calculate_volume_m3(200, 150, 100)
    assert vol == pytest.approx(3.0, abs=0.001)


# ============================================================
# v2 Tests — Vehicle Compatibility
# ============================================================

def test_vehicle_compatible_ok():
    vehicle = {"max_weight": 1000, "max_volume": 10, "max_length": 3, "max_width": 2, "max_height": 2}
    delivery = {"peso_kg": 200, "volume_m3": 0.5, "comprimento_cm": 100, "largura_cm": 60, "altura_cm": 50}
    compatible, alerts = vehicle_compatibility.is_vehicle_compatible(vehicle, delivery)
    assert compatible is True
    assert len(alerts) == 0


def test_vehicle_compatible_fail_weight():
    vehicle = {"max_weight": 100, "max_volume": 10, "max_length": 3, "max_width": 2, "max_height": 2}
    delivery = {"peso_kg": 200, "volume_m3": 0.5, "comprimento_cm": 100, "largura_cm": 60, "altura_cm": 50}
    compatible, alerts = vehicle_compatibility.is_vehicle_compatible(vehicle, delivery)
    assert compatible is False
    assert any("Peso" in a for a in alerts)


def test_vehicle_compatible_fail_dimension():
    vehicle = {"max_weight": 1000, "max_volume": 10, "max_length": 1, "max_width": 2, "max_height": 2}
    delivery = {"peso_kg": 200, "volume_m3": 0.5, "comprimento_cm": 150, "largura_cm": 60, "altura_cm": 50}
    compatible, alerts = vehicle_compatibility.is_vehicle_compatible(vehicle, delivery)
    assert compatible is False
    assert any("Comprimento" in a for a in alerts)


def test_compatibility_level():
    vehicle = {"max_weight": 1000, "max_volume": 10}
    deliveries_low = [{"peso_kg": 100, "volume_m3": 1}]
    deliveries_high = [{"peso_kg": 900, "volume_m3": 9}]
    deliveries_over = [{"peso_kg": 1100, "volume_m3": 11}]

    assert vehicle_compatibility.get_compatibility_level(vehicle, deliveries_low) == "ok"
    assert vehicle_compatibility.get_compatibility_level(vehicle, deliveries_high) == "warn"
    assert vehicle_compatibility.get_compatibility_level(vehicle, deliveries_over) == "fail"


# ============================================================
# v2 Tests — Consolidation Engine (Bin Packing)
# ============================================================

def test_consolidation_single_delivery():
    deliveries = [{"id": 1, "peso_kg": 100, "volume_m3": 0.5, "comprimento_cm": 80, "largura_cm": 60, "altura_cm": 50, "descricao": "Test"}]
    vehicles = [{"id": 1, "name": "Van", "tipo": "Van", "max_weight": 1500, "max_volume": 12, "max_length": 3.5, "max_width": 1.8, "max_height": 2, "cost_km": 1.2}]

    result = consolidation_engine.consolidate(deliveries, vehicles, route_distance_km=100)

    assert result["summary"]["allocated"] == 1
    assert result["summary"]["unallocated"] == 0
    assert result["summary"]["vehicles_used"] == 1
    assert result["total_cost"] == pytest.approx(120.0, abs=0.1)


def test_consolidation_multiple_vehicles():
    """Two heavy deliveries should require two vehicles if one can't hold both."""
    deliveries = [
        {"id": 1, "peso_kg": 800, "volume_m3": 5, "comprimento_cm": 100, "largura_cm": 80, "altura_cm": 60, "descricao": "Heavy 1"},
        {"id": 2, "peso_kg": 800, "volume_m3": 5, "comprimento_cm": 100, "largura_cm": 80, "altura_cm": 60, "descricao": "Heavy 2"},
    ]
    vehicles = [{"id": 1, "name": "Van", "tipo": "Van", "max_weight": 1000, "max_volume": 12, "max_length": 3, "max_width": 2, "max_height": 2, "cost_km": 1.0}]

    result = consolidation_engine.consolidate(deliveries, vehicles, route_distance_km=200)

    assert result["summary"]["vehicles_used"] == 2
    assert result["summary"]["allocated"] == 2


def test_consolidation_unallocated():
    """A delivery that exceeds all vehicle capacities should be unallocated."""
    deliveries = [{"id": 1, "peso_kg": 5000, "volume_m3": 50, "comprimento_cm": 500, "largura_cm": 300, "altura_cm": 200, "descricao": "Oversized"}]
    vehicles = [{"id": 1, "name": "Van", "tipo": "Van", "max_weight": 1500, "max_volume": 12, "max_length": 3.5, "max_width": 1.8, "max_height": 2, "cost_km": 1.2}]

    result = consolidation_engine.consolidate(deliveries, vehicles, route_distance_km=100)

    assert result["summary"]["unallocated"] == 1
    assert result["summary"]["allocated"] == 0
    assert len(result["alerts"]) > 0


def test_consolidation_empty_deliveries():
    result = consolidation_engine.consolidate([], [{"id": 1, "name": "Van"}], 100)
    assert result["summary"] == {}


def test_consolidation_occupation_percentage():
    deliveries = [{"id": 1, "peso_kg": 500, "volume_m3": 6, "comprimento_cm": 80, "largura_cm": 60, "altura_cm": 50}]
    vehicles = [{"id": 1, "name": "Van", "tipo": "Van", "max_weight": 1000, "max_volume": 12, "max_length": 3, "max_width": 2, "max_height": 2, "cost_km": 1.0}]

    result = consolidation_engine.consolidate(deliveries, vehicles, 100)

    assert len(result["allocations"]) == 1
    alloc = result["allocations"][0]
    assert alloc["occupation"]["weight_pct"] == pytest.approx(50.0, abs=0.1)
    assert alloc["occupation"]["volume_pct"] == pytest.approx(50.0, abs=0.1)
