from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from ..database import Base

simulation_deliveries = Table(
    "simulation_deliveries",
    Base.metadata,
    Column("simulation_id", Integer, ForeignKey("simulations.id", ondelete="CASCADE"), primary_key=True),
    Column("delivery_id", Integer, ForeignKey("deliveries.id", ondelete="CASCADE"), primary_key=True)
)

simulation_vehicles = Table(
    "simulation_vehicles",
    Base.metadata,
    Column("simulation_id", Integer, ForeignKey("simulations.id", ondelete="CASCADE"), primary_key=True),
    Column("vehicle_id", Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), primary_key=True)
)

class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    origin_city_id = Column(Integer, ForeignKey("cities.id"))
    created_at = Column(String)  # SQLite default TIMESTAMP string
    status = Column(String, default="completed")

    origin_city = relationship("City")
    deliveries = relationship("Delivery", secondary=simulation_deliveries)
    vehicles = relationship("Vehicle", secondary=simulation_vehicles)
    routes = relationship("Route", back_populates="simulation", cascade="all, delete-orphan")

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"))
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    total_distance = Column(Float)
    plausibility_score = Column(Float)
    final_score = Column(Float)
    approved = Column(Boolean)
    is_best = Column(Boolean, default=False)

    simulation = relationship("Simulation", back_populates="routes")
    vehicle = relationship("Vehicle")
    stops = relationship("RouteStop", back_populates="route", order_by="RouteStop.stop_order", cascade="all, delete-orphan")

class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"))
    city_id = Column(Integer, ForeignKey("cities.id"))
    stop_order = Column(Integer)

    route = relationship("Route", back_populates="stops")
    city = relationship("City")
