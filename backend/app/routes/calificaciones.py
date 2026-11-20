import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool

from app.async_database import get_async_db
from app.auth import get_current_user_async
from app.models.Aviso import Aviso, EstadoAvisoEnum
from app.models.PrestadorServicio import PrestadorServicio
from app.models.calificacion import Calificacion
from app.models.notificacion import Notificacion
from app.models.postulacion import Postulacion
from app.models.usuario import Usuario
from app.schemas.calificacion import CalificacionResponse
from app.services.image_validation import (
    MAX_IMAGE_SIZE_BYTES,
    ImageValidationError,
    validar_imagen,
)
from app.services.notificaciones_realtime import notification_connections
from app.services.portfolio_storage import (
    CloudinaryError as StorageCloudinaryError,
    CloudinaryNotConfiguredError,
    delete_portfolio_image,
    upload_portfolio_image,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calificaciones", tags=["Calificaciones"])


@router.get("/pendientes")
async def listar_calificaciones_pendientes(
    db: AsyncSession = Depends(get_async_db),
    usuario: Usuario = Depends(get_current_user_async),
):
    if (usuario.rol.nombre or "").strip().upper() != "CLIENTE":
        raise HTTPException(
            status_code=403,
            detail="Solo un cliente puede consultar calificaciones pendientes",
        )

    postulaciones = await db.scalars(
        select(Postulacion)
        .join(Aviso, Aviso.id_aviso == Postulacion.id_aviso)
        .outerjoin(
            Calificacion,
            Calificacion.id_postulacion == Postulacion.id_postulacion,
        )
        .options(
            selectinload(Postulacion.aviso),
            selectinload(Postulacion.prestador).selectinload(PrestadorServicio.usuario),
        )
        .where(
            Aviso.id_cliente == usuario.id_usuario,
            Aviso.estado == EstadoAvisoEnum.FINALIZADO,
            Postulacion.estado == "ACEPTADO",
            Calificacion.id_calificacion.is_(None),
        )
        .order_by(Aviso.fecha_publicacion.desc())
    )
    return [
        {
            "id_postulacion": postulacion.id_postulacion,
            "id_aviso": postulacion.id_aviso,
            "titulo": postulacion.aviso.titulo,
            "nombre_prestador": (
                " ".join(
                    parte
                    for parte in (
                        postulacion.prestador.usuario.nombre,
                        postulacion.prestador.usuario.apellido,
                    )
                    if parte
                )
                if postulacion.prestador and postulacion.prestador.usuario
                else "Prestador"
            ),
        }
        for postulacion in postulaciones.all()
    ]


@router.post("", response_model=CalificacionResponse, status_code=201)
async def crear_calificacion(
    id_postulacion: int = Form(gt=0),
    puntuacion: int = Form(ge=1, le=5),
    comentario: str | None = Form(default=None, max_length=2000),
    foto_comprobante: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_async_db),
    usuario: Usuario = Depends(get_current_user_async),
):
    if (usuario.rol.nombre or "").strip().upper() != "CLIENTE":
        raise HTTPException(
            status_code=403,
            detail="Solo un cliente puede calificar un trabajo",
        )

    postulacion_inicial = await db.scalar(
        select(Postulacion).where(Postulacion.id_postulacion == id_postulacion)
    )
    if postulacion_inicial is None:
        raise HTTPException(status_code=404, detail="Trabajo aceptado no encontrado")

    aviso = await db.scalar(
        select(Aviso)
        .where(Aviso.id_aviso == postulacion_inicial.id_aviso)
        .with_for_update()
    )
    if aviso is None:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    if aviso.id_cliente != usuario.id_usuario:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para calificar este trabajo",
        )
    if aviso.estado != EstadoAvisoEnum.FINALIZADO:
        raise HTTPException(status_code=409, detail="Primero debes finalizar el trabajo")

    postulacion = await db.scalar(
        select(Postulacion)
        .where(
            Postulacion.id_postulacion == id_postulacion,
            Postulacion.id_aviso == aviso.id_aviso,
            Postulacion.estado == "ACEPTADO",
        )
        .with_for_update()
    )
    if postulacion is None:
        raise HTTPException(
            status_code=409,
            detail="Solo se puede calificar al prestador seleccionado para este trabajo",
        )

    prestador = await db.get(PrestadorServicio, postulacion.id_prestador)
    if prestador is None:
        raise HTTPException(
            status_code=409,
            detail="El prestador seleccionado ya no está disponible",
        )

    calificacion = Calificacion(
        id_postulacion=postulacion.id_postulacion,
        id_cliente=usuario.id_usuario,
        id_prestador=postulacion.id_prestador,
        puntuacion=puntuacion,
        comentario=comentario.strip() or None if comentario else None,
    )
    db.add(calificacion)
    try:
        await db.flush()
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Este trabajo ya fue calificado") from error

    if foto_comprobante is not None:
        contenido = await foto_comprobante.read(MAX_IMAGE_SIZE_BYTES + 1)
        try:
            validar_imagen(
                contenido,
                foto_comprobante.content_type,
                foto_comprobante.filename or "Comprobante",
            )
        except ImageValidationError as error:
            await db.rollback()
            raise HTTPException(
                status_code=error.status_code,
                detail=error.detail,
            ) from error

        try:
            imagen = await run_in_threadpool(
                upload_portfolio_image,
                contenido,
                "uberofficios/comprobantes",
            )
        except CloudinaryNotConfiguredError as error:
            await db.rollback()
            raise HTTPException(
                status_code=503,
                detail="El almacenamiento de comprobantes no está configurado.",
            ) from error
        except StorageCloudinaryError as error:
            await db.rollback()
            raise HTTPException(
                status_code=502,
                detail="No se pudo cargar la foto comprobante.",
            ) from error
        calificacion.url_comprobante = imagen["secure_url"]
        calificacion.public_id_comprobante = imagen["public_id"]

    try:
        promedio = await db.scalar(
            select(func.avg(Calificacion.puntuacion)).where(
                Calificacion.id_prestador == postulacion.id_prestador
            )
        )
        prestador.prom_calificacion = promedio
        await db.execute(
            update(Notificacion)
            .where(
                Notificacion.id_usuario == usuario.id_usuario,
                Notificacion.id_postulacion == postulacion.id_postulacion,
                Notificacion.tipo == "calificacion_pendiente",
            )
            .values(leida=True)
        )
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        if calificacion.public_id_comprobante:
            try:
                await run_in_threadpool(
                    delete_portfolio_image,
                    calificacion.public_id_comprobante,
                )
            except (StorageCloudinaryError, CloudinaryNotConfiguredError):
                logger.exception(
                    "No se pudo eliminar de Cloudinary el comprobante tras fallar la calificación."
                )
        raise

    await db.refresh(calificacion)
    await notification_connections.broadcast(
        [usuario.id_usuario],
        {
            "type": "calificacion_completada",
            "id_postulacion": postulacion.id_postulacion,
        },
    )
    return calificacion
