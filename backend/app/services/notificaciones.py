from app.models.notificacion import Notificacion


def crear_notificacion(
    db,
    *,
    id_usuario: int,
    tipo: str,
    mensaje: str,
    id_postulacion: int | None = None,
) -> Notificacion:
    # Agrega la notificación a la sesión; el llamador decide cuándo confirmar.
    notificacion = Notificacion(
        id_usuario=id_usuario,
        id_postulacion=id_postulacion,
        tipo=tipo,
        mensaje=mensaje,
    )
    db.add(notificacion)
    return notificacion