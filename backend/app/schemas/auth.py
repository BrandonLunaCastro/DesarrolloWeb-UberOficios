from pydantic import BaseModel


# Datos necesarios para iniciar sesión.
class LoginRequest(BaseModel):
    correo: str
    contrasena: str


# Datos necesarios para registrar un usuario.
class RegisterRequest(BaseModel):
    nombre_apellido: str
    correo: str
    contrasena: str