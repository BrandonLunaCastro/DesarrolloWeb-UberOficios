from typing import Literal

from pydantic import BaseModel


# Datos necesarios para iniciar sesión.
class LoginRequest(BaseModel):
    email: str
    contrasena: str


# Datos necesarios para registrar un usuario.
class RegisterRequest(BaseModel):
    nombre: str
    apellido: str
    email: str
    contrasena: str
    telefono: str | None = None
    rol: Literal["CLIENTE", "PRESTADOR"] = "CLIENTE"