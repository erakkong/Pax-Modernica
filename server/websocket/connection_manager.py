"""
Pax Modernica - WebSocket Connection Manager
Maintains active client connections and broadcasts server-authoritative ticks and events.
"""

from typing import List, Dict, Any
from fastapi import WebSocket
import logging

logger = logging.getLogger("pax_websocket")

class ConnectionManager:
    """Manages active WebSockets and handles broadcasting."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket Client verbunden. Aktive Verbindungen: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket Client getrennt. Verbleibend: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcasts JSON payload to all connected clients."""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            if dead in self.active_connections:
                self.active_connections.remove(dead)

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Sends JSON payload to a single connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Fehler beim Senden an Client: {e}")

manager = ConnectionManager()
