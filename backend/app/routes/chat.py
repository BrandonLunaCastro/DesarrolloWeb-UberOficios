from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.async_database import get_async_db
from app.auth import get_current_user_id
from app.schemas.chat import MensajeCreate, MensajeResponse
from app.services.chat import crear_mensaje, obtener_historial_mensajes


router = APIRouter(prefix="/conversaciones", tags=["Chat"])


@router.post(
    "/{id_conversacion}/mensajes",
    response_model=MensajeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enviar_mensaje(
    id_conversacion: int,
    datos: MensajeCreate,
    db: AsyncSession = Depends(get_async_db),
    id_usuario: int = Depends(get_current_user_id),
):
    return await crear_mensaje(
        db,
        id_conversacion=id_conversacion,
        id_usuario=id_usuario,
        datos=datos,
    )


@router.get(
    "/{id_conversacion}/mensajes",
    response_model=list[MensajeResponse],
)
async def consultar_historial(
    id_conversacion: int,
    db: AsyncSession = Depends(get_async_db),
    id_usuario: int = Depends(get_current_user_id),
):
    return await obtener_historial_mensajes(
        db,
        id_conversacion=id_conversacion,
        id_usuario=id_usuario,
    )
