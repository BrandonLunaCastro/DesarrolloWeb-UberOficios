from pydantic import BaseModel, Field


class AvisoCreate(BaseModel):
    oficio: str = Field(min_length=1)
    descripcion: str = Field(min_length=1)
    zona: str = Field(min_length=1)
    telefono: str | None = None