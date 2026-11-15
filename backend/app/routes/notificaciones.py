from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.async_database import get_async_db
from app.auth import get_current_user_id
from app.models.notificacion import Notificacion


router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


@router.get("")
async def listar_notificaciones(
    db: AsyncSession = Depends(get_async_db),
    id_usuario: int = Depends(get_current_user_id),
):
    notificaciones = await db.scalars(
        select(Notificacion)
        .where(Notificacion.id_usuario == id_usuario)
        .order_by(Notificacion.fecha_creacion.desc(), Notificacion.id_notificacion.desc())
    )
    return notificaciones.all()


@router.patch("/leidas")
async def marcar_todas_leidas(
    db: AsyncSession = Depends(get_async_db),
    id_usuario: int = Depends(get_current_user_id),
):
    resultado = await db.execute(
        update(Notificacion)
        .where(
            Notificacion.id_usuario == id_usuario,
            Notificacion.leida.is_(False),
        )
        .values(leida=True)
    )
    await db.commit()
    return {"actualizadas": resultado.rowcount or 0}


@router.patch("/{id_notificacion}/leida")
async def marcar_notificacion_leida(
    id_notificacion: int,
    db: AsyncSession = Depends(get_async_db),
    id_usuario: int = Depends(get_current_user_id),
):
    notificacion = await db.scalar(
        select(Notificacion).where(
            Notificacion.id_notificacion == id_notificacion,
            Notificacion.id_usuario == id_usuario,
        )
    )
    if notificacion is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    notificacion.leida = True
    await db.commit()
    return {"id_notificacion": notificacion.id_notificacion, "leida": True}