from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.PrestadorServicio import PrestadorServicio
from app.models.usuario import Usuario
from app.schemas.perfil import PerfilUpdate


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("/perfil")
def obtener_perfil(
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

    zona = prestador.zona.strip() if prestador.zona else ""
    return {
        "usuario": {
            "id_usuario": usuario.id_usuario,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "email": usuario.email,
            "foto_perfil": usuario.foto_perfil,
            "fecha_registro": usuario.fecha_registro,
        },
        "prestador": {
            "id_prestador": prestador.id_prestador,
            "matricula": prestador.matricula,
            "biografia": prestador.biografia,
            "telefono": prestador.telefono,
            "zona": zona,
            "oficio": prestador.oficio,
        },
        "categoria": prestador.oficio or "Oficio sin definir",
        "zonas": [{"nombre": zona}] if zona else [],
        "rating": {
            "promedio": float(prestador.prom_calificacion or 0),
            "total": 0,
        },
        "fotos": [],
    }


@router.put("/perfil")
def actualizar_perfil(
    datos: PerfilUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    campos = datos.dict(exclude_unset=True)
    if not campos:
        raise HTTPException(status_code=400, detail="Debe enviar al menos un dato para actualizar")

    telefono_actual = usuario.telefono
    if "telefono" in campos:
        usuario_db = db.get(Usuario, usuario.id_usuario)
        if usuario_db is None:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        usuario_db.telefono = datos.telefono
        telefono_actual = usuario_db.telefono

    es_prestador = (usuario.rol.nombre or "").strip().upper() == "PRESTADOR"
    prestador = None
    if es_prestador:
        prestador = (
            db.query(PrestadorServicio)
            .filter(PrestadorServicio.id_usuario == usuario.id_usuario)
            .first()
        )
        if prestador is None:
            prestador = PrestadorServicio(id_usuario=usuario.id_usuario)
            db.add(prestador)

        if "zona" in campos:
            prestador.zona = datos.zona
        if "telefono" in campos:
            prestador.telefono = datos.telefono
        if "oficio" in campos:
            prestador.oficio = datos.oficio
        if "biografia" in campos:
            prestador.biografia = datos.biografia
    else:
        campos_no_disponibles = {"zona", "oficio", "biografia"} & campos.keys()
        if campos_no_disponibles:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El perfil de cliente no guarda zona ni oficio; "
                    "la zona se indica al publicar cada solicitud"
                ),
            )
    db.commit()
    if prestador is not None:
        db.refresh(prestador)

    return {
        "mensaje": "Perfil actualizado correctamente",
        "id_usuario": usuario.id_usuario,
        "cliente": None if es_prestador else {
            "zona": None,
            "telefono": telefono_actual,
        },
        "prestador": None if prestador is None else {
            "zona": prestador.zona,
            "oficio": prestador.oficio,
            "telefono": prestador.telefono,
        },
    }