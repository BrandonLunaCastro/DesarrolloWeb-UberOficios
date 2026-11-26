import logging

from cloudinary.exceptions import Error as CloudinaryError
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.auth import get_current_user_id
from app.database import get_db
from app.models.calificacion import Calificacion
from app.models.foto_portafolio import FotoPortafolio
from app.models.PrestadorServicio import PrestadorServicio
from app.services.portfolio_storage import (
    CloudinaryNotConfiguredError,
    delete_portfolio_image,
    upload_portfolio_image,
)
from app.services.image_validation import (
    MAX_IMAGE_SIZE_BYTES,
    ImageValidationError,
    validar_imagen,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prestadores", tags=["Prestadores"])

MAX_FOTOS_POR_SUBIDA = 12

# Centraliza la comprobación de que el usuario tenga un perfil profesional.
def _obtener_prestador(db: Session, id_usuario: int) -> PrestadorServicio:
    prestador = (
        db.query(PrestadorServicio)
        .filter(PrestadorServicio.id_usuario == id_usuario)
        .first()
    )
    if prestador is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere una cuenta de prestador para administrar el portafolio.",
        )
    return prestador


@router.get("/{id_prestador}/perfil")
def obtener_perfil_publico_prestador(
    id_prestador: int,
    _id_usuario: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # Agrega datos públicos, promedio y muestras recientes de opiniones del prestador.
    prestador = (
        db.query(PrestadorServicio)
        .options(
            joinedload(PrestadorServicio.usuario),
            selectinload(PrestadorServicio.fotos_portafolio),
        )
        .filter(PrestadorServicio.id_prestador == id_prestador)
        .first()
    )
    if prestador is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el perfil del prestador.",
        )

    zona = prestador.zona.strip() if prestador.zona else ""
    promedio, total = (
        db.query(func.avg(Calificacion.puntuacion), func.count(Calificacion.id_calificacion))
        .filter(Calificacion.id_prestador == prestador.id_prestador)
        .one()
    )
    calificaciones = (
        db.query(Calificacion)
        .options(joinedload(Calificacion.cliente))
        .filter(Calificacion.id_prestador == prestador.id_prestador)
        .order_by(Calificacion.fecha.desc())
        .limit(10)
        .all()
    )

    return {
        "usuario": {
            "nombre": prestador.usuario.nombre,
            "apellido": prestador.usuario.apellido,
            "foto_perfil": prestador.usuario.foto_perfil,
            "fecha_registro": prestador.usuario.fecha_registro,
        },
        "prestador": {
            "id_prestador": prestador.id_prestador,
            "matricula": prestador.matricula,
            "biografia": prestador.biografia,
            "zona": zona,
            "oficio": prestador.oficio,
        },
        "categoria": prestador.oficio or "Oficio sin definir",
        "zonas": [{"nombre": zona}] if zona else [],
        "rating": {
            "promedio": float(promedio or 0),
            "total": total,
        },
        "calificaciones": [
            {
                "id_calificacion": calificacion.id_calificacion,
                "puntuacion": calificacion.puntuacion,
                "comentario": calificacion.comentario,
                "url_comprobante": calificacion.url_comprobante,
                "fecha": calificacion.fecha,
                "cliente": {
                    "nombre": calificacion.cliente.nombre,
                    "apellido": (
                        f"{calificacion.cliente.apellido[0]}."
                        if calificacion.cliente.apellido
                        else ""
                    ),
                },
            }
            for calificacion in calificaciones
        ],
        "fotos": [
            {
                "id_foto": foto.id_foto,
                "url_imagen": foto.url_imagen,
                "descripcion": foto.descripcion,
            }
            for foto in prestador.fotos_portafolio
        ],
    }


def _limpiar_subidas(public_ids: list[str]) -> None:
    # Compensa cargas externas si después falla el guardado de metadatos en la BD.
    for public_id in public_ids:
        try:
            delete_portfolio_image(public_id)
        except (CloudinaryError, CloudinaryNotConfiguredError):
            logger.exception(
                "No se pudo limpiar la imagen de Cloudinary %s",
                public_id,
            )


@router.post("/me/fotos", status_code=status.HTTP_201_CREATED)
def subir_fotos_portafolio(
    fotos: list[UploadFile] = File(...),
    id_usuario: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # Valida todos los archivos antes de subir cualquiera para evitar cargas parciales.
    if not fotos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe seleccionar al menos una foto.",
        )
    if len(fotos) > MAX_FOTOS_POR_SUBIDA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Se permite subir hasta {MAX_FOTOS_POR_SUBIDA} fotos por vez.",
        )

    prestador = _obtener_prestador(db, id_usuario)
    contenidos = []
    for archivo in fotos:
        contenido = archivo.file.read(MAX_IMAGE_SIZE_BYTES + 1)
        # Cloudinary y la base no comparten transacción; los public_id permiten revertir la carga.
        try:
            validar_imagen(
                contenido,
                archivo.content_type,
                archivo.filename or "Archivo",
            )
        except ImageValidationError as error:
            raise HTTPException(
                status_code=error.status_code,
                detail=error.detail,
            ) from error
        contenidos.append(contenido)

    registros = []
    public_ids = []
    try:
        for contenido in contenidos:
            resultado = upload_portfolio_image(
                contenido,
                folder=f"uberoficios/prestadores/{prestador.id_prestador}",
            )
            public_id = resultado.get("public_id")
            secure_url = resultado.get("secure_url")
            if not public_id or not secure_url:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Cloudinary no devolvió los datos de la imagen.",
                )
            public_ids.append(public_id)
            registros.append(
                FotoPortafolio(
                    id_prestador=prestador.id_prestador,
                    url_imagen=secure_url,
                    public_id=public_id,
                )
            )
    except CloudinaryNotConfiguredError as error:
        _limpiar_subidas(public_ids)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El almacenamiento de imágenes no está configurado.",
        ) from error
    except CloudinaryError as error:
        _limpiar_subidas(public_ids)
        logger.exception("Falló la carga de una foto de portafolio en Cloudinary")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudieron guardar las fotos en el almacenamiento.",
        ) from error
    except HTTPException:
        _limpiar_subidas(public_ids)
        raise

    try:
        db.add_all(registros)
        db.flush()
        respuesta = [
            {
                "id_foto": registro.id_foto,
                "url_imagen": registro.url_imagen,
                "descripcion": registro.descripcion,
            }
            for registro in registros
        ]
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        _limpiar_subidas(public_ids)
        logger.exception("No se pudieron guardar las fotos de portafolio en la base de datos")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudieron guardar las fotos en el perfil.",
        ) from error

    return respuesta


@router.delete("/me/fotos/{id_foto}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_foto_portafolio(
    id_foto: int,
    id_usuario: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # La consulta une la foto con su dueño antes de eliminar el registro y el archivo externo.
    foto = (
        db.query(FotoPortafolio)
        .join(PrestadorServicio)
        .filter(
            FotoPortafolio.id_foto == id_foto,
            PrestadorServicio.id_usuario == id_usuario,
        )
        .first()
    )
    if foto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la foto en tu portafolio.",
        )

    public_id = foto.public_id
    db.delete(foto)
    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("No se pudo eliminar la foto de portafolio de la base de datos")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo eliminar la foto del perfil.",
        ) from error

    try:
        delete_portfolio_image(public_id)
    except (CloudinaryError, CloudinaryNotConfiguredError):
        logger.exception("No se pudo eliminar la imagen de Cloudinary %s", public_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
