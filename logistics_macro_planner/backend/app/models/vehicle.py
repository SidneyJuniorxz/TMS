from sqlalchemy import Column, Integer, String, Float, Boolean
from ..database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    tipo = Column(String, default="Truck")  # Van, Truck, Carreta, etc.
    max_weight = Column(Float)   # kg
    max_volume = Column(Float)   # m³
    max_length = Column(Float)   # metros
    max_width = Column(Float)    # metros
    max_height = Column(Float)   # metros
    cost_km = Column(Float)      # R$/km
    ativo = Column(Boolean, default=True)
