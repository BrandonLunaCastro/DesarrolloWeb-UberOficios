from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.async_database import get_async_db
from app.auth import get_current_user_async
from app.models.Aviso import Aviso, EstadoAvisoEnum
from app.models.PrestadorServicio import PrestadorServicio
from app.models.calificacion import Calificacion
from app.models.postulacion import Postulacion
from app.models.usuario import Usuario
from app.schemas.calificacion import CalificacionCreate, CalificacionResponse


router = APIRouter(prefix="/calificaciones", tags=["Calificaciones"])


@router.post("", response_model=CalificacionResponse, status_code=201)
async def crear_calificacion(
    datos: CalificacionCreate,
    db: AsyncSession = Depends(get_async_db),
    usuario: Usuario = Depends(get_current_user_async),
):
    if (usuario.rol.nombre or "").strip().upper() != "CLIENTE":
        raise HTTPException(status_code=403, detail="Solo un cliente puede calificar un trabajo")

    postulacion_inicial = await db.scalar(
        select(Postulacion).where(
            Postulacion.id_postulacion == datos.id_postulacion
        )
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
        raise HTTPException(status_code=403, detail="No tienes permiso para calificar este trabajo")
    if aviso.estado != EstadoAvisoEnum.FINALIZADO:
        raise HTTPException(status_code=409, detail="Primero debes finalizar el trabajo")

    postulacion = await db.scalar(
        select(Postulacion)
        .where(
            Postulacion.id_postulacion == datos.id_postulacion,
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
        raise HTTPException(status_code=409, detail="El prestador seleccionado ya no está disponible")

    existente = await db.scalar(
        select(Calificacion.id_calificacion).where(
            Calificacion.id_postulacion == postulacion.id_postulacion
        )
    )
    if existente is not None:
        raise HTTPException(status_code=409, detail="Este trabajo ya fue calificado")

    calificacion = Calificacion(
        id_postulacion=postulacion.id_postulacion,
        id_cliente=usuario.id_usuario,
        id_prestador=postulacion.id_prestador,
        puntuacion=datos.puntuacion,
        comentario=datos.comentario.strip() or None if datos.comentario else None,
    )
    db.add(calificacion)
    try:
        await db.flush()
        promedio = await db.scalar(
            select(func.avg(Calificacion.puntuacion)).where(
                Calificacion.id_prestador == postulacion.id_prestador
            )
        )
        prestador.prom_calificacion = promedio
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Este trabajo ya fue calificado") from error

    await db.refresh(calificacion)
    return calificacion