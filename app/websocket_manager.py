from typing import Dict, List
from fastapi import WebSocket
import asyncio

class ConnectionManager:
    def __init__(self):
        # Active room connections: room_id → list of WebSocket clients
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.lock = asyncio.Lock()  # Ensure thread-safe operations

    async def connect(self, room_id: str, websocket: WebSocket):
        """Add client WebSocket to a room."""
        async with self.lock:
            if room_id not in self.active_connections:
                self.active_connections[room_id] = []
            self.active_connections[room_id].append(websocket)

    async def disconnect(self, room_id: str, websocket: WebSocket):
        """Remove client WebSocket from a room."""
        async with self.lock:
            if room_id in self.active_connections:
                if websocket in self.active_connections[room_id]:
                    self.active_connections[room_id].remove(websocket)
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]  # Cleanup empty room

    async def broadcast(self, room_id: str, message: dict):
        """Send message to all clients in a room."""
        async with self.lock:
            if room_id in self.active_connections:
                # Send concurrently to all clients
                await asyncio.gather(*[
                    connection.send_json(message)
                    for connection in self.active_connections[room_id]
                ])

# Global instance of connection manager
manager = ConnectionManager()
