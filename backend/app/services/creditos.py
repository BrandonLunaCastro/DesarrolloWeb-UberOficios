import calendar
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.PrestadorServicio import PrestadorServicio


BONO_MENSUAL_CREDITOS = 5


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
        prestadores_actualizados += 1
        creditos_acreditados += credito

    return prestadores_actualizados, creditos_acreditados
