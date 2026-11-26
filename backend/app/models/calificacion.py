from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Calificacion(Base):
    # Una sola calificación por postulación aceptada; la BD también limita la puntuación a 1–5.
    __tablename__ = "calificacion"
    __table_args__ = (
        CheckConstraint("puntuacion BETWEEN 1 AND 5", name="ck_calificacion_puntuacion"),
        UniqueConstraint("id_postulacion", name="uq_calificacion_postulacion"),
    )

    id_calificacion = Column(Integer, primary_key=True, index=True)
    id_postulacion = Column(
        Integer,
        ForeignKey("postulacion.id_postulacion", ondelete="CASCADE"),
        nullable=False,
    )
    id_cliente = Column(
        Integer,
        ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False,
    )
    id_prestador = Column(
        Integer,
        ForeignKey("prestador_servicio.id_prestador", ondelete="CASCADE"),
        nullable=False,
    )
    puntuacion = Column(Integer, nullable=False)
    comentario = Column(Text, nullable=True)
    url_comprobante = Column(String(2048), nullable=True)
    public_id_comprobante = Column(String(255), nullable=True)
    fecha = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    cliente = relationship("Usuario")
    postulacion = relationship("Postulacion", back_populates="calificacion")
    prestador = relationship("PrestadorServicio")