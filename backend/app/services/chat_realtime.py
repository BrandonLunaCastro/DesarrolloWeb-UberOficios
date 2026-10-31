import asyncio
import logging
from collections import defaultdict

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect


logger = logging.getLogger(__name__)


class ChatConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._conversation_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

    def lock_for(self, id_conversacion: int) -> asyncio.Lock:
        return self._conversation_locks[id_conversacion]

    def connect(self, id_conversacion: int, websocket: WebSocket) -> None:
        self._connections[id_conversacion].add(websocket)

    def disconnect(self, id_conversacion: int, websocket: WebSocket) -> None:
        connections = self._connections.get(id_conversacion)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(id_conversacion, None)

    async def broadcast(self, id_conversacion: int, mensaje: dict) -> None:
        async with self.lock_for(id_conversacion):
            desconectados = []
            for websocket in self._connections.get(id_conversacion, set()):
                try:
                    await websocket.send_json({"type": "message", "message": mensaje})
                except (OSError, RuntimeError, WebSocketDisconnect) as error:
                    logger.warning(
                        "No se pudo enviar un mensaje en tiempo real; "
                        "se cerrará la conexión fallida",
                        exc_info=error,
                    )
                    desconectados.append(websocket)

            for websocket in desconectados:
                self.disconnect(id_conversacion, websocket)


chat_connections = ChatConnectionManager()
