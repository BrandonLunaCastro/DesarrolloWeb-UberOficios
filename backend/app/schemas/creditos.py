from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.creditos import TipoTransaccionEnum


class TransaccionCreditoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    billetera_id: int
    monto: int
    tipo: TipoTransaccionEnum
    referencia_id: int | None
    referencia_tipo: str | None
    descripcion: str | None
    fecha_registro: datetime
