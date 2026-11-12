from datetime import datetime

from pydantic import BaseModel, Field


class CalificacionCreate(BaseModel):
    id_postulacion: int = Field(gt=0)
    puntuacion: int = Field(ge=1, le=5)
    comentario: str | None = Field(default=None, max_length=2000)


class CalificacionResponse(BaseModel):
    id_calificacion: int
    id_postulacion: int
    id_prestador: int
    puntuacion: int
    comentario: str | None
    fecha: datetime