from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import relationship

from app.database import Base


class Conversacion(Base):
    __tablename__ = "conversacion"

    id_conversacion = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(
        Integer,
        ForeignKey("cliente.id_cliente", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_prestador = Column(
        Integer,
        ForeignKey("prestador_servicio.id_prestador", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fecha_creacion = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    fecha_actualizacion = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    cliente = relationship("Cliente", back_populates="conversaciones")
    prestador = relationship("PrestadorServicio", back_populates="conversaciones")
    mensajes = relationship(
        "Mensaje",
        back_populates="conversacion",
        cascade="all, delete-orphan",
        order_by="Mensaje.fecha_envio",
    )
