from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.async_database import AsyncSessionLocal, get_async_db
from app.auth import get_current_user_id, get_user_id_from_token
from app.schemas.chat import MensajeCreate, MensajeResponse
from app.services.chat import (
    _obtener_conversacion_participante,
    crear_mensaje,
    listar_conversaciones,
    obtener_historial_mensajes,
)
from app.services.chat_realtime import chat_connections


router = APIRouter(prefix="/conversaciones", tags=["Chat"])


@router.get("")
async def consultar_conversaciones(
    db: AsyncSession = Depends(get_async_db),
    id_usuario: int = Depends(get_current_user_id),
):
    return await listar_conversaciones(db, id_usuario=id_usuario)


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
    mensaje = await crear_mensaje(
        db,
        id_conversacion=id_conversacion,
        id_usuario=id_usuario,
        datos=datos,
    )
    await chat_connections.broadcast(
        id_conversacion,
        MensajeResponse.model_validate(mensaje).model_dump(mode="json"),
    )
    return mensaje


@router.get(
    "/{id_conversacion}/mensajes",
    response_model=list[MensajeResponse],
)
async def consultar_historial(
    id_conversacion: int,
    after_id: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_async_db),
    id_usuario: int = Depends(get_current_user_id),
):
    return await obtener_historial_mensajes(
        db,
        id_conversacion=id_conversacion,
        id_usuario=id_usuario,
        despues_de_id=after_id,
    )


@router.websocket("/{id_conversacion}/ws")
async def conectar_chat(
    websocket: WebSocket,
    id_conversacion: int,
    token: str | None = Query(default=None),
    after_id: int = Query(default=0, ge=0),
):
    await websocket.accept()

    try:
        if not token:
            await websocket.close(code=4401, reason="Autenticación requerida")
            return
        try:
            id_usuario = get_user_id_from_token(token)
        except HTTPException:
            await websocket.close(code=4401, reason="Token inválido")
            return

        async with AsyncSessionLocal() as db:
            try:
                await _obtener_conversacion_participante(
                    db,
                    id_conversacion=id_conversacion,
                    id_usuario=id_usuario,
                )
            except HTTPException as error:
                if error.status_code == 403:
                    await websocket.close(code=4403, reason="Acceso denegado")
                elif error.status_code == 404:
                    await websocket.close(code=4404, reason="Conversación no encontrada")
                else:
                    raise
                return

        async with chat_connections.lock_for(id_conversacion):
            chat_connections.connect(id_conversacion, websocket)
            async with AsyncSessionLocal() as db:
                mensajes = await obtener_historial_mensajes(
                    db,
                    id_conversacion=id_conversacion,
                    id_usuario=id_usuario,
                    despues_de_id=after_id,
                )
            for mensaje in mensajes:
                await websocket.send_json({
                    "type": "message",
                    "message": MensajeResponse.model_validate(mensaje).model_dump(mode="json"),
                })

        while True:
            await websocket.receive_text()
            await websocket.close(code=1008, reason="El socket solo admite recepción")
            break
    except WebSocketDisconnect:
        pass
    finally:
        async with chat_connections.lock_for(id_conversacion):
            chat_connections.disconnect(id_conversacion, websocket)
