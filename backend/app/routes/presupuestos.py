from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.async_database import get_async_db
from app.auth import get_current_user
from app.models.Aviso import Aviso
from app.models.PrestadorServicio import PrestadorServicio
from app.models.postulacion import Postulacion
from app.models.usuario import Usuario
from app.schemas.postulacion import PostulacionListItem
from app.services.postulaciones import (
    listar_postulaciones_por_cliente,
    listar_postulaciones_por_prestador,
)

router = APIRouter(tags=["Presupuestos"])


@router.get(
    "/prestadores/{id_prestador}/presupuestos",
    response_model=list[PostulacionListItem],
)
async def obtener_presupuestos_del_prestador(
    id_prestador: int,
    db: AsyncSession = Depends(get_async_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    if (usuario_actual.rol.nombre or "").strip().upper() != "PRESTADOR":
        raise HTTPException(
            status_code=403,
            detail="Se requiere una cuenta de prestador para consultar presupuestos enviados",
        )

    prestador = await db.scalar(
        select(PrestadorServicio)
        .where(PrestadorServicio.id_usuario == usuario_actual.id_usuario)
        .options(selectinload(PrestadorServicio.usuario))
    )
    if prestador is None:
        raise HTTPException(
            status_code=404,
            detail="No se encontró un perfil de prestador para este usuario",
        )
    if prestador.id_prestador != id_prestador:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para consultar presupuestos de otro prestador",
        )

    return await listar_postulaciones_por_prestador(db, id_prestador=id_prestador)


@router.get(
    "/clientes/{id_cliente}/presupuestos",
    response_model=list[PostulacionListItem],
)
async def obtener_presupuestos_del_cliente(
    id_cliente: int,
    db: AsyncSession = Depends(get_async_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    if (usuario_actual.rol.nombre or "").strip().upper() != "CLIENTE":
        raise HTTPException(
            status_code=403,
            detail="Se requiere una cuenta de cliente para consultar presupuestos recibidos",
        )
    if usuario_actual.id_usuario != id_cliente:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para consultar presupuestos de otro cliente",
        )

    usuario = await db.get(Usuario, id_cliente)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return await listar_postulaciones_por_cliente(db, id_cliente=id_cliente)
