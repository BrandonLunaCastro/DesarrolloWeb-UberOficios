from passlib.context import CryptContext
from jose import jwt


# Configuración para hashear o verificar contraseñas.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# Configuración del JWT.
# Por ahora dejamos la clave directamente en el código.
# Más adelante la vamos a pasar al archivo .env.
SECRET_KEY = "clave-secreta-uberoficios"

ALGORITHM = "HS256"


# Hashea una contraseña.
#
# Ejemplo:
# "123456" → "$2b$12$...."
#
# Nunca vamos a guardar la contraseña original
# directamente en la base de datos.
def hashear_contrasena(contrasena):

    return pwd_context.hash(contrasena)


# Verifica si una contraseña coincide con un hash.
#
# contraseña → la que escribió el usuario
# contraseña_hash → la que tenemos guardada en la BD
def verificar_contrasena(contrasena, contrasena_hash):

    return pwd_context.verify(
        contrasena,
        contrasena_hash
    )


# Crea un token JWT.
def crear_token(data: dict):

    return jwt.encode(
        data,
        SECRET_KEY,
        algorithm=ALGORITHM
    )