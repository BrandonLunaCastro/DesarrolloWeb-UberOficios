from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.Aviso import Aviso
from app.models.Cliente import Cliente
from app.models.PrestadorServicio import PrestadorServicio
from app.models.usuario import Usuario
from app.schemas.aviso import AvisoCreate


router = APIRouter(prefix="/avisos", tags=["Avisos"])


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
        .filter(func.lower(func.trim(Aviso.zona)) == zona_prestador)
        .order_by(Aviso.fecha_creacion.desc())
        .all()
    )
    return [
        {
            "id_aviso": aviso.id_aviso,
            "id_cliente": aviso.id_cliente,
            "oficio": aviso.oficio,
            "descripcion": aviso.descripcion,
            "zona": aviso.zona,
            "telefono": aviso.telefono,
            "estado": aviso.estado,
            "fecha_creacion": aviso.fecha_creacion,
        }
        for aviso in avisos
    ]


@router.post("", status_code=201)
def crear_aviso(
    datos: AvisoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    cliente = db.query(Cliente).filter(Cliente.id_usuario == usuario.id_usuario).first()
    if cliente is None:
        cliente = Cliente(id_usuario=usuario.id_usuario)
        db.add(cliente)
        db.flush()

    cliente.zona = datos.zona
    if datos.telefono is not None:
        cliente.telefono = datos.telefono

    aviso = Aviso(
        id_cliente=cliente.id_cliente,
        oficio=datos.oficio,
        descripcion=datos.descripcion,
        zona=datos.zona,
        telefono=datos.telefono,
    )
    db.add(aviso)
    db.commit()
    db.refresh(aviso)

    return {
        "mensaje": "Solicitud de trabajo creada correctamente",
        "id_aviso": aviso.id_aviso,
        "id_cliente": aviso.id_cliente,
        "oficio": aviso.oficio,
        "descripcion": aviso.descripcion,
        "zona": aviso.zona,
        "telefono": aviso.telefono,
        "estado": aviso.estado,
        "fecha_creacion": aviso.fecha_creacion,
    }