import unicodedata

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload

from app.async_database import get_async_db
from app.auth import get_current_user
from app.database import get_db
from app.models.Aviso import Aviso, EstadoAvisoEnum
from app.models.Categoria import Categoria
from app.models.PrestadorServicio import PrestadorServicio
from app.models.usuario import Usuario
from app.schemas.aviso import AvisoCreate
from app.schemas.postulacion import PostulacionCreate, PostulacionResponse
from app.services.postulaciones import crear_postulacion


router = APIRouter(prefix="/avisos", tags=["Avisos"])


def _normalizar_categoria(nombre: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", nombre.casefold())
    sin_acentos = "".join(
        caracter
        for caracter in descompuesto
        if not unicodedata.combining(caracter)
    )
    normalizado = " ".join(sin_acentos.strip().split())
    aliases = {
        "plomeria": "plomeria y gas",
        "gasista": "plomeria y gas",
        "electricista": "electricidad",
        "cerrajero": "cerrajeria",
    }
    return aliases.get(normalizado, normalizado)


@router.get("/zona")
def listar_avisos_por_zona(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    prestador = (
        db.query(PrestadorServicio)
        .filter(PrestadorServicio.id_usuario == usuario.id_usuario)
        .first()
    )
    if prestador is None:
        raise HTTPException(
            status_code=404,
            detail="No se encontró un perfil de prestador para este usuario",
        )

    if prestador.zona is None or not prestador.zona.strip():
        raise HTTPException(
            status_code=400,
            detail="Debe configurar su zona en el perfil para buscar avisos",
        )

    zona_prestador = prestador.zona.strip().lower()
    avisos = (
        db.query(Aviso)
        .options(joinedload(Aviso.categoria), joinedload(Aviso.cliente))
        .filter(
            func.lower(func.trim(Aviso.ubicacion)) == zona_prestador,
            Aviso.estado == EstadoAvisoEnum.ABIERTO,
        )
        .order_by(Aviso.fecha_publicacion.desc())
        .all()
    )
    return [
        {
            "id_aviso": aviso.id_aviso,
            "id_cliente": aviso.id_cliente,
            "titulo": aviso.titulo,
            "oficio": aviso.categoria.nombre,
            "descripcion": aviso.descripcion,
            "zona": aviso.ubicacion,
            "telefono": aviso.cliente.telefono,
            "estado": aviso.estado.value.lower(),
            "fecha_creacion": aviso.fecha_publicacion,
        }
        for aviso in avisos
    ]


@router.post("", status_code=201)
def crear_aviso(
    datos: AvisoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    categorias = db.query(Categoria).all()
    categoria_buscada = _normalizar_categoria(datos.oficio)
    categoria = next(
        (
            item
            for item in categorias
            if _normalizar_categoria(item.nombre) == categoria_buscada
        ),
        None,
    )
    if categoria is None:
        raise HTTPException(
            status_code=400,
            detail=f"La categoría {datos.oficio} no está disponible para publicar avisos",
        )

    usuario_db = db.get(Usuario, usuario.id_usuario)
    if usuario_db is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    if datos.telefono is not None:
        usuario_db.telefono = datos.telefono

    aviso = Aviso(
        id_cliente=usuario.id_usuario,
        id_categoria=categoria.id_categoria,
        titulo=categoria.nombre,
        descripcion=datos.descripcion,
        ubicacion=datos.zona,
        estado=EstadoAvisoEnum.ABIERTO,
    )
    db.add(aviso)
    db.commit()
    db.refresh(aviso)

    return {
        "mensaje": "Solicitud de trabajo creada correctamente",
        "id_aviso": aviso.id_aviso,
        "id_cliente": aviso.id_cliente,
        "titulo": aviso.titulo,
        "oficio": categoria.nombre,
        "descripcion": aviso.descripcion,
        "zona": aviso.ubicacion,
        "telefono": usuario_db.telefono,
        "estado": aviso.estado.value.lower(),
        "fecha_creacion": aviso.fecha_publicacion,
    }


@router.post(
    "/{id_aviso}/postulaciones",
    response_model=PostulacionResponse,
    status_code=201,
)
async def postularse_a_aviso(
    id_aviso: int,
    datos: PostulacionCreate,
    db: AsyncSession = Depends(get_async_db),
    usuario: Usuario = Depends(get_current_user),
):
    if (usuario.rol.nombre or "").strip().upper() != "PRESTADOR":
        raise HTTPException(
            status_code=403,
            detail="Se requiere una cuenta de prestador para postularse",
        )

    return await crear_postulacion(
        db,
        id_aviso=id_aviso,
        id_usuario=usuario.id_usuario,
        datos=datos,
    )