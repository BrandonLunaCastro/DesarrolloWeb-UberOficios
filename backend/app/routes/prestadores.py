import logging

from cloudinary.exceptions import Error as CloudinaryError
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import get_current_user_id
from app.database import get_db
from app.models.foto_portafolio import FotoPortafolio
from app.models.PrestadorServicio import PrestadorServicio
from app.services.portfolio_storage import (
    CloudinaryNotConfiguredError,
    delete_portfolio_image,
    upload_portfolio_image,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prestadores", tags=["Prestadores"])

MAX_FOTOS_POR_SUBIDA = 12
MAX_BYTES_POR_FOTO = 5 * 1024 * 1024
FIRMAS_IMAGEN = {
    "image/jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
    "image/png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/webp": lambda data: (
        len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    ),
}


def _validar_imagen(archivo: UploadFile, contenido: bytes) -> None:
    if not contenido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{archivo.filename or 'Archivo'}: la imagen está vacía.",
        )
    valida_firma = FIRMAS_IMAGEN.get(archivo.content_type or "")
    if valida_firma is None or not valida_firma(contenido):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{archivo.filename or 'Archivo'}: solo se permiten imágenes JPG, PNG o WebP válidas.",
        )
    if len(contenido) > MAX_BYTES_POR_FOTO:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"{archivo.filename or 'Archivo'}: supera el límite de 5 MB.",
        )


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


def _limpiar_subidas(public_ids: list[str]) -> None:
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
        contenido = archivo.file.read(MAX_BYTES_POR_FOTO + 1)
        _validar_imagen(archivo, contenido)
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
