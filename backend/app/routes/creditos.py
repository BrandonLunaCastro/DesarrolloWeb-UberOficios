from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.async_database import get_async_db
from app.auth import get_current_user
from app.models.PrestadorServicio import PrestadorServicio
from app.models.creditos import BilleteraCredito, TransaccionCredito
from app.models.usuario import Usuario
from app.schemas.creditos import TransaccionCreditoResponse


router = APIRouter(prefix="/creditos", tags=["Créditos"])


@router.get("/movimientos", response_model=list[TransaccionCreditoResponse])
async def listar_movimientos_creditos(
    limite: int = Query(default=100, ge=1, le=500),
    desplazamiento: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_async_db),
    usuario: Usuario = Depends(get_current_user),
):
    id_prestador = await db.scalar(
        select(PrestadorServicio.id_prestador).where(
            PrestadorServicio.id_usuario == usuario.id_usuario
        )
    )
    if id_prestador is None:
        raise HTTPException(
            status_code=404,
            detail="No se encontró un perfil de prestador para este usuario",
        )

    billetera_id = await db.scalar(
        select(BilleteraCredito.id).where(
            BilleteraCredito.prestador_id == id_prestador
        )
    )
    if billetera_id is None:
        raise HTTPException(status_code=404, detail="No se encontró la billetera de créditos")

    movimientos = await db.scalars(
        select(TransaccionCredito)
        .where(TransaccionCredito.billetera_id == billetera_id)
        .order_by(
            TransaccionCredito.fecha_registro.desc(),
            TransaccionCredito.id.desc(),
        )
        .limit(limite)
        .offset(desplazamiento)
    )
    return movimientos.all()
