from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, func

from app.database import Base


class Notificacion(Base):
    __tablename__ = "notificacion"
    __table_args__ = (
        Index("ix_notificacion_usuario_fecha", "id_usuario", "fecha_creacion"),
    )

    id_notificacion = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False,
    )
    tipo = Column(String(30), nullable=False)
    mensaje = Column(Text, nullable=False)
    fecha_creacion = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    leida = Column(Boolean, nullable=False, default=False, server_default="false")