from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Postulacion(Base):
    __tablename__ = "postulacion"
    __table_args__ = (
        UniqueConstraint("id_aviso", "id_prestador", name="uq_postulacion_aviso_prestador"),
    )

    id_postulacion = Column(Integer, primary_key=True, index=True)
    id_aviso = Column(
        Integer,
        ForeignKey("aviso.id_aviso", ondelete="CASCADE"),
        nullable=False,
    )
    id_prestador = Column(
        Integer,
        ForeignKey("prestador_servicio.id_prestador", ondelete="CASCADE"),
        nullable=False,
    )
    presupuesto = Column(Numeric(12, 2), nullable=False)
    comentario = Column(Text, nullable=True)
    fecha_postulacion = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    estado = Column(String(30), nullable=False, default="PENDIENTE", server_default="PENDIENTE")

    aviso = relationship("Aviso", back_populates="postulaciones")
    prestador = relationship("PrestadorServicio", back_populates="postulaciones")
    conversacion = relationship(
        "Conversacion",
        back_populates="postulacion",
        uselist=False,
    )