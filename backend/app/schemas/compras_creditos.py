from datetime import datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.creditos import EstadoCompraCreditoEnum


class PaqueteCreditoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    cantidad_creditos: int
    precio_centavos: int
    moneda: str


class IniciarCompraRequest(BaseModel):
    paquete_id: int


class SimularPagoRequest(BaseModel):
    resultado: Literal[
        EstadoCompraCreditoEnum.APROBADA,
        EstadoCompraCreditoEnum.RECHAZADA,
        EstadoCompraCreditoEnum.CANCELADA,
    ]


class CompraCreditoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    paquete_id: int
    paquete_nombre: str | None = None
    cantidad_creditos: int
    precio_centavos: int
    moneda: str
    estado: EstadoCompraCreditoEnum
    fecha_creacion: datetime
    fecha_acreditacion: datetime | None
