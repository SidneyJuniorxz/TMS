from sqlalchemy import Column, Integer, Float, String, ForeignKey
from ..database import Base


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)

    # Legacy field — kept nullable for backward compatibility with old data
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=True)

    # Origin
    origem_cidade = Column(String, nullable=False, default="")
    origem_cep = Column(String, nullable=False, default="")

    # Destination
    destino_cidade = Column(String, nullable=False, default="")
    destino_cep = Column(String, nullable=False, default="")

    # Physical attributes
    peso_kg = Column(Float, nullable=False, default=0.0)
    comprimento_cm = Column(Float, nullable=False, default=0.0)
    largura_cm = Column(Float, nullable=False, default=0.0)
    altura_cm = Column(Float, nullable=False, default=0.0)
    volume_m3 = Column(Float, nullable=False, default=0.0)  # auto-calculated

    # SLA
    deadline_days = Column(Integer, nullable=False, default=5)

    # Descriptive
    descricao = Column(String, nullable=True, default="")
    prioridade = Column(String, nullable=True, default="media")  # alta, media, baixa
    observacao = Column(String, nullable=True, default="")

    # Legacy fields kept for migration — mapped from old data
    # weight -> peso_kg, volume -> volume_m3
    weight = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
