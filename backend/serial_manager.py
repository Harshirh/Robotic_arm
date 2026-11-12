"""Thread-safe newline-delimited JSON serial protocol for the ESP32."""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any

import serial
from serial.tools import list_ports

from errors import (
    ConfigurationError,
    HardwareOperationError,
    HardwareTimeout,
    HardwareUnavailable,
)

DEFAULT_BAUD_RATE = 115200
MAX_RESPONSE_BYTES = 4096
SUPPORTED_COMMANDS = {"PING", "GET_STATUS"}


class SerialManager:
    def __init__(self, baud_rate: int = DEFAULT_BAUD_RATE, response_timeout: float = 2.0) -> None:
        self.baud_rate = baud_rate
        self.response_timeout = response_timeout
        self._connection: serial.Serial | None = None
        self._port: str | None = None
        self._lock = threading.RLock()

    def status(self) -> dict[str, Any]:
        with self._lock:
            connected = bool(self._connection and self._connection.is_open)
            return {
                "connected": connected,
                "port": self._port if connected else None,
                "baud_rate": self.baud_rate,
                "available_ports": self.available_ports(),
                "message": "Serial port is open" if connected else "ESP32 is not connected",
            }

    @staticmethod
    def available_ports() -> list[dict[str, str | None]]:
        try:
            return [
                {"device": port.device, "description": port.description, "hwid": port.hwid}
                for port in list_ports.comports()
            ]
        except Exception:
            return []

    def connect(self, port: str | None = None) -> dict[str, Any]:
        selected_port = (port or os.getenv("SERIAL_PORT", "")).strip()
        if not selected_port:
            raise ConfigurationError(
                "Provide a serial port (for example COM3) or set SERIAL_PORT.", resource="esp32"
            )
        if os.name == "nt" and not selected_port.upper().startswith("COM"):
            raise ConfigurationError("On Windows, use a COM port such as COM3.", resource="esp32")

        with self._lock:
            if self._connection and self._connection.is_open:
                if self._port == selected_port:
                    return self.status()
                self._close_locked()

            try:
                self._connection = serial.Serial(
                    port=selected_port,
                    baudrate=self.baud_rate,
                    timeout=self.response_timeout,
                    write_timeout=self.response_timeout,
                )
                self._port = selected_port
                # Opening a CP2102 serial port may reset an ESP32 through DTR/RTS.
                # Let its bootloader/application settle, then discard boot log lines.
                time.sleep(1.5)
                self._connection.reset_input_buffer()
            except (serial.SerialException, OSError, ValueError) as exc:
                self._close_after_error_locked()
                raise HardwareUnavailable(
                    f"Could not open {selected_port}. Check the COM port and USB connection.",
                    resource="esp32",
                ) from exc
            return self.status()

    def disconnect(self) -> dict[str, Any]:
        with self._lock:
            try:
                self._close_locked()
            except (serial.SerialException, OSError) as exc:
                self._close_after_error_locked()
                raise HardwareOperationError("Failed to close the ESP32 serial port.", resource="esp32") from exc
            return self.status()

    def send_command(self, command: dict[str, Any]) -> dict[str, Any]:
        """Send one JSON command and read one JSON response, both newline-delimited.

        Only non-motion commands are allowed while the robotic arm is being built.
        """
        command_name = command.get("command")
        if command_name not in SUPPORTED_COMMANDS:
            raise ConfigurationError(
                f"Unsupported serial command. Allowed commands: {', '.join(sorted(SUPPORTED_COMMANDS))}.",
                resource="esp32",
            )

        with self._lock:
            connection = self._require_connection_locked()
            try:
                # Drop unsolicited/stale boot text so the response is correlated to this request.
                connection.reset_input_buffer()
                payload = json.dumps(command, separators=(",", ":"), ensure_ascii=True).encode("utf-8") + b"\n"
                connection.write(payload)
                connection.flush()
                raw_response = connection.readline(MAX_RESPONSE_BYTES + 1)
            except (serial.SerialException, OSError) as exc:
                port = self._port
                self._close_after_error_locked()
                raise HardwareUnavailable(
                    f"Serial communication with {port or 'the ESP32'} was interrupted.", resource="esp32"
                ) from exc

            if not raw_response:
                raise HardwareTimeout(
                    f"ESP32 did not respond to {command_name} within {self.response_timeout:g} seconds.",
                    resource="esp32",
                )
            if len(raw_response) > MAX_RESPONSE_BYTES or not raw_response.endswith(b"\n"):
                self._close_after_error_locked()
                raise HardwareOperationError(
                    "ESP32 response exceeded the protocol limit or was not newline terminated; connection closed.",
                    resource="esp32",
                )

            try:
                response = json.loads(raw_response.decode("utf-8").strip())
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise HardwareOperationError("ESP32 returned malformed JSON.", resource="esp32") from exc
            if not isinstance(response, dict):
                raise HardwareOperationError("ESP32 response must be a JSON object.", resource="esp32")
            return response

    def test_connection(self) -> dict[str, Any]:
        """Perform a protocol-level PING/PONG check; no motion command is sent."""
        response = self.send_command({"command": "PING"})
        if response.get("status") != "success" or response.get("response") != "PONG":
            raise HardwareOperationError(
                "ESP32 returned an unexpected response to PING.", resource="esp32"
            )
        return {
            "connected": True,
            "port": self._port,
            "message": "ESP32 responded to PING with PONG.",
            "device": response.get("device"),
            "response": response,
        }

    def get_device_status(self) -> dict[str, Any]:
        response = self.send_command({"command": "GET_STATUS"})
        if response.get("status") != "success":
            raise HardwareOperationError("ESP32 could not provide its status.", resource="esp32")
        return response

    def _require_connection_locked(self) -> serial.Serial:
        if not self._connection or not self._connection.is_open:
            self._close_after_error_locked()
            raise HardwareUnavailable("ESP32 is not connected. Connect a COM port first.", resource="esp32")
        return self._connection

    def _close_locked(self) -> None:
        connection = self._connection
        self._connection = None
        self._port = None
        if connection is not None and connection.is_open:
            connection.close()

    def _close_after_error_locked(self) -> None:
        try:
            self._close_locked()
        except (serial.SerialException, OSError):
            self._connection = None
            self._port = None


try:
    configured_baud_rate = int(os.getenv("BAUD_RATE", str(DEFAULT_BAUD_RATE)))
    if configured_baud_rate <= 0:
        raise ValueError("BAUD_RATE must be positive")
except ValueError:
    configured_baud_rate = DEFAULT_BAUD_RATE

try:
    configured_response_timeout = max(0.1, float(os.getenv("SERIAL_TIMEOUT", "2.0")))
except ValueError:
    configured_response_timeout = 2.0

serial_manager = SerialManager(
    baud_rate=configured_baud_rate,
    response_timeout=configured_response_timeout,
)
