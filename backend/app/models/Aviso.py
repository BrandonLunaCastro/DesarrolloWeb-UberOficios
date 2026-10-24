import enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship

from app.database import Base


class EstadoAvisoEnum(str, enum.Enum):
    ABIERTO = "ABIERTO"
    EN_PROCESO = "EN_PROCESO"
    CANCELADO = "CANCELADO"
    FINALIZADO = "FINALIZADO"


class Aviso(Base):
    __tablename__ = "aviso"

    id_aviso = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(
        Integer,
        ForeignKey("usuario.id_usuario", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    id_categoria = Column(
        Integer,
        ForeignKey("categoria.id_categoria", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    titulo = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)
    ubicacion = Column(String, nullable=False)
    estado = Column(
        ENUM(EstadoAvisoEnum, name="estado_aviso_enum", create_type=False),
        nullable=False,
        default=EstadoAvisoEnum.ABIERTO,
    )
    fecha_publicacion = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    cliente = relationship("Usuario", back_populates="avisos")
    categoria = relationship("Categoria", back_populates="avisos")
    postulaciones = relationship(
        "Postulacion",
        back_populates="aviso",
        cascade="all, delete-orphan",
    )