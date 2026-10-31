from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.Aviso import Aviso
from app.models.Cliente import Cliente
from app.models.PrestadorServicio import PrestadorServicio
from app.models.conversacion import Conversacion
from app.models.postulacion import Postulacion
from app.models.usuario import Usuario
from app.schemas.postulacion import PostulacionCreate, PostulacionListItem


COSTO_POSTULACION = 1


async def listar_postulaciones_por_prestador(
    db: AsyncSession,
    *,
    id_prestador: int,
) -> list[PostulacionListItem]:
    prestador = await db.scalar(
        select(PrestadorServicio)
        .where(PrestadorServicio.id_prestador == id_prestador)
        .options(selectinload(PrestadorServicio.usuario))
    )
    if prestador is None:
        raise HTTPException(status_code=404, detail="Prestador no encontrado")

    resultados = await db.scalars(
        select(Postulacion)
        .options(
            selectinload(Postulacion.aviso).selectinload(Aviso.cliente),
            selectinload(Postulacion.prestador).selectinload(PrestadorServicio.usuario),
            selectinload(Postulacion.conversacion),
        )
        .where(Postulacion.id_prestador == id_prestador)
        .order_by(Postulacion.fecha_postulacion.desc())
    )

    items: list[PostulacionListItem] = []
    for postulacion in resultados.all():
        aviso = postulacion.aviso
        cliente = aviso.cliente if aviso else None
        items.append(
            PostulacionListItem(
                id_postulacion=postulacion.id_postulacion,
                id_aviso=postulacion.id_aviso,
                id_prestador=postulacion.id_prestador,
                id_cliente=cliente.id_usuario if cliente else None,
                id_conversacion=(
                    postulacion.conversacion.id_conversacion
                    if postulacion.conversacion
                    else None
                ),
                presupuesto=postulacion.presupuesto,
                comentario=postulacion.comentario,
                fecha_postulacion=postulacion.fecha_postulacion,
                estado=postulacion.estado,
                titulo_aviso=aviso.titulo if aviso else None,
                descripcion_aviso=aviso.descripcion if aviso else None,
                nombre_prestador=prestador.usuario.nombre if prestador.usuario else None,
                apellido_prestador=prestador.usuario.apellido if prestador.usuario else None,
                oficio_prestador=prestador.oficio,
                nombre_cliente=cliente.nombre if cliente else None,
                apellido_cliente=cliente.apellido if cliente else None,
                zona_aviso=aviso.ubicacion if aviso else None,
            )
        )
    return items


async def listar_postulaciones_por_cliente(
    db: AsyncSession,
    *,
    id_cliente: int,
) -> list[PostulacionListItem]:
    cliente = await db.get(Usuario, id_cliente)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    resultados = await db.scalars(
        select(Postulacion)
        .options(
            selectinload(Postulacion.aviso).selectinload(Aviso.cliente),
            selectinload(Postulacion.prestador).selectinload(PrestadorServicio.usuario),
            selectinload(Postulacion.conversacion),
        )
        .join(Aviso, Postulacion.id_aviso == Aviso.id_aviso)
        .where(Aviso.id_cliente == id_cliente)
        .order_by(Postulacion.fecha_postulacion.desc())
    )

    items: list[PostulacionListItem] = []
    for postulacion in resultados.all():
        aviso = postulacion.aviso
        cliente = aviso.cliente if aviso else None
        prestador = postulacion.prestador
        items.append(
            PostulacionListItem(
                id_postulacion=postulacion.id_postulacion,
                id_aviso=postulacion.id_aviso,
                id_prestador=postulacion.id_prestador,
                id_cliente=id_cliente,
                id_conversacion=(
                    postulacion.conversacion.id_conversacion
                    if postulacion.conversacion
                    else None
                ),
                presupuesto=postulacion.presupuesto,
                comentario=postulacion.comentario,
                fecha_postulacion=postulacion.fecha_postulacion,
                estado=postulacion.estado,
                titulo_aviso=aviso.titulo if aviso else None,
                descripcion_aviso=aviso.descripcion if aviso else None,
                nombre_prestador=prestador.usuario.nombre if prestador and prestador.usuario else None,
                apellido_prestador=prestador.usuario.apellido if prestador and prestador.usuario else None,
                oficio_prestador=prestador.oficio if prestador else None,
                nombre_cliente=cliente.nombre if cliente else None,
                apellido_cliente=cliente.apellido if cliente else None,
                zona_aviso=aviso.ubicacion if aviso else None,
            )
        )
    return items


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

    descuento = await db.execute(
        update(PrestadorServicio)
        .where(
            PrestadorServicio.id_prestador == prestador.id_prestador,
            PrestadorServicio.saldo_creditos >= COSTO_POSTULACION,
        )
        .values(
            saldo_creditos=PrestadorServicio.saldo_creditos - COSTO_POSTULACION,
        )
    )
    if descuento.rowcount != 1:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No tenés créditos suficientes para postularte",
        )

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


async def aceptar_postulacion(
    db: AsyncSession,
    *,
    id_postulacion: int,
    id_usuario: int,
) -> tuple[Postulacion, Conversacion]:
    postulacion = await db.scalar(
        select(Postulacion)
        .where(Postulacion.id_postulacion == id_postulacion)
    )
    if postulacion is None:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

    aviso = await db.scalar(
        select(Aviso)
        .where(Aviso.id_aviso == postulacion.id_aviso)
        .with_for_update()
    )
    if aviso is None:
        raise HTTPException(status_code=404, detail="Aviso no encontrado")
    if aviso.id_cliente != id_usuario:
        raise HTTPException(
            status_code=403,
            detail="No tenés permiso para aceptar presupuestos de este aviso",
        )

    postulacion = await db.scalar(
        select(Postulacion)
        .where(Postulacion.id_postulacion == id_postulacion)
        .with_for_update()
    )
    if postulacion is None:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

    conversacion = await db.scalar(
        select(Conversacion).where(
            Conversacion.id_postulacion == postulacion.id_postulacion
        )
    )
    if postulacion.estado == "ACEPTADO":
        if conversacion is None:
            cliente = await db.scalar(
                select(Cliente).where(Cliente.id_usuario == id_usuario)
            )
            if cliente is None:
                cliente = Cliente(id_usuario=id_usuario)
                db.add(cliente)
                await db.flush()
            conversacion = Conversacion(
                id_cliente=cliente.id_cliente,
                id_prestador=postulacion.id_prestador,
                id_postulacion=postulacion.id_postulacion,
            )
            db.add(conversacion)
            await db.commit()
            await db.refresh(conversacion)
        return postulacion, conversacion

    if aviso.estado != "ABIERTO":
        raise HTTPException(
            status_code=409,
            detail="Este aviso ya no acepta presupuestos",
        )
    if postulacion.estado != "PENDIENTE":
        raise HTTPException(
            status_code=409,
            detail="Este presupuesto ya no se puede aceptar",
        )

    cliente = await db.scalar(
        select(Cliente)
        .where(Cliente.id_usuario == id_usuario)
        .with_for_update()
    )
    if cliente is None:
        cliente = Cliente(id_usuario=id_usuario)
        db.add(cliente)
        await db.flush()

    postulacion.estado = "ACEPTADO"
    aviso.estado = "EN_PROCESO"
    await db.execute(
        update(Postulacion)
        .where(
            Postulacion.id_aviso == aviso.id_aviso,
            Postulacion.id_postulacion != postulacion.id_postulacion,
            Postulacion.estado == "PENDIENTE",
        )
        .values(estado="RECHAZADO")
    )
    conversacion = Conversacion(
        id_cliente=cliente.id_cliente,
        id_prestador=postulacion.id_prestador,
        id_postulacion=postulacion.id_postulacion,
    )
    db.add(conversacion)
    await db.commit()
    await db.refresh(postulacion)
    await db.refresh(conversacion)
    return postulacion, conversacion