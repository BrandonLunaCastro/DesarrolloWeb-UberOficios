from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database import Base


class Conversacion(Base):
    __tablename__ = "conversacion"
    __table_args__ = (
        UniqueConstraint(
            "id_postulacion",
            name="uq_conversacion_id_postulacion",
        ),
    )

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
    id_postulacion = Column(
        Integer,
        ForeignKey("postulacion.id_postulacion", ondelete="SET NULL"),
        nullable=True,
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
    oculta_para_cliente = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    oculta_para_prestador = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    cliente = relationship("Cliente", back_populates="conversaciones")
    prestador = relationship("PrestadorServicio", back_populates="conversaciones")
    postulacion = relationship("Postulacion", back_populates="conversacion")
    mensajes = relationship(
        "Mensaje",
        back_populates="conversacion",
        cascade="all, delete-orphan",
        order_by="Mensaje.fecha_envio",
    )
