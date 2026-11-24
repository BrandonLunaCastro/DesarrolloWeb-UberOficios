import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
    SimularPagoRequest,
)
from app.services.creditos import registrar_transaccion


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
    return compra


@router.get("/compras", response_model=list[CompraCreditoResponse])
async def listar_compras_creditos(
    limite: int = Query(default=100, ge=1, le=500),
    desplazamiento: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_async_db),
    id_usuario: int = Depends(get_current_user_id),
):
    prestador = await _obtener_prestador(db, id_usuario)
    resultado = await db.execute(
        select(CompraCredito, PaqueteCredito.nombre.label("paquete_nombre"))
        .join(PaqueteCredito, PaqueteCredito.id == CompraCredito.paquete_id)
        .where(CompraCredito.prestador_id == prestador.id_prestador)
        .order_by(CompraCredito.fecha_creacion.desc(), CompraCredito.id.desc())
        .limit(limite)
        .offset(desplazamiento)
    )
    return [
        {
            "id": compra.id,
            "paquete_id": compra.paquete_id,
            "paquete_nombre": paquete_nombre,
            "cantidad_creditos": compra.cantidad_creditos,
            "precio_centavos": compra.precio_centavos,
            "moneda": compra.moneda,
            "estado": compra.estado,
            "fecha_creacion": compra.fecha_creacion,
            "fecha_acreditacion": compra.fecha_acreditacion,
        }
        for compra, paquete_nombre in resultado.all()
    ]


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


@router.post(
    "/compras/{compra_id}/simular-pago",
    response_model=CompraCreditoResponse,
)
async def simular_pago_creditos(
    compra_id: int,
    datos: SimularPagoRequest,
    db: AsyncSession = Depends(get_async_db),
    id_usuario: int = Depends(get_current_user_id),
):
    if os.getenv("PAYMENT_MODE") != "mock":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El simulador de pagos no está habilitado",
        )

    prestador = await _obtener_prestador(db, id_usuario)
    compra = await db.scalar(
        select(CompraCredito)
        .where(
            CompraCredito.id == compra_id,
            CompraCredito.prestador_id == prestador.id_prestador,
        )
        .with_for_update()
    )
    if compra is None:
        raise HTTPException(status_code=404, detail="No se encontró la compra")
    if compra.estado != EstadoCompraCreditoEnum.PENDIENTE:
        raise HTTPException(status_code=409, detail="La compra ya fue resuelta")

    if datos.resultado == EstadoCompraCreditoEnum.APROBADA:
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
        compra.transaccion_id = transaccion.id
        compra.fecha_acreditacion = datetime.now(timezone.utc)
    elif datos.resultado == EstadoCompraCreditoEnum.RECHAZADA:
        compra.estado = EstadoCompraCreditoEnum.RECHAZADA
    else:
        compra.estado = EstadoCompraCreditoEnum.CANCELADA

    await db.commit()
    await db.refresh(compra)
    return compra
