from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.creditos import EstadoCompraCreditoEnum


class PaqueteCreditoResponse(BaseModel):
    # Datos públicos de un paquete disponible para iniciar una compra.
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    cantidad_creditos: int
    precio_centavos: int
    moneda: str


class IniciarCompraRequest(BaseModel):
    # La cantidad y el precio se obtienen del paquete en el servidor, no del cliente.
    paquete_id: int


class CompraCreditoResponse(BaseModel):
    # Estado de la compra y URL externa para completar el checkout, si existe.
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
