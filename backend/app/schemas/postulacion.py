from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PostulacionCreate(BaseModel):
    presupuesto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    comentario: str | None = Field(default=None, max_length=2000)


class PostulacionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_postulacion: int
    id_aviso: int
    id_prestador: int
    id_cliente: int | None = None
    id_conversacion: int | None = None
    presupuesto: Decimal
    comentario: str | None = None
    fecha_postulacion: datetime
    estado: str
    titulo_aviso: str | None = None
    descripcion_aviso: str | None = None
    nombre_prestador: str | None = None
    apellido_prestador: str | None = None
    oficio_prestador: str | None = None
    nombre_cliente: str | None = None
    apellido_cliente: str | None = None
    zona_aviso: str | None = None


class PostulacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_postulacion: int
    id_aviso: int
    id_prestador: int
    presupuesto: Decimal
    comentario: str | None
    fecha_postulacion: datetime
    estado: str


class AceptarPostulacionResponse(BaseModel):
    id_postulacion: int
    estado: str
    id_conversacion: int