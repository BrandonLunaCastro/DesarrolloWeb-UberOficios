import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class TipoTransaccionEnum(str, enum.Enum):
    RECARGA = "RECARGA"
    CONSUMO_POSTULACION = "CONSUMO_POSTULACION"
    DEVOLUCION = "DEVOLUCION"
    BONIFICACION = "BONIFICACION"


class EstadoCompraCreditoEnum(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    CANCELADA = "CANCELADA"


class PaqueteCredito(Base):
    __tablename__ = "paquete_credito"
    __table_args__ = (
        CheckConstraint("cantidad_creditos > 0", name="ck_paquete_credito_cantidad"),
        CheckConstraint("precio_centavos > 0", name="ck_paquete_credito_precio"),
    )

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(60), nullable=False, unique=True)
    cantidad_creditos = Column(Integer, nullable=False)
    precio_centavos = Column(Integer, nullable=False)
    moneda = Column(String(3), nullable=False, default="ARS", server_default="ARS")
    activo = Column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    orden = Column(Integer, nullable=False, default=0, server_default="0")
    fecha_creacion = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )
    fecha_actualizacion = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    compras = relationship("CompraCredito", back_populates="paquete")


class CompraCredito(Base):
    __tablename__ = "compra_credito"
    __table_args__ = (
        CheckConstraint("cantidad_creditos > 0", name="ck_compra_credito_cantidad"),
        CheckConstraint("precio_centavos > 0", name="ck_compra_credito_precio"),
        UniqueConstraint("referencia_pago", name="uq_compra_credito_referencia_pago"),
        UniqueConstraint("transaccion_id", name="uq_compra_credito_transaccion"),
    )

    id = Column(Integer, primary_key=True, index=True)
    prestador_id = Column(
        Integer,
        ForeignKey("prestador_servicio.id_prestador", ondelete="RESTRICT"),
        nullable=False,
    )
    paquete_id = Column(
        Integer,
        ForeignKey("paquete_credito.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cantidad_creditos = Column(Integer, nullable=False)
    precio_centavos = Column(Integer, nullable=False)
    moneda = Column(String(3), nullable=False)
    estado = Column(
        Enum(
            EstadoCompraCreditoEnum,
            native_enum=False,
            create_constraint=True,
            name="estado_compra_credito_enum",
        ),
        nullable=False,
        default=EstadoCompraCreditoEnum.PENDIENTE,
    )
    referencia_pago = Column(String(100), nullable=True)
    transaccion_id = Column(
        Integer,
        ForeignKey("transaccion_credito.id", ondelete="RESTRICT"),
        nullable=True,
    )
    preferencia_pago_id = Column(String(100), nullable=True)
    url_pago = Column(String(2048), nullable=True)
    fecha_creacion = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )
    fecha_acreditacion = Column(DateTime(timezone=True), nullable=True)

    prestador = relationship("PrestadorServicio")
    paquete = relationship("PaqueteCredito", back_populates="compras")
    transaccion = relationship("TransaccionCredito")


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