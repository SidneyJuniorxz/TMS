from sqlalchemy import Column, Integer, String, Float
from ..database import Base

class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    lat = Column(Float)
    lon = Column(Float)
