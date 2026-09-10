from passlib.context import CryptContext
from jose import jwt

#Configuracion para encriptar o verificar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#configuracion del jwt
#secret key momentaneamente visible
SECRET_KEY = "clave-secreta-uberoficios"
ALGORITHM = "HS256"


def verificar_contrasena(contrasena, contrasena_hash):
    return pwd_context.verify(contrasena, contrasena_hash)


def crear_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
