from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.Aviso import Aviso
from app.models.Cliente import Cliente
from app.models.PrestadorServicio import PrestadorServicio
from app.models.conversacion import Conversacion
from app.models.mensaje import Mensaje
from app.models.postulacion import Postulacion
from app.schemas.chat import MensajeCreate
from app.models.usuario import Usuario


async def listar_conversaciones(
    db: AsyncSession,
    *,
    id_usuario: int,
) -> list[dict]:
    id_cliente = await db.scalar(
        select(Cliente.id_cliente).where(Cliente.id_usuario == id_usuario)
    )
    id_prestador = await db.scalar(
        select(PrestadorServicio.id_prestador).where(
            PrestadorServicio.id_usuario == id_usuario
        )
    )
    condiciones = []
    if id_cliente is not None:
        condiciones.append(Conversacion.id_cliente == id_cliente)
    if id_prestador is not None:
        condiciones.append(Conversacion.id_prestador == id_prestador)
    if not condiciones:
        return []

    conversaciones = await db.scalars(
        select(Conversacion)
        .where(or_(*condiciones))
        .options(
            selectinload(Conversacion.cliente).selectinload(Cliente.usuario),
            selectinload(Conversacion.prestador).selectinload(PrestadorServicio.usuario),
            selectinload(Conversacion.postulacion)
            .selectinload(Postulacion.aviso)
            .selectinload(Aviso.categoria),
            selectinload(Conversacion.mensajes),
        )
        .order_by(Conversacion.fecha_actualizacion.desc())
    )

    items = []
    for conversacion in conversaciones.all():
        es_cliente = conversacion.id_cliente == id_cliente
        otro_usuario: Usuario = (
            conversacion.prestador.usuario
            if es_cliente
            else conversacion.cliente.usuario
        )
        postulacion = conversacion.postulacion
        aviso = postulacion.aviso if postulacion else None
        ultimo = max(
            conversacion.mensajes,
            key=lambda mensaje: (mensaje.fecha_envio, mensaje.id_mensaje),
            default=None,
        )
        items.append({
            "id_conversacion": conversacion.id_conversacion,
            "id_aviso": aviso.id_aviso if aviso else None,
            "oficio": (
                aviso.categoria.nombre
                if aviso and aviso.categoria
                else conversacion.prestador.oficio or "Servicio"
            ),
            "estado": (
                aviso.estado.value.lower()
                if aviso and hasattr(aviso.estado, "value")
                else str(aviso.estado).lower() if aviso else "en_proceso"
            ),
            "otro_participante": {
                "id_usuario": otro_usuario.id_usuario,
                "nombre": otro_usuario.nombre,
                "apellido": otro_usuario.apellido,
            },
            "ultimo_mensaje": (
                {
                    "contenido": ultimo.contenido,
                    "fecha_envio": ultimo.fecha_envio,
                }
                if ultimo
                else None
            ),
            "_ultima_actividad": (
                ultimo.fecha_envio
                if ultimo
                else conversacion.fecha_actualizacion
            ),
        })
    items.sort(key=lambda item: item["_ultima_actividad"], reverse=True)
    for item in items:
        item.pop("_ultima_actividad")
    return items


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
    despues_de_id: int = 0,
) -> list[Mensaje]:
    await _obtener_conversacion_participante(
        db,
        id_conversacion=id_conversacion,
        id_usuario=id_usuario,
    )

    mensajes = await db.scalars(
        select(Mensaje)
        .where(
            Mensaje.conversacion_id == id_conversacion,
            Mensaje.id_mensaje > despues_de_id,
        )
        .order_by(Mensaje.fecha_envio.asc(), Mensaje.id_mensaje.asc())
    )
    return list(mensajes.all())
