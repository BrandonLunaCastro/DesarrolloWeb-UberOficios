from pydantic import BaseModel


class PerfilUpdate(BaseModel):
    # Todos los campos son opcionales para permitir actualizaciones parciales.
    zona: str | None = None
    oficio: str | None = None
    telefono: str | None = None
    biografia: str | None = None