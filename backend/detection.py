"""Bottle object detection and a deliberately separate fill-state classifier."""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class BottleDetectionService:
    """Runs bottle-only YOLO inference over frames read by CameraManager.

    COCO bottle detection supplies presence and box confidence. It does not
    determine fill level: a detected bottle remains `uncertain` until a
    separately validated fill-state model or sensor is integrated.
    """

    def __init__(self) -> None:
        self.model_path = os.getenv("YOLO_MODEL", "yolo26n.pt")
        self.confidence_threshold = self._read_float("DETECTION_CONFIDENCE", 0.25, 0.01, 0.99)
        self.image_size = self._read_int("DETECTION_IMAGE_SIZE", 640, 160, 1280)
        self._model: Any = None
        self._model_error: str | None = None
        self._bottle_class_ids: list[int] = []
        self._active = threading.Event()
        self._status_lock = threading.RLock()
        self._status: dict[str, Any] = self._empty_status()

    @staticmethod
    def _read_float(name: str, fallback: float, minimum: float, maximum: float) -> float:
        try:
            return min(max(float(os.getenv(name, str(fallback))), minimum), maximum)
        except ValueError:
            return fallback

    @staticmethod
    def _read_int(name: str, fallback: int, minimum: int, maximum: int) -> int:
        try:
            return min(max(int(os.getenv(name, str(fallback))), minimum), maximum)
        except ValueError:
            return fallback

    def _empty_status(self) -> dict[str, Any]:
        return {
            "running": False,
            "state": "waiting",
            "detected": None,
            "detections": [],
            "confidence": None,
            "classification": {
                "state": "uncertain",
                "confidence": None,
                "message": "Fill level is not classified by bottle-presence detection.",
            },
            "model": self.model_path,
            "message": "Detection is waiting for the camera to start.",
            "updated_at": None,
        }

    def get_status(self) -> dict[str, Any]:
        with self._status_lock:
            # Return a detached snapshot so request handlers cannot mutate shared state.
            return {
                **self._status,
                "detections": [dict(item) for item in self._status["detections"]],
                "classification": dict(self._status["classification"]),
            }

    def _set_status(self, **updates: Any) -> None:
        with self._status_lock:
            self._status = {**self._status, **updates, "updated_at": datetime.now(timezone.utc).isoformat()}

    def start(self) -> dict[str, Any]:
        self._active.set()
        self._set_status(
            running=True,
            state="waiting",
            detected=None,
            detections=[],
            confidence=None,
            message="Camera started; waiting for the first frame.",
        )
        return self.get_status()

    def stop(self) -> dict[str, Any]:
        self._active.clear()
        self._set_status(
            running=False,
            state="waiting",
            detected=None,
            detections=[],
            confidence=None,
            classification={
                "state": "uncertain",
                "confidence": None,
                "message": "No active frame; fill level has not been classified.",
            },
            message="Bottle detection stopped.",
        )
        return self.get_status()

    def _load_model(self) -> None:
        if self._model is not None:
            return
        if self._model_error is not None:
            raise RuntimeError(self._model_error)
        try:
            from ultralytics import YOLO

            self._model = YOLO(self.model_path)
            names = self._model.names
            items = names.items() if isinstance(names, dict) else enumerate(names)
            self._bottle_class_ids = [int(class_id) for class_id, name in items if str(name).strip().casefold() == "bottle"]
            if not self._bottle_class_ids:
                raise RuntimeError(f"Model '{self.model_path}' has no class named 'bottle'.")
        except Exception as exc:
            self._model = None
            self._model_error = f"Bottle detector could not load model '{self.model_path}': {exc}"
            logger.exception("Bottle detector model initialization failed")
            raise RuntimeError(self._model_error) from exc

    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, list[dict[str, Any]]]:
        """Run bottle detection, draw boxes, and update presence-only status."""
        try:
            self._load_model()
        except Exception as exc:
            self._set_status(
                running=True,
                state="unavailable",
                detected=None,
                detections=[],
                confidence=None,
                message=str(exc),
            )
            return frame, []

        try:
            results = self._model.predict(
                source=frame,
                classes=self._bottle_class_ids,
                conf=self.confidence_threshold,
                imgsz=self.image_size,
                device="cpu",
                verbose=False,
            )
            boxes = results[0].boxes if results else None
            detections: list[dict[str, Any]] = []
            annotated = frame.copy()
            if boxes is not None:
                xyxy = boxes.xyxy.cpu().numpy()
                confidences = boxes.conf.cpu().numpy()
                class_ids = boxes.cls.cpu().numpy().astype(int)
                for coordinates, confidence, class_id in zip(xyxy, confidences, class_ids):
                    if int(class_id) not in self._bottle_class_ids:
                        continue
                    x1, y1, x2, y2 = (int(value) for value in coordinates)
                    confidence_value = float(confidence)
                    label = f"Bottle {confidence_value:.0%}"
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (70, 222, 161), 2)
                    text_y = max(20, y1 - 8)
                    cv2.putText(annotated, label, (x1, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (70, 222, 161), 2, cv2.LINE_AA)
                    detections.append({
                        "label": "bottle",
                        "confidence": round(confidence_value, 4),
                        "box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    })

            detected = bool(detections)
            confidences = [item["confidence"] for item in detections]
            self._set_status(
                running=True,
                state="bottle_detected" if detected else "no_bottle_detected",
                detected=detected,
                detections=detections,
                confidence=max(confidences) if confidences else None,
                classification={
                    "state": "uncertain" if detected else "no_bottle_detected",
                    "confidence": None,
                    "message": (
                        "Bottle presence detected; fill level is not assessed. Transparency is not used to infer emptiness."
                        if detected
                        else "No bottle detected in the current frame."
                    ),
                },
                message="Bottle detected." if detected else "No bottle detected.",
            )
            return annotated, detections
        except Exception as exc:
            logger.exception("Bottle inference failed")
            self._set_status(
                running=True,
                state="unavailable",
                detected=None,
                detections=[],
                confidence=None,
                message=f"Bottle inference failed: {exc}",
            )
            return frame, []

    async def run(
        self,
        read_frame: Callable[[], np.ndarray | None],
        broadcast_frame: Callable[[bytes], Awaitable[None]],
        broadcast_status: Callable[[], Awaitable[None]],
    ) -> None:
        """Background capture/inference loop; frames are JPEG binary WebSocket messages."""
        while True:
            if not self._active.is_set():
                await asyncio.sleep(0.1)
                continue

            frame = await asyncio.to_thread(read_frame)
            if not self._active.is_set():
                # A manual stop can release the camera while read_frame is blocked.
                continue
            if frame is None:
                self._active.clear()
                self._set_status(
                    running=False,
                    state="camera_disconnected",
                    detected=None,
                    detections=[],
                    confidence=None,
                    message="Camera stopped returning frames. Detection paused; restart the camera to retry.",
                )
                await broadcast_status()
                continue

            annotated, _ = await asyncio.to_thread(self.process_frame, frame)
            if not self._active.is_set():
                # A stop request may arrive while model inference is running.
                self._set_status(
                    running=False,
                    state="waiting",
                    detected=None,
                    detections=[],
                    confidence=None,
                    message="Bottle detection stopped.",
                )
                continue
            ok, encoded = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 82])
            if ok:
                await broadcast_frame(encoded.tobytes())
            else:
                logger.warning("Could not encode webcam frame as JPEG")


detection_service = BottleDetectionService()


def get_detection_status() -> dict[str, Any]:
    return detection_service.get_status()
