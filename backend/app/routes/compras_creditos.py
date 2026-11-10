import asyncio
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.async_database import get_async_db
from app.auth import get_current_user_id
from app.models.PrestadorServicio import PrestadorServicio
from app.models.creditos import (
    CompraCredito,
    EstadoCompraCreditoEnum,
    PaqueteCredito,
    TipoTransaccionEnum,
)
from app.schemas.compras_creditos import (
    CompraCreditoResponse,
    IniciarCompraRequest,
    PaqueteCreditoResponse,
)
from app.services.creditos import registrar_transaccion
from app.services.mercado_pago import (
    MercadoPagoError,
    configuracion_mercado_pago_disponible,
    crear_preferencia,
    firma_webhook_valida,
    importe_pago_valido,
    obtener_pago,
)


router = APIRouter(prefix="/creditos", tags=["Compras de créditos"])


async def _obtener_prestador(
    db: AsyncSession,
    id_usuario: int,
) -> PrestadorServicio:
    prestador = await db.scalar(
        select(PrestadorServicio).where(PrestadorServicio.id_usuario == id_usuario)
    )
    if prestador is None:
        raise HTTPException(
            status_code=403,
            detail="Se requiere una cuenta de prestador para comprar créditos",
        )
    return prestador


async def _iniciar_checkout(
    db: AsyncSession,
    compra: CompraCredito,
) -> CompraCredito:
    try:
        preference = await asyncio.to_thread(crear_preferencia, compra)
    except MercadoPagoError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"mensaje": str(error), "compra_id": compra.id},
        ) from error

    compra.preferencia_pago_id = preference["id"]
    compra.url_pago = preference["url"]
    await db.commit()
    await db.refresh(compra)
    return compra


@router.get("/paquetes", response_model=list[PaqueteCreditoResponse])
async def listar_paquetes_creditos(
    db: AsyncSession = Depends(get_async_db),
    id_usuario: int = Depends(get_current_user_id),
):
    del id_usuario
    paquetes = await db.scalars(
        select(PaqueteCredito)
        .where(PaqueteCredito.activo.is_(True))
        .order_by(PaqueteCredito.orden, PaqueteCredito.id)
    )
    return paquetes.all()


@router.post(
    "/compras",
    response_model=CompraCreditoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def iniciar_compra_creditos(
    datos: IniciarCompraRequest,
    db: AsyncSession = Depends(get_async_db),
    id_usuario: int = Depends(get_current_user_id),
):
    if not configuracion_mercado_pago_disponible():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La pasarela de pago no está configurada",
        )

    prestador = await _obtener_prestador(db, id_usuario)
    paquete = await db.scalar(
        select(PaqueteCredito).where(
            PaqueteCredito.id == datos.paquete_id,
            PaqueteCredito.activo.is_(True),
        )
    )
    if paquete is None:
        raise HTTPException(status_code=404, detail="El paquete no existe o no está disponible")

    compra = CompraCredito(
        prestador_id=prestador.id_prestador,
        paquete_id=paquete.id,
        cantidad_creditos=paquete.cantidad_creditos,
        precio_centavos=paquete.precio_centavos,
        moneda=paquete.moneda,
        estado=EstadoCompraCreditoEnum.PENDIENTE,
    )
    db.add(compra)
    await db.commit()
    await db.refresh(compra)
    return await _iniciar_checkout(db, compra)


@router.post(
    "/compras/{compra_id}/checkout",
    response_model=CompraCreditoResponse,
)
async def reintentar_checkout_compra(
    compra_id: int,
    db: AsyncSession = Depends(get_async_db),
    id_usuario: int = Depends(get_current_user_id),
):
    prestador = await _obtener_prestador(db, id_usuario)
    compra = await db.scalar(
        select(CompraCredito).where(
            CompraCredito.id == compra_id,
            CompraCredito.prestador_id == prestador.id_prestador,
        )
    )
    if compra is None:
        raise HTTPException(status_code=404, detail="No se encontró la compra")
    if compra.estado != EstadoCompraCreditoEnum.PENDIENTE:
        raise HTTPException(status_code=409, detail="La compra ya no está pendiente")
    if compra.url_pago:
        return compra
    if not configuracion_mercado_pago_disponible():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La pasarela de pago no está configurada",
        )
    return await _iniciar_checkout(db, compra)


@router.get("/compras/{compra_id}", response_model=CompraCreditoResponse)
async def consultar_compra_creditos(
    compra_id: int,
    db: AsyncSession = Depends(get_async_db),
    id_usuario: int = Depends(get_current_user_id),
):
    prestador = await _obtener_prestador(db, id_usuario)
    compra = await db.scalar(
        select(CompraCredito).where(
            CompraCredito.id == compra_id,
            CompraCredito.prestador_id == prestador.id_prestador,
        )
    )
    if compra is None:
        raise HTTPException(status_code=404, detail="No se encontró la compra")
    return compra


@router.post("/pagos/webhook")
async def confirmar_pago_creditos(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    if not os.getenv("MERCADOPAGO_WEBHOOK_SECRET"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La confirmación de pagos no está configurada",
        )

    try:
        body = await request.json()
    except ValueError:
        body = {}
    if not isinstance(body, dict):
        body = {}
    data = body.get("data")
    if not isinstance(data, dict):
        data = {}
    payment_id = (
        request.query_params.get("data.id")
        or data.get("id")
    )
    event_type = request.query_params.get("type") or body.get("type")
    if event_type not in (None, "payment"):
        return {"recibido": True}
    if not payment_id:
        raise HTTPException(status_code=400, detail="Falta el identificador del pago")
    payment_id = str(payment_id)
    if not firma_webhook_valida(
        payment_id=payment_id,
        request_id=request.headers.get("x-request-id"),
        signature=request.headers.get("x-signature"),
    ):
        raise HTTPException(status_code=401, detail="Firma de notificación inválida")

    try:
        pago = await asyncio.to_thread(obtener_pago, payment_id)
    except MercadoPagoError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    if str(pago.get("id")) != payment_id:
        raise HTTPException(status_code=400, detail="La pasarela devolvió otro pago")
    external_reference = pago.get("external_reference")
    if not external_reference or not str(external_reference).isdigit():
        raise HTTPException(status_code=404, detail="No se encontró la compra del pago")

    compra = await db.scalar(
        select(CompraCredito)
        .where(CompraCredito.id == int(external_reference))
        .with_for_update()
    )
    if compra is None:
        raise HTTPException(status_code=404, detail="No se encontró la compra del pago")
    if not importe_pago_valido(pago, compra):
        raise HTTPException(status_code=400, detail="El importe o moneda del pago no coincide")

    if compra.estado != EstadoCompraCreditoEnum.PENDIENTE:
        return {"recibido": True, "estado": compra.estado.value}

    estado_pago = pago.get("status")
    if estado_pago == "approved":
        nombre_paquete = await db.scalar(
            select(PaqueteCredito.nombre).where(
                PaqueteCredito.id == compra.paquete_id
            )
        )
        transaccion = await registrar_transaccion(
            db,
            id_prestador=compra.prestador_id,
            monto=compra.cantidad_creditos,
            tipo=TipoTransaccionEnum.RECARGA,
            referencia_id=compra.id,
            referencia_tipo="compra_credito",
            descripcion=(
                f"Compra de paquete {nombre_paquete} "
                f"({compra.cantidad_creditos} créditos)"
            ),
        )
        compra.estado = EstadoCompraCreditoEnum.APROBADA
        compra.referencia_pago = payment_id
        compra.transaccion_id = transaccion.id
        compra.fecha_acreditacion = datetime.now(timezone.utc)
    elif estado_pago == "rejected":
        compra.estado = EstadoCompraCreditoEnum.RECHAZADA
        compra.referencia_pago = payment_id
    elif estado_pago == "cancelled":
        compra.estado = EstadoCompraCreditoEnum.CANCELADA
        compra.referencia_pago = payment_id

    await db.commit()
    return {"recibido": True, "estado": compra.estado.value}
