from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session

from app.auth import (
    crear_token,
    get_current_user,
    get_current_user_id,
    hashear_contrasena,
    verificar_contrasena,
)
from app.database import get_db
from app.models.PrestadorServicio import PrestadorServicio
from app.models.creditos import (
    BilleteraCredito,
    TipoTransaccionEnum,
    TransaccionCredito,
)
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.services.creditos import BONO_MENSUAL_CREDITOS
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
        prestador = PrestadorServicio(
            saldo_creditos=BONO_MENSUAL_CREDITOS
        )
        billetera = BilleteraCredito(saldo_actual=BONO_MENSUAL_CREDITOS)
        billetera.transacciones.append(
            TransaccionCredito(
                monto=BONO_MENSUAL_CREDITOS,
                tipo=TipoTransaccionEnum.BONIFICACION,
                referencia_tipo="bonificacion_inicial",
                descripcion="Bonificación inicial de créditos por registro",
            )
        )
        prestador.billetera = billetera
        nuevo_usuario.prestador = prestador

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
    usuario = (
        db.query(Usuario)
        .options(joinedload(Usuario.rol))
        .filter(Usuario.email == datos.email)
        .first()
    )
    if not usuario:
        db.rollback()
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos",
        )

    id_usuario = usuario.id_usuario
    password_hash = usuario.password_hash
    email = usuario.email
    rol = usuario.rol.nombre
    db.rollback()

    if not verificar_contrasena(datos.contrasena, password_hash):
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos",
        )

    token = crear_token({
        "sub": str(id_usuario),
        "email": email,
        "rol": rol,
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


@router.get("/me/saldo")
def obtener_saldo_prestador(
    db: Session = Depends(get_db),
    id_usuario: int = Depends(get_current_user_id),
):
    prestador = (
        db.query(PrestadorServicio)
        .filter(PrestadorServicio.id_usuario == id_usuario)
        .first()
    )
    if prestador is None:
        raise HTTPException(
            status_code=403,
            detail="Se requiere una cuenta de prestador para consultar el saldo",
        )

    return {"saldo_creditos": prestador.saldo_creditos}
