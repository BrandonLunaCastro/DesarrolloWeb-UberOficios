from pydantic import BaseModel, Field


class AvisoCreate(BaseModel):
    # Valida los campos mínimos antes de que la ruta consulte o escriba en la BD.
    oficio: str = Field(min_length=1)
    descripcion: str = Field(min_length=1)
    zona: str = Field(min_length=1)
    telefono: str | None = None