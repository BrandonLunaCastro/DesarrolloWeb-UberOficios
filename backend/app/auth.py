from passlib.context import CryptContext
from jose import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import joinedload
from app.database import SessionLocal
from app.models.usuario import Usuario

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
def hashear_contrasena(contrasena):

    return pwd_context.hash(contrasena)


# Verifica si una contraseña coincide con un hash.
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



# Permite recibir el token enviado como:
# Authorization: Bearer <token>
security = HTTPBearer()


# Obtiene y valida el usuario a partir del JWT.
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        id_usuario = payload.get("sub")

        if id_usuario is None:
            raise HTTPException(
                status_code=401,
                detail="Token inválido"
            )

        id_usuario = int(id_usuario)

    except (JWTError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado"
        )

    with SessionLocal() as db:
        usuario = (
            db.query(Usuario)
            .options(joinedload(Usuario.rol))
            .filter(Usuario.id_usuario == id_usuario)
            .first()
        )

    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail="Usuario no encontrado"
        )

    return usuario
