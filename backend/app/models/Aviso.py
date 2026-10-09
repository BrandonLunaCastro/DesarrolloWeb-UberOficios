from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class Aviso(Base):
    __tablename__ = "aviso"

    id_aviso = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey("cliente.id_cliente"), nullable=False)
    oficio = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)
    zona = Column(String, nullable=False)
    telefono = Column(String, nullable=True)
    estado = Column(String, nullable=False, default="pendiente")
    fecha_creacion = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    cliente = relationship("Cliente", back_populates="avisos")