from datetime import datetime
from uuid import UUID

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class MensajeCreate(BaseModel):
    # El UUID identifica de forma estable el mismo mensaje si el cliente reintenta el envío.
    contenido: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    identificador_unico: UUID


class MensajeResponse(BaseModel):
    # Estructura común para respuestas HTTP e historiales enviados por WebSocket.
    model_config = ConfigDict(from_attributes=True)

    id_mensaje: int
    conversacion_id: int
    remitente_id: int
    contenido: str
    identificador_unico: UUID | None
    fecha_envio: datetime
