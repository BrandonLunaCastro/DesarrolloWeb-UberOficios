from app.models.notificacion import Notificacion


def crear_notificacion(
    db,
    *,
    id_usuario: int,
    tipo: str,
    mensaje: str,
) -> Notificacion:
    notificacion = Notificacion(
        id_usuario=id_usuario,
        tipo=tipo,
        mensaje=mensaje,
    )
    db.add(notificacion)
    return notificacion