from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import relationship
from app.database import Base


class PrestadorServicio(Base):
    __tablename__ = "prestador_servicio"

    id_prestador = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(
        Integer,
        ForeignKey("usuario.id_usuario", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True,
    )
    matricula = Column(String(50), nullable=True)
    biografia = Column(Text, nullable=True)
    telefono = Column(String(20), nullable=True)
    provincia = Column(String(100), nullable=True)
    departamento = Column(String(100), nullable=True)
    zona = Column(String(150), nullable=True)
    oficio = Column(String(100), nullable=True)
    prom_calificacion = Column(Numeric(3, 2), nullable=True, default=0)
    creditos = Column(Integer, nullable=False, default=10)
    saldo_creditos = Column(Integer, nullable=False, server_default=text("0"))
    activo = Column(Boolean, nullable=False, default=True)
    inicio_ciclo_creditos = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    meses_creditos_otorgados = Column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    usuario = relationship("Usuario", back_populates="prestador")