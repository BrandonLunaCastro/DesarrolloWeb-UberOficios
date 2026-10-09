from pydantic import BaseModel


class PerfilUpdate(BaseModel):
    zona: str | None = None
    oficio: str | None = None
    telefono: str | None = None