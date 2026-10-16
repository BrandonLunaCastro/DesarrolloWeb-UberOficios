import calendar
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.PrestadorServicio import PrestadorServicio
from app.models.creditos import (
    BilleteraCredito,
    TipoTransaccionEnum,
    TransaccionCredito,
)


BONO_MENSUAL_CREDITOS = 5
COSTO_POSTULACION_CREDITOS = 1


def _normalizar_utc(fecha: datetime) -> datetime:
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


def _aniversario_mensual(inicio: datetime, meses: int) -> datetime:
    indice_mes = inicio.month - 1 + meses
    anio = inicio.year + indice_mes // 12
    mes = indice_mes % 12 + 1
    dia = min(inicio.day, calendar.monthrange(anio, mes)[1])
    return inicio.replace(year=anio, month=mes, day=dia)


def _meses_cumplidos(inicio: datetime, ahora: datetime) -> int:
    meses = (ahora.year - inicio.year) * 12 + ahora.month - inicio.month
    if meses <= 0:
        return 0
    if _aniversario_mensual(inicio, meses) > ahora:
        meses -= 1
    return max(meses, 0)


def acreditar_bonos_mensuales(
    db: Session,
    ahora: datetime | None = None,
) -> tuple[int, int]:
    """Acredita los bonos vencidos; el llamador debe confirmar la transacción."""
    fecha_actual = _normalizar_utc(ahora or datetime.now(timezone.utc))
    prestadores_actualizados = 0
    creditos_acreditados = 0

    prestadores = (
        db.query(PrestadorServicio)
        .filter(PrestadorServicio.inicio_ciclo_creditos <= fecha_actual)
        .order_by(PrestadorServicio.id_prestador)
        .with_for_update(skip_locked=True)
        .all()
    )

    for prestador in prestadores:
        inicio = _normalizar_utc(prestador.inicio_ciclo_creditos)
        meses_vencidos = _meses_cumplidos(inicio, fecha_actual)
        meses_pendientes = meses_vencidos - prestador.meses_creditos_otorgados
        if meses_pendientes <= 0:
            continue

        credito = meses_pendientes * BONO_MENSUAL_CREDITOS
        prestador.saldo_creditos += credito
        prestador.meses_creditos_otorgados = meses_vencidos
        billetera = (
            db.query(BilleteraCredito)
            .filter(BilleteraCredito.prestador_id == prestador.id_prestador)
            .with_for_update()
            .first()
        )
        if billetera is None:
            billetera = BilleteraCredito(
                prestador_id=prestador.id_prestador,
                saldo_actual=prestador.saldo_creditos - credito,
            )
            db.add(billetera)
            db.flush()

        billetera.saldo_actual += credito
        billetera.fecha_actualizacion = fecha_actual
        db.add(
            TransaccionCredito(
                billetera_id=billetera.id,
                monto=credito,
                tipo=TipoTransaccionEnum.BONIFICACION,
                referencia_tipo="bonificacion_mensual",
                descripcion=f"Bonificación mensual de {credito} créditos",
                fecha_registro=fecha_actual,
            )
        )
        prestadores_actualizados += 1
        creditos_acreditados += credito

    return prestadores_actualizados, creditos_acreditados


async def registrar_transaccion(
    db: AsyncSession,
    *,
    id_prestador: int,
    monto: int,
    tipo: TipoTransaccionEnum,
    referencia_id: int | None = None,
    referencia_tipo: str | None = None,
    descripcion: str | None = None,
) -> TransaccionCredito:
    """Actualiza ambos saldos e inserta el movimiento en la transacción vigente."""
    if monto == 0:
        raise ValueError("El monto de una transacción de créditos no puede ser cero")
    if tipo == TipoTransaccionEnum.CONSUMO_POSTULACION and monto > 0:
        raise ValueError("El consumo de créditos debe registrarse con un monto negativo")
    if tipo != TipoTransaccionEnum.CONSUMO_POSTULACION and monto < 0:
        raise ValueError("Las acreditaciones de créditos deben registrarse con un monto positivo")

    prestador = await db.scalar(
        select(PrestadorServicio)
        .where(PrestadorServicio.id_prestador == id_prestador)
        .with_for_update()
    )
    if prestador is None:
        raise HTTPException(status_code=404, detail="Prestador no encontrado")

    billetera = await db.scalar(
        select(BilleteraCredito)
        .where(BilleteraCredito.prestador_id == id_prestador)
        .with_for_update()
    )
    if billetera is None:
        raise HTTPException(status_code=404, detail="No se encontró la billetera de créditos")

    saldo_actualizado = billetera.saldo_actual + monto
    if saldo_actualizado < 0:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Saldo de créditos insuficiente para realizar la operación",
        )

    fecha_actual = datetime.now(timezone.utc)
    billetera.saldo_actual = saldo_actualizado
    billetera.fecha_actualizacion = fecha_actual
    prestador.saldo_creditos = saldo_actualizado
    transaccion = TransaccionCredito(
        billetera_id=billetera.id,
        monto=monto,
        tipo=tipo,
        referencia_id=referencia_id,
        referencia_tipo=referencia_tipo,
        descripcion=descripcion,
        fecha_registro=fecha_actual,
    )
    db.add(transaccion)
    await db.flush()
    return transaccion
