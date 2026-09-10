# APIRouter nos permite crear un grupo de endpoints relacionados.
# En este caso, todos los endpoints relacionados con autenticación.
from fastapi import APIRouter, Depends, HTTPException

# Session representa una sesión de conexión con nuestra base de datos.
from sqlalchemy.orm import Session

# Importamos la función que abre y cierra la conexión a la BD.
from app.database import get_db

# Importamos nuestro modelo Usuario para poder consultar la tabla "usuario".
from app.models.usuario import Usuario

# Importamos el schema que creamos anteriormente.
# LoginRequest define los datos que debe recibir el login:
# correo y contraseña.
from app.schemas.auth import LoginRequest, RegisterRequest

# Importamos las funciones que creamos en auth.py:
# - verificar_contrasena() compara la contraseña con el hash guardado.
# - crear_token() genera el JWT.
from app.auth import (
    verificar_contrasena, 
    crear_token,
    hashear_contrasena
)


# Creamos un router para los endpoints de autenticación.
router = APIRouter(
    # Todos los endpoints de este router comenzarán con /auth
    prefix="/auth",

    # Esto sirve para agruparlos dentro de Swagger (/docs).
    tags=["Autenticación"]
)


# Endpoint para registrar un nuevo usuario.
#
# POST /auth/register
#
# Recibe:
# - nombre_apellido
# - correo
# - contrasena
#
# Luego:
# 1. Comprueba que el correo no esté registrado.
# 2. Hashea la contraseña.
# 3. Crea el usuario.
# 4. Lo guarda en la base de datos.
@router.post("/register")
def register(
    datos: RegisterRequest,
    db: Session = Depends(get_db)
):

    # Buscamos si ya existe un usuario
    # con el correo recibido.
    usuario_existente = db.query(Usuario).filter(
        Usuario.correo == datos.correo
    ).first()

    # Si encontramos un usuario,
    # significa que ese correo ya está registrado.
    if usuario_existente:
        raise HTTPException(
            status_code=400,
            detail="El correo ya está registrado"
        )

    # Convertimos la contraseña original
    # en un hash antes de guardarla.
    contrasena_hash = hashear_contrasena(
        datos.contrasena
    )

    # Creamos un nuevo objeto Usuario.
    nuevo_usuario = Usuario(
        nombre_apellido=datos.nombre_apellido,
        correo=datos.correo,
        contrasena=contrasena_hash
    )

    # Agregamos el nuevo usuario a la sesión.
    db.add(nuevo_usuario)

    # Confirmamos los cambios en la base de datos.
    db.commit()

    # Actualizamos el objeto para obtener,
    # por ejemplo, el id generado automáticamente.
    db.refresh(nuevo_usuario)

    # Devolvemos información del usuario creado.
    #
    # IMPORTANTE:
    # Nunca devolvemos la contraseña ni su hash.
    return {
        "mensaje": "Usuario registrado correctamente",
        "id_usuario": nuevo_usuario.id_usuario,
        "nombre_apellido": nuevo_usuario.nombre_apellido,
        "correo": nuevo_usuario.correo
    }



# Creamos el endpoint:
#
# POST /auth/login
#
# datos -> contiene el correo y la contraseña enviados por el usuario.
# db -> representa la conexión con nuestra base de datos.
#
# Depends(get_db) le dice a FastAPI:
# "Antes de ejecutar esta función, dame una sesión de la base de datos".
@router.post("/login")
def login(
    datos: LoginRequest,
    db: Session = Depends(get_db)
):

    # Buscamos en la tabla Usuario un registro cuyo correo
    # sea igual al correo que envió el usuario.
    #
    # .first() devuelve el primer resultado encontrado.
    # Si no encuentra ninguno, devuelve None.
    usuario = db.query(Usuario).filter(
        Usuario.correo == datos.correo
    ).first()


    # Si no encontramos un usuario con ese correo,
    # devolvemos un error HTTP 401 (No autorizado).
    #
    # No decimos "el correo no existe" porque eso podría
    # revelar información sobre las cuentas registradas.
    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos"
        )


    # Ahora verificamos la contraseña.
    #
    # datos.contrasena -> contraseña que acaba de escribir el usuario.
    #
    # usuario.contrasena -> hash de contraseña que tenemos
    # almacenado en nuestra base de datos.
    #
    # verificar_contrasena() se encarga de comparar ambas.
    if not verificar_contrasena(
        datos.contrasena,
        usuario.contrasena
    ):

        # Si las contraseñas no coinciden,
        # devolvemos nuevamente un error 401.
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos"
        )


    # Llegamos acá solamente si:
    #
    # 1. El usuario existe.
    # 2. La contraseña es correcta.
    #
    # Ahora creamos el JWT.
    #
    # "sub" significa subject y lo utilizaremos para identificar
    # al usuario autenticado.
    #
    # Guardamos también el correo dentro del token.
    token = crear_token({
        "sub": str(usuario.id_usuario),
        "correo": usuario.correo
    })


    # Finalmente devolvemos el JWT al usuario.
    #
    # access_token -> contiene el JWT.
    # token_type -> indica que estamos utilizando un token Bearer.
    return {
        "access_token": token,
        "token_type": "bearer"
    }