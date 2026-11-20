from datetime import datetime, timedelta, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.Aviso import Aviso, EstadoAvisoEnum


DURACION_AVISO = timedelta(hours=72)


def aviso_vencido(
    fecha_publicacion: datetime,
    ahora: datetime | None = None,
) -> bool:
    if fecha_publicacion.tzinfo is None:
        fecha_publicacion = fecha_publicacion.replace(tzinfo=timezone.utc)
    momento_actual = ahora or datetime.now(timezone.utc)
    if momento_actual.tzinfo is None:
        momento_actual = momento_actual.replace(tzinfo=timezone.utc)
    return fecha_publicacion + DURACION_AVISO <= momento_actual


def expirar_avisos_vencidos(db: Session) -> int:
    limite = datetime.now(timezone.utc) - DURACION_AVISO
    cantidad = (
        db.query(Aviso)
        .filter(
            Aviso.estado == EstadoAvisoEnum.ABIERTO,
            Aviso.fecha_publicacion <= limite,
        )
        .update(
            {Aviso.estado: EstadoAvisoEnum.EXPIRADO},
            synchronize_session=False,
        )
    )
    if cantidad:
        db.commit()
    return cantidad


async def expirar_avisos_vencidos_async(db: AsyncSession) -> int:
    limite = datetime.now(timezone.utc) - DURACION_AVISO
    resultado = await db.execute(
        update(Aviso)
        .where(
            Aviso.estado == EstadoAvisoEnum.ABIERTO,
            Aviso.fecha_publicacion <= limite,
        )
        .values(estado=EstadoAvisoEnum.EXPIRADO)
    )
    cantidad = resultado.rowcount or 0
    if cantidad:
        await db.commit()
    return cantidad
