from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.vehicle import Vehicle
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


# --- Pydantic Schemas ---

class VehicleCreate(BaseModel):
    name: str
    tipo: Optional[str] = "Truck"
    max_weight: float
    max_volume: float
    max_length: Optional[float] = 0
    max_width: Optional[float] = 0
    max_height: Optional[float] = 0
    cost_km: float = 0

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Nome do veículo é obrigatório")
        return v.strip()

    @field_validator("max_weight")
    @classmethod
    def weight_positive(cls, v):
        if v <= 0:
            raise ValueError("Peso máximo deve ser maior que zero")
        return v

    @field_validator("max_volume")
    @classmethod
    def volume_positive(cls, v):
        if v <= 0:
            raise ValueError("Volume máximo deve ser maior que zero")
        return v


class VehicleUpdate(BaseModel):
    name: Optional[str] = None
    tipo: Optional[str] = None
    max_weight: Optional[float] = None
    max_volume: Optional[float] = None
    max_length: Optional[float] = None
    max_width: Optional[float] = None
    max_height: Optional[float] = None
    cost_km: Optional[float] = None
    ativo: Optional[bool] = None


class VehicleResponse(BaseModel):
    id: int
    name: str
    tipo: Optional[str] = "Truck"
    max_weight: float
    max_volume: float
    max_length: Optional[float] = 0
    max_width: Optional[float] = 0
    max_height: Optional[float] = 0
    cost_km: float
    ativo: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


# --- Endpoints ---

@router.get("/", response_model=list[VehicleResponse])
def list_vehicles(include_inactive: bool = False, db: Session = Depends(get_db)):
    query = db.query(Vehicle)
    if not include_inactive:
        query = query.filter((Vehicle.ativo == True) | (Vehicle.ativo == None))
    return query.all()


@router.post("/", response_model=VehicleResponse)
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    db_vehicle = Vehicle(
        name=vehicle.name,
        tipo=vehicle.tipo or "Truck",
        max_weight=vehicle.max_weight,
        max_volume=vehicle.max_volume,
        max_length=vehicle.max_length or 0,
        max_width=vehicle.max_width or 0,
        max_height=vehicle.max_height or 0,
        cost_km=vehicle.cost_km,
        ativo=True,
    )
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(vehicle_id: int, vehicle: VehicleUpdate, db: Session = Depends(get_db)):
    db_vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not db_vehicle:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    update_data = vehicle.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_vehicle, key, value)

    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    db_vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not db_vehicle:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    db.delete(db_vehicle)
    db.commit()
    return {"message": f"Veículo '{db_vehicle.name}' removido com sucesso"}


@router.patch("/{vehicle_id}/toggle", response_model=VehicleResponse)
def toggle_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    db_vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not db_vehicle:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    db_vehicle.ativo = not db_vehicle.ativo
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle
