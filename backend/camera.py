"""Opt-in OpenCV camera lifecycle manager, independent of ESP32 serial."""

from __future__ import annotations

import os
import threading
from typing import Any

import cv2

from errors import HardwareOperationError, HardwareUnavailable


class CameraManager:
    def __init__(self, device_index: int | None = None) -> None:
        configured_index = os.getenv("CAMERA_INDEX", "0")
        try:
            self.device_index = device_index if device_index is not None else int(configured_index)
        except ValueError:
            self.device_index = 0
        self._capture: cv2.VideoCapture | None = None
        self._lock = threading.RLock()

    def status(self) -> dict[str, Any]:
        with self._lock:
            active = bool(self._capture and self._capture.isOpened())
            return {
                "active": active,
                "device_index": self.device_index if active else None,
                "message": "Camera is active" if active else "Camera is inactive",
            }

    def initialize(self, device_index: int | None = None) -> dict[str, Any]:
        with self._lock:
            if self._capture and self._capture.isOpened():
                return self.status()
            if device_index is not None:
                self.device_index = device_index

            capture: cv2.VideoCapture | None = None
            try:
                capture = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(self.device_index)
                if not capture.isOpened():
                    capture.release()
                    raise HardwareUnavailable(
                        f"Could not open camera device {self.device_index}.", resource="camera"
                    )
                self._capture = capture
            except HardwareUnavailable:
                self._capture = None
                raise
            except Exception as exc:
                if capture is not None:
                    capture.release()
                self._capture = None
                raise HardwareUnavailable("Camera initialization failed.", resource="camera") from exc
            return self.status()

    def release(self) -> dict[str, Any]:
        with self._lock:
            capture = self._capture
            self._capture = None
            try:
                if capture is not None:
                    capture.release()
            except Exception as exc:
                raise HardwareOperationError("Failed to release the camera device.", resource="camera") from exc
            return self.status()

    def read_frame(self):
        """Read one frame; release the device if the camera stops responding."""
        with self._lock:
            capture = self._capture
            if capture is None or not capture.isOpened():
                return None
            try:
                ok, frame = capture.read()
            except Exception:
                ok, frame = False, None
            if not ok or frame is None:
                self._capture = None
                try:
                    capture.release()
                except Exception:
                    pass
                return None
            return frame


camera_manager = CameraManager()
