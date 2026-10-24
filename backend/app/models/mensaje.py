from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class Mensaje(Base):
    __tablename__ = "mensaje"

    id_mensaje = Column(Integer, primary_key=True, index=True)
    conversacion_id = Column(
        Integer,
        ForeignKey("conversacion.id_conversacion", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    remitente_id = Column(
        Integer,
        ForeignKey("usuario.id_usuario", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    contenido = Column(Text, nullable=False)
    fecha_envio = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    conversacion = relationship("Conversacion", back_populates="mensajes")
    remitente = relationship("Usuario", back_populates="mensajes_enviados")
