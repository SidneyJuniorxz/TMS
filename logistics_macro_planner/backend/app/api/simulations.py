from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.delivery import Delivery
from ..models.city import City
from ..models.vehicle import Vehicle
from ..models.simulation import Simulation, Route, RouteStop, simulation_deliveries, simulation_vehicles
from ..services import scenario_generator, plausibility_engine, vehicle_compatibility, sla_validator, optimizer, scenario_splitter, consolidation_engine
from ..utils.geo_utils import route_total_distance

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("/run")
def run_simulation(
    origin_city_id: int = Body(..., embed=True),
    delivery_ids: list[int] = Body(...),
    vehicle_ids: list[int] = Body(...),
    db: Session = Depends(get_db)
):
    # 1. Fetch data
    origin_city = db.query(City).filter(City.id == origin_city_id).first()
    if not origin_city:
        raise HTTPException(status_code=404, detail="Cidade de origem não encontrada")

    origin = {"lat": origin_city.lat, "lon": origin_city.lon, "city": origin_city.name}

    deliveries_db = db.query(Delivery).filter(Delivery.id.in_(delivery_ids)).all()
    if not deliveries_db:
        raise HTTPException(status_code=400, detail="Nenhuma entrega válida encontrada")

    deliveries = []
    for d in deliveries_db:
        # Resolve coordinates: prefer city_id lookup, fallback to no coords
        city = db.query(City).filter(City.id == d.city_id).first() if d.city_id else None

        deliveries.append({
            "id": d.id,
            "lat": city.lat if city else origin_city.lat,  # Fallback to origin coords
            "lon": city.lon if city else origin_city.lon,
            "peso_kg": d.peso_kg or d.weight or 0,
            "weight": d.peso_kg or d.weight or 0,  # Legacy compatibility
            "volume_m3": d.volume_m3 or d.volume or 0,
            "volume": d.volume_m3 or d.volume or 0,  # Legacy compatibility
            "comprimento_cm": d.comprimento_cm or 0,
            "largura_cm": d.largura_cm or 0,
            "altura_cm": d.altura_cm or 0,
            "deadline_days": d.deadline_days,
            "city": city.name if city else (d.destino_cidade or "Destino"),
            "city_id": city.id if city else d.city_id,
            "destino_cidade": d.destino_cidade or (city.name if city else ""),
            "destino_cep": d.destino_cep or "",
            "origem_cidade": d.origem_cidade or "",
            "origem_cep": d.origem_cep or "",
            "descricao": d.descricao or "",
            "prioridade": d.prioridade or "media",
            "observacao": d.observacao or "",
        })

    vehicles_db = db.query(Vehicle).filter(Vehicle.id.in_(vehicle_ids)).all()
    if not vehicles_db:
        raise HTTPException(status_code=400, detail="Nenhum veículo válido encontrado")

    vehicles = [{
        "id": v.id,
        "name": v.name,
        "tipo": v.tipo or "Truck",
        "max_weight": v.max_weight,
        "max_volume": v.max_volume,
        "max_length": v.max_length or 0,
        "max_width": v.max_width or 0,
        "max_height": v.max_height or 0,
        "cost_km": v.cost_km or 0,
    } for v in vehicles_db]

    # Create Simulation entry in DB
    db_simulation = Simulation(origin_city_id=origin_city_id, status="processing")
    db.add(db_simulation)
    db.commit()
    db.refresh(db_simulation)

    # Insert inputs relations
    for delivery_id in delivery_ids:
        db.execute(
            simulation_deliveries.insert().values(simulation_id=db_simulation.id, delivery_id=delivery_id)
        )
    for vehicle_id in vehicle_ids:
        db.execute(
            simulation_vehicles.insert().values(simulation_id=db_simulation.id, vehicle_id=vehicle_id)
        )
    db.commit()

    # 2. Generate Scenarios (using the clustered generator)
    scenarios = scenario_generator.generate_scenarios(deliveries)

    # 3. Process Scenarios
    results = []
    routes_to_save = []

    for scenario_stops in scenarios:
        for vehicle in vehicles:
            if not vehicle_compatibility.can_vehicle_handle_route(vehicle, scenario_stops):
                continue

            dist = route_total_distance(origin, scenario_stops)

            if not sla_validator.check_route_sla(dist, scenario_stops):
                continue

            plausibility = plausibility_engine.calculate_plausibility_score(origin, scenario_stops)

            # Scoring: plausibility penalizing distance
            final_score = plausibility["score"] - (dist * 0.01)
            final_score = max(0.0, round(final_score, 2))

            # Cost estimation
            estimated_cost = round(dist * vehicle.get("cost_km", 0), 2)

            results.append({
                "vehicle_id": vehicle["id"],
                "vehicle_name": vehicle["name"],
                "vehicle_tipo": vehicle.get("tipo", "Truck"),
                "stops": scenario_stops,
                "total_distance": dist,
                "plausibility_score": plausibility["score"],
                "plausibility_details": plausibility["details"],
                "final_score": final_score,
                "estimated_cost": estimated_cost,
            })

    # 4. Optimize / Pick Best
    best = {}
    if results:
        best = sorted(results, key=lambda x: x["final_score"], reverse=True)[0]

    # 5. Run Consolidation Engine (Bin Packing)
    best_distance = best.get("total_distance", 0) if best else 0
    consolidation = consolidation_engine.consolidate(deliveries, vehicles, best_distance)

    # 6. Persist Routes in DB
    for res in results:
        is_best = (res == best)
        db_route = Route(
            simulation_id=db_simulation.id,
            vehicle_id=res["vehicle_id"],
            total_distance=res["total_distance"],
            plausibility_score=res["plausibility_score"],
            final_score=res["final_score"],
            approved=res["plausibility_score"] >= 60,
            is_best=is_best
        )
        db.add(db_route)
        db.commit()
        db.refresh(db_route)

        # Save stops
        for idx, stop in enumerate(res["stops"]):
            db_stop = RouteStop(
                route_id=db_route.id,
                city_id=stop.get("city_id"),
                stop_order=idx
            )
            db.add(db_stop)
        db.commit()

    db_simulation.status = "completed"
    db.commit()

    # Calculate outlier split recommendation for the best route
    split_recommendation = None
    if best and len(best.get("stops", [])) >= 3:
        split_res = scenario_splitter.split_by_outlier(origin, best["stops"])
        if split_res["should_split"]:
            split_recommendation = {
                "should_split": True,
                "gain": split_res["gain"],
                "isolated_stop": split_res["isolated_stop"]["city"],
                "remaining_route": [s["city"] for s in split_res["remaining_route"]],
                "message": f"Separar '{split_res['isolated_stop']['city']}' melhora o score de plausibilidade em {split_res['gain']} pontos."
            }

    return {
        "simulation_id": db_simulation.id,
        "summary": {
            "scenarios_generated": len(scenarios),
            "valid_scenarios_found": len(results),
        },
        "best_scenario": {
            "vehicle": best.get("vehicle_name") if best else None,
            "vehicle_tipo": best.get("vehicle_tipo") if best else None,
            "stops": [s["city"] for s in best["stops"]] if best else [],
            "stops_detailed": best.get("stops", []) if best else [],
            "total_distance": best.get("total_distance") if best else 0,
            "plausibility_score": best.get("plausibility_score") if best else 0,
            "final_score": best.get("final_score") if best else 0,
            "estimated_cost": best.get("estimated_cost") if best else 0,
            "split_recommendation": split_recommendation
        },
        "consolidation": consolidation,
    }


@router.get("/")
def list_simulations(db: Session = Depends(get_db)):
    simulations = db.query(Simulation).order_by(Simulation.id.desc()).all()
    results = []
    for sim in simulations:
        # Get best route
        best_route = db.query(Route).filter(Route.simulation_id == sim.id, Route.is_best == True).first()
        best_route_data = None
        if best_route:
            vehicle = db.query(Vehicle).filter(Vehicle.id == best_route.vehicle_id).first()
            stops_db = db.query(RouteStop).filter(RouteStop.route_id == best_route.id).order_by(RouteStop.stop_order).all()
            stops = []
            for s in stops_db:
                city = db.query(City).filter(City.id == s.city_id).first()
                stops.append(city.name if city else "Unknown")

            best_route_data = {
                "vehicle": vehicle.name if vehicle else "Unknown",
                "stops": stops,
                "total_distance": best_route.total_distance,
                "plausibility_score": best_route.plausibility_score,
                "final_score": best_route.final_score
            }

        origin = db.query(City).filter(City.id == sim.origin_city_id).first()
        results.append({
            "id": sim.id,
            "origin": origin.name if origin else "Unknown",
            "created_at": sim.created_at,
            "status": sim.status,
            "best_route": best_route_data
        })
    return results


@router.get("/{simulation_id}")
def get_simulation_details(simulation_id: int, db: Session = Depends(get_db)):
    sim = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulação não encontrada")

    origin = db.query(City).filter(City.id == sim.origin_city_id).first()
    origin_dict = {"lat": origin.lat, "lon": origin.lon, "city": origin.name} if origin else None

    # Get all routes for this simulation
    routes_db = db.query(Route).filter(Route.simulation_id == sim.id).order_by(Route.final_score.desc()).all()
    routes = []
    for r in routes_db:
        vehicle = db.query(Vehicle).filter(Vehicle.id == r.vehicle_id).first()
        stops_db = db.query(RouteStop).filter(RouteStop.route_id == r.id).order_by(RouteStop.stop_order).all()
        stops = []
        stops_detailed = []
        for s in stops_db:
            city = db.query(City).filter(City.id == s.city_id).first()
            if city:
                stops.append(city.name)
                stops_detailed.append({
                    "city": city.name,
                    "lat": city.lat,
                    "lon": city.lon
                })

        routes.append({
            "id": r.id,
            "vehicle": vehicle.name if vehicle else "Unknown",
            "vehicle_tipo": vehicle.tipo if vehicle else "Truck",
            "total_distance": r.total_distance,
            "plausibility_score": r.plausibility_score,
            "final_score": r.final_score,
            "estimated_cost": round(r.total_distance * (vehicle.cost_km if vehicle else 0), 2),
            "approved": r.approved,
            "is_best": r.is_best,
            "stops": stops,
            "stops_detailed": stops_detailed
        })

    # Split recommendation for best route
    best_route = next((r for r in routes if r["is_best"]), None)
    split_recommendation = None
    if best_route and len(best_route["stops_detailed"]) >= 3 and origin_dict:
        split_res = scenario_splitter.split_by_outlier(origin_dict, best_route["stops_detailed"])
        if split_res["should_split"]:
            split_recommendation = {
                "should_split": True,
                "gain": split_res["gain"],
                "isolated_stop": split_res["isolated_stop"]["city"],
                "remaining_route": [s["city"] for s in split_res["remaining_route"]],
                "message": f"Separar '{split_res['isolated_stop']['city']}' melhora o score em {split_res['gain']} pontos."
            }

    return {
        "id": sim.id,
        "origin": origin_dict,
        "created_at": sim.created_at,
        "status": sim.status,
        "routes": routes,
        "split_recommendation": split_recommendation
    }


@router.delete("/{simulation_id}")
def delete_simulation(simulation_id: int, db: Session = Depends(get_db)):
    sim = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulação não encontrada")

    db.delete(sim)
    db.commit()
    return {"message": f"Simulação {simulation_id} removida com sucesso"}
