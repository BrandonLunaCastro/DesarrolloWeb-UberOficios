from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.Aviso import Aviso
from app.models.PrestadorServicio import PrestadorServicio
from app.models.postulacion import Postulacion
from app.models.usuario import Usuario
from app.schemas.postulacion import PostulacionCreate, PostulacionListItem


COSTO_POSTULACION = 1


async def listar_postulaciones_por_prestador(
    db: AsyncSession,
    *,
    id_prestador: int,
) -> list[PostulacionListItem]:
    prestador = await db.get(PrestadorServicio, id_prestador)
    if prestador is None:
        raise HTTPException(status_code=404, detail="Prestador no encontrado")

    resultados = await db.scalars(
        select(Postulacion)
        .options(
            selectinload(Postulacion.aviso).selectinload(Aviso.cliente),
            selectinload(Postulacion.prestador).selectinload(PrestadorServicio.usuario),
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
                presupuesto=postulacion.presupuesto,
                comentario=postulacion.comentario,
                fecha_postulacion=postulacion.fecha_postulacion,
                estado=postulacion.estado,
                titulo_aviso=aviso.titulo if aviso else None,
                descripcion_aviso=aviso.descripcion if aviso else None,
                nombre_prestador=prestador.usuario.nombre if prestador.usuario else None,
                apellido_prestador=prestador.usuario.apellido if prestador.usuario else None,
                oficio_prestador=prestador.oficio,
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
            selectinload(Postulacion.aviso),
            selectinload(Postulacion.prestador).selectinload(PrestadorServicio.usuario),
        )
        .join(Aviso, Postulacion.id_aviso == Aviso.id_aviso)
        .where(Aviso.id_cliente == id_cliente)
        .order_by(Postulacion.fecha_postulacion.desc())
    )

    items: list[PostulacionListItem] = []
    for postulacion in resultados.all():
        aviso = postulacion.aviso
        prestador = postulacion.prestador
        items.append(
            PostulacionListItem(
                id_postulacion=postulacion.id_postulacion,
                id_aviso=postulacion.id_aviso,
                id_prestador=postulacion.id_prestador,
                id_cliente=id_cliente,
                presupuesto=postulacion.presupuesto,
                comentario=postulacion.comentario,
                fecha_postulacion=postulacion.fecha_postulacion,
                estado=postulacion.estado,
                titulo_aviso=aviso.titulo if aviso else None,
                descripcion_aviso=aviso.descripcion if aviso else None,
                nombre_prestador=prestador.usuario.nombre if prestador and prestador.usuario else None,
                apellido_prestador=prestador.usuario.apellido if prestador and prestador.usuario else None,
                oficio_prestador=prestador.oficio if prestador else None,
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