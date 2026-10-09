from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.Cliente import Cliente
from app.models.PrestadorServicio import PrestadorServicio
from app.models.usuario import Usuario
from app.schemas.perfil import PerfilUpdate


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.put("/perfil")
def actualizar_perfil(
    datos: PerfilUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    campos = datos.dict(exclude_unset=True)
    if not campos:
        raise HTTPException(status_code=400, detail="Debe enviar al menos un dato para actualizar")

    cliente = db.query(Cliente).filter(Cliente.id_usuario == usuario.id_usuario).first()
    prestador = db.query(PrestadorServicio).filter(
        PrestadorServicio.id_usuario == usuario.id_usuario
    ).first()

    if cliente is None and prestador is None:
        if datos.oficio is not None:
            prestador = PrestadorServicio(id_usuario=usuario.id_usuario)
            db.add(prestador)
        else:
            cliente = Cliente(id_usuario=usuario.id_usuario)
            db.add(cliente)

    if cliente is not None:
        if "zona" in campos:
            cliente.zona = datos.zona
        if "telefono" in campos:
            cliente.telefono = datos.telefono

    if datos.oficio is not None and prestador is None:
        prestador = PrestadorServicio(id_usuario=usuario.id_usuario)
        db.add(prestador)

    if prestador is not None:
        if "zona" in campos:
            prestador.zona = datos.zona
        if "telefono" in campos:
            prestador.telefono = datos.telefono
        if "oficio" in campos:
            prestador.oficio = datos.oficio

    db.commit()
    if cliente is not None:
        db.refresh(cliente)
    if prestador is not None:
        db.refresh(prestador)

    return {
        "mensaje": "Perfil actualizado correctamente",
        "id_usuario": usuario.id_usuario,
        "cliente": None if cliente is None else {
            "zona": cliente.zona,
            "telefono": cliente.telefono,
        },
        "prestador": None if prestador is None else {
            "zona": prestador.zona,
            "oficio": prestador.oficio,
            "telefono": prestador.telefono,
        },
    }