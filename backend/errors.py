"""Structured errors shared by the hardware managers."""


class HardwareError(Exception):
    code = "hardware_error"

    def __init__(self, message: str, *, resource: str):
        super().__init__(message)
        self.message = message
        self.resource = resource


class HardwareUnavailable(HardwareError):
    code = "hardware_unavailable"


class HardwareOperationError(HardwareError):
    code = "hardware_operation_failed"


class HardwareTimeout(HardwareError):
    code = "hardware_timeout"


class ConfigurationError(HardwareError):
    code = "configuration_error"
