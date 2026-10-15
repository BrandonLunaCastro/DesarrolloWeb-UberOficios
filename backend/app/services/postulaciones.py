from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.Aviso import Aviso
from app.models.PrestadorServicio import PrestadorServicio
from app.models.postulacion import Postulacion
from app.schemas.postulacion import PostulacionCreate


COSTO_POSTULACION = 1


async def crear_postulacion(
    db: AsyncSession,
    *,
    id_aviso: int,
    id_usuario: int,
    datos: PostulacionCreate,
) -> Postulacion:
    aviso = await db.scalar(
        select(Aviso)
        .where(Aviso.id_aviso == id_aviso)
        .with_for_update()
    )
    if aviso is None:
        raise HTTPException(status_code=404, detail="Aviso no encontrado")
    if (aviso.estado or "").strip().upper() != "ABIERTO":
        raise HTTPException(status_code=400, detail="El aviso no está abierto")

    prestador = await db.scalar(
        select(PrestadorServicio)
        .where(PrestadorServicio.id_usuario == id_usuario)
        .with_for_update()
    )
    if prestador is None or not prestador.activo:
        raise HTTPException(
            status_code=403,
            detail="Se requiere un perfil de prestador activo para postularse",
        )

    existente = await db.scalar(
        select(Postulacion.id_postulacion).where(
            Postulacion.id_aviso == id_aviso,
            Postulacion.id_prestador == prestador.id_prestador,
        )
    )
    if existente is not None:
        raise HTTPException(status_code=400, detail="Ya te postulaste a este aviso")
    if prestador.saldo_creditos < COSTO_POSTULACION:
        raise HTTPException(
            status_code=400,
            detail="No tenés créditos suficientes para postularte",
        )

    prestador.saldo_creditos -= COSTO_POSTULACION
    postulacion = Postulacion(
        id_aviso=id_aviso,
        id_prestador=prestador.id_prestador,
        presupuesto=datos.presupuesto,
        comentario=datos.comentario,
    )
    db.add(postulacion)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        existente = await db.scalar(
            select(Postulacion.id_postulacion).where(
                Postulacion.id_aviso == id_aviso,
                Postulacion.id_prestador == prestador.id_prestador,
            )
        )
        if existente is not None:
            raise HTTPException(status_code=400, detail="Ya te postulaste a este aviso")
        raise

    await db.refresh(postulacion)
    return postulacion