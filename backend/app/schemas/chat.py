from datetime import datetime
from uuid import UUID

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class MensajeCreate(BaseModel):
    contenido: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    identificador_unico: UUID


class MensajeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_mensaje: int
    conversacion_id: int
    remitente_id: int
    contenido: str
    identificador_unico: UUID | None
    fecha_envio: datetime
