"""FastAPI service for the Recycling Robotic Arm dashboard."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv

load_dotenv()

from camera import camera_manager
from detection import detection_service, get_detection_status
from errors import HardwareError, HardwareTimeout
from serial_manager import serial_manager
from websocket_manager import websocket_manager

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("recycling_arm_api")


def get_system_status() -> dict[str, Any]:
    return {
        "backend": {"available": True, "message": "API is running"},
        "esp32": serial_manager.status(),
        "camera": camera_manager.status(),
        "detection": get_detection_status(),
    }


async def broadcast_status() -> None:
    await websocket_manager.broadcast({"type": "status", "data": get_system_status()})


async def status_broadcaster() -> None:
    """Send status snapshots to connected clients; no hardware is opened here."""
    while True:
        await broadcast_status()
        await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(status_broadcaster(), name="status-broadcaster")
    detection_task = asyncio.create_task(
        detection_service.run(camera_manager.read_frame, websocket_manager.broadcast_bytes, broadcast_status),
        name="bottle-detection",
    )
    try:
        yield
    finally:
        detection_service.stop()
        detection_task.cancel()
        with suppress(asyncio.CancelledError):
            await detection_task
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        # Resources are independent. Release failures are logged, not allowed to mask shutdown.
        try:
            await asyncio.to_thread(camera_manager.release)
        except Exception:
            logger.exception("Camera cleanup failed")
        try:
            await asyncio.to_thread(serial_manager.disconnect)
        except Exception:
            logger.exception("Serial cleanup failed")


app = FastAPI(
    title="Recycling Robotic Arm API",
    description="Camera bottle-presence detection API. Fill-state classification and robot movement are not implemented.",
    version="0.1.0",
    lifespan=lifespan,
)

origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(HardwareError)
async def hardware_error_handler(_: Request, exc: HardwareError) -> JSONResponse:
    status_code = (
        400 if exc.code == "configuration_error"
        else 503 if exc.code == "hardware_unavailable"
        else 504 if isinstance(exc, HardwareTimeout)
        else 500
    )
    return JSONResponse(status_code=status_code, content={"error": {"code": exc.code, "message": exc.message, "resource": exc.resource}})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": "Request validation failed.", "details": exc.errors()}})


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": "http_error", "message": str(exc.detail)}})


@app.exception_handler(Exception)
async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API error", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": {"code": "internal_error", "message": "An unexpected server error occurred."}})


@app.get("/api/status")
async def api_status() -> dict[str, Any]:
    return get_system_status()


@app.get("/api/esp32/status")
async def esp32_status() -> dict[str, Any]:
    return serial_manager.status()


@app.post("/api/esp32/connect")
async def esp32_connect(payload: dict[str, str] | None = None) -> dict[str, Any]:
    port = payload.get("port") if payload else None
    result = await asyncio.to_thread(serial_manager.connect, port)
    await broadcast_status()
    return result


@app.post("/api/esp32/disconnect")
async def esp32_disconnect() -> dict[str, Any]:
    result = await asyncio.to_thread(serial_manager.disconnect)
    await broadcast_status()
    return result


@app.post("/api/esp32/test")
async def esp32_test() -> dict[str, Any]:
    return await asyncio.to_thread(serial_manager.test_connection)


@app.get("/api/esp32/device-status")
async def esp32_device_status() -> dict[str, Any]:
    return await asyncio.to_thread(serial_manager.get_device_status)


@app.get("/api/camera/status")
async def camera_status() -> dict[str, Any]:
    return camera_manager.status()


@app.post("/api/camera/start")
async def camera_start(payload: dict[str, int] | None = None) -> dict[str, Any]:
    device_index = payload.get("device_index") if payload else None
    result = await asyncio.to_thread(camera_manager.initialize, device_index)
    detection_service.start()
    await broadcast_status()
    return {**result, "detection": get_detection_status()}


@app.post("/api/camera/stop")
async def camera_stop() -> dict[str, Any]:
    detection_service.stop()
    result = await asyncio.to_thread(camera_manager.release)
    await broadcast_status()
    return {**result, "detection": get_detection_status()}


@app.get("/api/detection/status")
async def detection_status() -> dict[str, Any]:
    return get_detection_status()


@app.websocket("/ws")
async def status_websocket(websocket: WebSocket) -> None:
    await websocket_manager.connect(websocket)
    try:
        await websocket_manager.send_json(websocket, {"type": "status", "data": get_system_status()})
        # Clients may send text ping frames; frames and status are server-to-client.
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(websocket)
