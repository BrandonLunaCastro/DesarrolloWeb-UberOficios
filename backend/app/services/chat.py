from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.Cliente import Cliente
from app.models.PrestadorServicio import PrestadorServicio
from app.models.conversacion import Conversacion
from app.models.mensaje import Mensaje
from app.schemas.chat import MensajeCreate


async def _obtener_conversacion_participante(
    db: AsyncSession,
    *,
    id_conversacion: int,
    id_usuario: int,
) -> Conversacion:
    conversacion = await db.get(Conversacion, id_conversacion)
    if conversacion is None:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    id_cliente = await db.scalar(
        select(Cliente.id_cliente).where(Cliente.id_usuario == id_usuario)
    )
    if id_cliente == conversacion.id_cliente:
        return conversacion

    id_prestador = await db.scalar(
        select(PrestadorServicio.id_prestador).where(
            PrestadorServicio.id_usuario == id_usuario
        )
    )
    if id_prestador == conversacion.id_prestador:
        return conversacion

    raise HTTPException(
        status_code=403,
        detail="No tenés permiso para acceder a esta conversación",
    )


async def crear_mensaje(
    db: AsyncSession,
    *,
    id_conversacion: int,
    id_usuario: int,
    datos: MensajeCreate,
) -> Mensaje:
    await _obtener_conversacion_participante(
        db,
        id_conversacion=id_conversacion,
        id_usuario=id_usuario,
    )

    mensaje = Mensaje(
        conversacion_id=id_conversacion,
        remitente_id=id_usuario,
        contenido=datos.contenido,
    )
    db.add(mensaje)
    await db.commit()
    await db.refresh(mensaje)
    return mensaje


async def obtener_historial_mensajes(
    db: AsyncSession,
    *,
    id_conversacion: int,
    id_usuario: int,
) -> list[Mensaje]:
    await _obtener_conversacion_participante(
        db,
        id_conversacion=id_conversacion,
        id_usuario=id_usuario,
    )

    mensajes = await db.scalars(
        select(Mensaje)
        .where(Mensaje.conversacion_id == id_conversacion)
        .order_by(Mensaje.fecha_envio.asc(), Mensaje.id_mensaje.asc())
    )
    return list(mensajes.all())
