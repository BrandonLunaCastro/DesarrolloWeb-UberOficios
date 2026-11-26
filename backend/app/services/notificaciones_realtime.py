import asyncio
import logging
from collections import defaultdict

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect


logger = logging.getLogger(__name__)


class NotificationConnectionManager:
    # Registra sockets por usuario para enviar eventos solo a sus sesiones activas.
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._user_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

    def connect(self, id_usuario: int, websocket: WebSocket) -> None:
        self._connections[id_usuario].add(websocket)

    def disconnect(self, id_usuario: int, websocket: WebSocket) -> None:
        connections = self._connections.get(id_usuario)
        if connections is None:
            return
        connections.discard(websocket)
        # Quita la clave cuando ya no quedan sockets para ese usuario.
        if not connections:
            self._connections.pop(id_usuario, None)

    async def broadcast(self, id_usuarios: list[int], evento: dict) -> None:
        # Deduplicar IDs evita enviar dos veces el mismo evento a un usuario.
        for id_usuario in set(id_usuarios):
            desconectados = []
            async with self._user_locks[id_usuario]:
                for websocket in self._connections.get(id_usuario, set()):
                    try:
                        await websocket.send_json(evento)
                    except (OSError, RuntimeError, WebSocketDisconnect) as error:
                        logger.warning(
                            "No se pudo enviar una notificación en tiempo real; "
                            "se cerrará la conexión fallida",
                            exc_info=error,
                        )
                        desconectados.append(websocket)

                for websocket in desconectados:
                    self.disconnect(id_usuario, websocket)


notification_connections = NotificationConnectionManager()
