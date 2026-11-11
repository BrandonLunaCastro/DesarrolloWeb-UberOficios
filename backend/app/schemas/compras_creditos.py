from datetime import datetime

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


class CompraCreditoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    paquete_id: int
    paquete_nombre: str | None = None
    cantidad_creditos: int
    precio_centavos: int
    moneda: str
    estado: EstadoCompraCreditoEnum
    url_pago: str | None
    fecha_creacion: datetime
    fecha_acreditacion: datetime | None
