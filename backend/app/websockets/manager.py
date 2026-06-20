# WebSocket connection manager
"""
Maintains a registry of all active browser connections and
provides a broadcast method to push messages to all of them.
"""

import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Thread-safe manager for active WebSocket connections."""

    def __init__(self):
        self.active_connections: set = set()

    async def connect(self, websocket: WebSocket):
        """Accept a new browser connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"🔌 WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a disconnected browser."""
        self.active_connections.discard(websocket)
        logger.info(f"🔌 WebSocket disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        """Send a message to ALL connected browsers."""
        if not self.active_connections:
            return

        dead = set()
        for websocket in list(self.active_connections):
            try:
                await websocket.send_text(message)
            except Exception:
                dead.add(websocket)

        for ws in dead:
            self.disconnect(ws)

    async def send_to(self, websocket: WebSocket, message: str):
        """Send a message to one specific connection."""
        try:
            await websocket.send_text(message)
        except Exception:
            self.disconnect(websocket)

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


# Global singleton
ws_manager = ConnectionManager()
