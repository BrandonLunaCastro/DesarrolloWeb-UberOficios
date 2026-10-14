from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.Aviso import Aviso
from app.models.postulacion import Postulacion
from app.schemas.postulacion import PostulacionCreate


async def crear_postulacion(
    db: AsyncSession,
    *,
    id_aviso: int,
    id_prestador: int,
    datos: PostulacionCreate,
) -> Postulacion:
    aviso = await db.scalar(select(Aviso).where(Aviso.id_aviso == id_aviso))
    if aviso is None:
        raise HTTPException(status_code=404, detail="Aviso no encontrado")
    if aviso.estado != "ABIERTO":
        raise HTTPException(status_code=400, detail="El aviso no está abierto")

    existente = await db.scalar(
        select(Postulacion.id_postulacion).where(
            Postulacion.id_aviso == id_aviso,
            Postulacion.id_prestador == id_prestador,
        )
    )
    if existente is not None:
        raise HTTPException(status_code=400, detail="Ya te postulaste a este aviso")

    postulacion = Postulacion(
        id_aviso=id_aviso,
        id_prestador=id_prestador,
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
                Postulacion.id_prestador == id_prestador,
            )
        )
        if existente is not None:
            raise HTTPException(status_code=400, detail="Ya te postulaste a este aviso")
        raise

    await db.refresh(postulacion)
    return postulacion