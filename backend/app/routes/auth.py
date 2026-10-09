from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import (
    crear_token,
    get_current_user,
    hashear_contrasena,
    verificar_contrasena,
)
from app.database import get_db
from app.models.PrestadorServicio import PrestadorServicio
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, RegisterRequest

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
)


@router.post("/register")
def register(
    datos: RegisterRequest,
    db: Session = Depends(get_db),
):
    if db.query(Usuario).filter(Usuario.email == datos.email).first():
        raise HTTPException(
            status_code=400,
            detail="El correo ya está registrado",
        )

    rol = db.query(Rol).filter(Rol.nombre == datos.rol).first()
    if rol is None:
        raise HTTPException(
            status_code=503,
            detail=f"El rol {datos.rol} no está configurado en la base de datos",
        )

    nuevo_usuario = Usuario(
        nombre=datos.nombre,
        apellido=datos.apellido,
        email=datos.email,
        password_hash=hashear_contrasena(datos.contrasena),
        telefono=datos.telefono,
        rol=rol,
    )
    if datos.rol == "PRESTADOR":
        nuevo_usuario.prestador = PrestadorServicio()

    db.add(nuevo_usuario)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if db.query(Usuario).filter(Usuario.email == datos.email).first():
            raise HTTPException(
                status_code=400,
                detail="El correo ya está registrado",
            ) from error
        raise

    db.refresh(nuevo_usuario)
    return {
        "mensaje": "Usuario registrado correctamente",
        "id_usuario": nuevo_usuario.id_usuario,
        "nombre": nuevo_usuario.nombre,
        "apellido": nuevo_usuario.apellido,
        "email": nuevo_usuario.email,
        "rol": nuevo_usuario.rol.nombre,
    }


@router.post("/login")
def login(
    datos: LoginRequest,
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos",
        )

    if not verificar_contrasena(datos.contrasena, usuario.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos",
        )

    token = crear_token({
        "sub": str(usuario.id_usuario),
        "email": usuario.email,
        "rol": usuario.rol.nombre,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/me")
def obtener_usuario_actual(usuario: Usuario = Depends(get_current_user)):
    return {
        "id_usuario": usuario.id_usuario,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "email": usuario.email,
        "telefono": usuario.telefono,
        "foto_perfil": usuario.foto_perfil,
        "fecha_registro": usuario.fecha_registro,
        "rol": usuario.rol.nombre,
    }


# ----En esta parte iria la ruta de avisos general----

 #@router.get("/avisos/zona/{zona}")
  #   def obtener_avisos_por_zona()
