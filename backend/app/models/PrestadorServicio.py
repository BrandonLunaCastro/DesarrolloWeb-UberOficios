from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class PrestadorServicio(Base):
    __tablename__ = "prestador_servicio"

    id_prestador = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False, unique=True)
    telefono = Column(String, nullable=True)
    provincia = Column(String, nullable=True)
    departamento = Column(String, nullable=True)
    prom_calificacion = Column(Numeric(3, 2), nullable=True, default=0)
    creditos = Column(Integer, nullable=False, default=10)

    usuario = relationship("Usuario", back_populates="prestador")