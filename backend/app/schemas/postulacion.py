from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PostulacionCreate(BaseModel):
    presupuesto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    comentario: str | None = Field(default=None, max_length=2000)


class PostulacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_postulacion: int
    id_aviso: int
    id_prestador: int
    presupuesto: Decimal
    comentario: str | None
    fecha_postulacion: datetime
    estado: str