from __future__ import annotations

from dataclasses import dataclass


USB_VENDOR_ID = "00000483"
USB_PRODUCT_ID = "00000065"
HID_REPORT_SIZE = 64

SMARTMONITOR_RESET_COMMAND = b"\x01reset"
SMARTMONITOR_YMODEM_COMMAND = b"ymodem"
SMARTMONITOR_TIME_COMMAND = 0x03

YMODEM_SOH = 0x01
YMODEM_STX = 0x02
YMODEM_EOT = 0x04
YMODEM_ACK = 0x06
YMODEM_NAK = 0x15


@dataclass(slots=True)
class ThemeSensorSpec:
    fast_sensor: int
    sensor_type_name: str = ""
    sensor_name: str = ""
    reading_name: str = ""


@dataclass(slots=True)
class ThemeWidgetSpec:
    object_name: str
    widget_type: int
    sensor: ThemeSensorSpec | None = None
