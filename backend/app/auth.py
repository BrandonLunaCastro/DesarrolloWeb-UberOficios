from passlib.context import CryptContext
from jose import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload
from app.async_database import get_async_db
from app.database import get_db
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
def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    return _get_authenticated_user_id(credentials)


def get_current_user(
    id_usuario: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
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


async def get_current_user_async(
    id_usuario: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_db),
):
    result = await db.execute(
        select(Usuario)
        .options(joinedload(Usuario.rol))
        .where(Usuario.id_usuario == id_usuario)
    )
    usuario = result.scalar_one_or_none()

    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail="Usuario no encontrado"
        )

    return usuario


def _get_authenticated_user_id(
    credentials: HTTPAuthorizationCredentials,
) -> int:
    return get_user_id_from_token(credentials.credentials)


def get_user_id_from_token(token: str) -> int:
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
    return id_usuario
