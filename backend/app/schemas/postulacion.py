from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PostulacionCreate(BaseModel):
    # El prestador envía un único precio positivo y un comentario opcional.
    presupuesto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    comentario: str | None = Field(default=None, max_length=2000)


class PostulacionListItem(BaseModel):
    # Campos combinados de aviso, propuesta y participantes para las vistas de presupuestos.
    model_config = ConfigDict(from_attributes=True)

    id_postulacion: int
    id_aviso: int
    id_prestador: int
    id_cliente: int | None = None
    id_conversacion: int | None = None
    id_calificacion: int | None = None
    presupuesto: Decimal
    presupuesto_minimo: Decimal | None = None
    presupuesto_maximo: Decimal | None = None
    comentario: str | None = None
    fecha_postulacion: datetime
    estado: str
    titulo_aviso: str | None = None
    oficio_aviso: str | None = None
    descripcion_aviso: str | None = None
    nombre_prestador: str | None = None
    apellido_prestador: str | None = None
    oficio_prestador: str | None = None
    nombre_cliente: str | None = None
    apellido_cliente: str | None = None
    zona_aviso: str | None = None
    estado_aviso: str | None = None


class PostulacionPresupuestoUpdate(BaseModel):
    # Se valida el nuevo importe antes de que el servicio compruebe permisos y estado.
    presupuesto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class PostulacionResponse(BaseModel):
    # Representación de una postulación individual creada o modificada.
    model_config = ConfigDict(from_attributes=True)

    id_postulacion: int
    id_aviso: int
    id_prestador: int
    presupuesto: Decimal
    comentario: str | None
    fecha_postulacion: datetime
    estado: str


class AceptarPostulacionResponse(BaseModel):
    # Incluye el chat creado al aceptar para que el cliente pueda abrirlo directamente.
    id_postulacion: int
    estado: str
    id_conversacion: int