"""WebSocket connection registry and best-effort JSON broadcaster."""

from __future__ import annotations

import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._send_locks: dict[WebSocket, asyncio.Lock] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
            self._send_locks[websocket] = asyncio.Lock()

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
            self._send_locks.pop(websocket, None)

    async def send_json(self, websocket: WebSocket, message: dict) -> None:
        async with self._lock:
            send_lock = self._send_locks.get(websocket)
        if send_lock is not None:
            async with send_lock:
                await websocket.send_json(message)

    async def broadcast(self, message: dict) -> None:
        async with self._lock:
            connections = [(websocket, self._send_locks[websocket]) for websocket in self._connections]
        disconnected: list[WebSocket] = []
        for websocket, send_lock in connections:
            try:
                async with send_lock:
                    await websocket.send_json(message)
            except Exception:
                logger.debug("Removing an inactive WebSocket client")
                disconnected.append(websocket)
        if disconnected:
            async with self._lock:
                self._connections.difference_update(disconnected)
                for websocket in disconnected:
                    self._send_locks.pop(websocket, None)

    async def broadcast_bytes(self, message: bytes) -> None:
        """Send a binary frame to every connected WebSocket client."""
        async with self._lock:
            connections = [(websocket, self._send_locks[websocket]) for websocket in self._connections]
        disconnected: list[WebSocket] = []
        for websocket, send_lock in connections:
            try:
                async with send_lock:
                    await websocket.send_bytes(message)
            except Exception:
                logger.debug("Removing an inactive WebSocket client")
                disconnected.append(websocket)
        if disconnected:
            async with self._lock:
                self._connections.difference_update(disconnected)
                for websocket in disconnected:
                    self._send_locks.pop(websocket, None)


websocket_manager = WebSocketManager()
