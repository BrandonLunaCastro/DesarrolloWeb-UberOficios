import enum
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class TipoTransaccionEnum(str, enum.Enum):
    RECARGA = "RECARGA"
    CONSUMO_POSTULACION = "CONSUMO_POSTULACION"
    DEVOLUCION = "DEVOLUCION"
    BONIFICACION = "BONIFICACION"


class BilleteraCredito(Base):
    __tablename__ = "billetera_credito"

    id = Column(Integer, primary_key=True, index=True)
    prestador_id = Column(
        Integer,
        ForeignKey("prestador_servicio.id_prestador", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    saldo_actual = Column(Integer, default=0, nullable=False)
    fecha_actualizacion = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    prestador = relationship("PrestadorServicio", back_populates="billetera")
    transacciones = relationship(
        "TransaccionCredito",
        back_populates="billetera",
        cascade="all, delete-orphan",
    )


class TransaccionCredito(Base):
    __tablename__ = "transaccion_credito"

    id = Column(Integer, primary_key=True, index=True)
    billetera_id = Column(
        Integer,
        ForeignKey("billetera_credito.id", ondelete="CASCADE"),
        nullable=False,
    )
    monto = Column(Integer, nullable=False)
    tipo = Column(Enum(TipoTransaccionEnum), nullable=False)
    referencia_id = Column(Integer, nullable=True)
    referencia_tipo = Column(String(50), nullable=True)
    descripcion = Column(String(255), nullable=True)
    fecha_registro = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    billetera = relationship("BilleteraCredito", back_populates="transacciones")