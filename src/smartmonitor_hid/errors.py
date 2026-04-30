class SmartMonitorError(Exception):
    """Base exception for the smartmonitor_hid package."""


class SmartMonitorBridgeError(SmartMonitorError):
    """Raised when a bridge into the host project is unavailable."""


class SmartMonitorTransportError(SmartMonitorError):
    """Raised for HID transport/runtime communication errors."""


class SmartMonitorCompilerError(SmartMonitorError):
    """Raised for `.ui -> img.dat` compile failures."""
