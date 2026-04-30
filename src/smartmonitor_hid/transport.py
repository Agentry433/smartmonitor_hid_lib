from __future__ import annotations

import glob
import logging
import os
import select
import threading
import time
from datetime import datetime
from pathlib import Path

from .protocol import (
    HID_REPORT_SIZE,
    SMARTMONITOR_RESET_COMMAND,
    SMARTMONITOR_TIME_COMMAND,
    SMARTMONITOR_YMODEM_COMMAND,
    USB_PRODUCT_ID,
    USB_VENDOR_ID,
    YMODEM_ACK,
    YMODEM_EOT,
    YMODEM_NAK,
    YMODEM_SOH,
    YMODEM_STX,
)
from .errors import SmartMonitorTransportError

logger = logging.getLogger(__name__)


class SmartMonitorHidTransport:
    def __init__(self, device_path: str = "AUTO"):
        self.requested_device_path = device_path
        self.device_path = device_path
        self.fd: int | None = None
        self._io_lock = threading.Lock()

    @staticmethod
    def _uevent_to_dict(uevent_path: str) -> dict[str, str]:
        data: dict[str, str] = {}
        with open(uevent_path, "rt", encoding="utf-8") as stream:
            for line in stream:
                if "=" not in line:
                    continue
                key, value = line.strip().split("=", 1)
                data[key] = value
        return data

    @classmethod
    def auto_detect_path(cls) -> str | None:
        target = f"0003:{USB_VENDOR_ID}:{USB_PRODUCT_ID}"
        for uevent_path in glob.glob("/sys/class/hidraw/hidraw*/device/uevent"):
            try:
                data = cls._uevent_to_dict(uevent_path)
            except OSError:
                continue
            if data.get("HID_ID", "").upper() != target:
                continue
            hidraw_name = Path(uevent_path).parents[1].name
            return f"/dev/{hidraw_name}"
        return None

    @classmethod
    def auto(cls) -> "SmartMonitorHidTransport":
        instance = cls(device_path="AUTO")
        instance.open()
        return instance

    def open(self):
        if self.fd is not None:
            return
        last_error = None
        for _ in range(10):
            candidate = self.requested_device_path
            if candidate == "AUTO":
                candidate = self.device_path if self.device_path != "AUTO" and Path(self.device_path).exists() else None
                if candidate is None:
                    candidate = self.auto_detect_path()
            if not candidate:
                last_error = FileNotFoundError("SmartMonitor hidraw device is not visible yet")
                time.sleep(0.5)
                continue
            self.device_path = candidate
            try:
                self.fd = os.open(candidate, os.O_RDWR | os.O_NONBLOCK)
                return
            except OSError as exc:
                last_error = exc
                self.fd = None
                time.sleep(0.5)
        raise SmartMonitorTransportError("Unable to open SmartMonitor HID device") from last_error

    def close(self):
        if self.fd is None:
            return
        try:
            os.close(self.fd)
        finally:
            self.fd = None

    def __enter__(self) -> "SmartMonitorHidTransport":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def reopen(self, wait_after_close: float = 1.0, flush_input: bool = True):
        self.close()
        time.sleep(wait_after_close)
        self.open()
        if flush_input:
            self.flush_input()

    def recover(self, attempts: int = 3, wait_after_close: float = 1.0, flush_input: bool = True):
        last_error = None
        for _ in range(attempts):
            try:
                self.reopen(wait_after_close=wait_after_close, flush_input=flush_input)
                return
            except OSError as exc:
                last_error = exc
                time.sleep(wait_after_close)
        if last_error is not None:
            raise SmartMonitorTransportError("Failed to recover SmartMonitor HID device") from last_error

    @staticmethod
    def _crc16_xmodem(payload: bytes) -> int:
        crc = 0
        for byte in payload:
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ 0x1021) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
        return crc

    def _serial_write(self, data: bytes):
        assert self.fd is not None
        offset = 0
        while offset < len(data):
            payload = data[offset: offset + HID_REPORT_SIZE]
            report = bytes([0]) + payload.ljust(HID_REPORT_SIZE, b"\x00")
            os.write(self.fd, report)
            offset += len(payload)

    def write_report(self, payload: bytes):
        if len(payload) > HID_REPORT_SIZE:
            raise ValueError(f"HID payload too large: {len(payload)} > {HID_REPORT_SIZE}")
        with self._io_lock:
            if self.fd is None:
                self.open()
            self._serial_write(payload)

    def read_report(self, timeout: float = 1.0) -> bytes:
        with self._io_lock:
            if self.fd is None:
                self.open()
            ready, _, _ = select.select([self.fd], [], [], timeout)
            if not ready:
                return b""
            report = os.read(self.fd, HID_REPORT_SIZE + 1)
            if not report:
                return b""
            if len(report) == HID_REPORT_SIZE + 1 and report[0] == 0:
                report = report[1:]
            return report

    def read_all(self) -> bytes:
        assert self.fd is not None
        chunks: list[bytes] = []
        while True:
            ready, _, _ = select.select([self.fd], [], [], 0)
            if not ready:
                break
            report = os.read(self.fd, HID_REPORT_SIZE + 1)
            if not report:
                break
            if len(report) == HID_REPORT_SIZE + 1 and report[0] == 0:
                report = report[1:]
            chunks.append(report)
        return b"".join(chunks)

    def flush_input(self):
        if self.fd is None:
            return
        self.read_all()

    def _expect_ack_report(self, timeout: float = 2.0) -> bytes:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            report = self.read_report(timeout=max(0.0, deadline - time.monotonic()))
            if not report:
                continue
            if report[0] in (YMODEM_ACK, YMODEM_NAK):
                return report
            logger.debug("Ignoring non-ACK HID report during SmartMonitor upload: %s", report.hex())
        raise SmartMonitorTransportError("Timed out waiting for ACK from SmartMonitor")

    @classmethod
    def _build_ymodem_frame(cls, block_type: int, block_number: int, payload: bytes) -> bytes:
        frame = bytes([block_type, block_number & 0xFF, 0xFF - (block_number & 0xFF)]) + payload
        crc = cls._crc16_xmodem(payload)
        return frame + crc.to_bytes(2, "big")

    def _send_ymodem_frame(self, frame: bytes, timeout: float = 2.0, max_retries: int = 8) -> bytes:
        last_report = b""
        for attempt in range(1, max_retries + 1):
            self._serial_write(frame)
            report = self._expect_ack_report(timeout=timeout)
            last_report = report
            if report[0] == YMODEM_ACK:
                return report
            if report[0] == YMODEM_NAK:
                logger.warning("SmartMonitor NAKed YMODEM frame on attempt %d/%d", attempt, max_retries)
                continue
        raise SmartMonitorTransportError(
            f"SmartMonitor kept NAKing YMODEM frame after {max_retries} retries: {last_report.hex()}"
        )

    def send_reset(self, reconnect_delay: float = 2.5):
        self.write_report(SMARTMONITOR_RESET_COMMAND)
        time.sleep(reconnect_delay)
        self.recover(attempts=5, wait_after_close=0.5)

    def enter_ymodem(self, timeout: float = 2.0, attempts: int = 3) -> bytes:
        last_exc = None
        per_attempt_timeout = max(1.0, timeout / max(1, attempts))
        for attempt in range(1, attempts + 1):
            self.flush_input()
            self.write_report(SMARTMONITOR_YMODEM_COMMAND)
            try:
                return self._expect_ack_report(timeout=per_attempt_timeout)
            except Exception as exc:
                last_exc = exc
                if attempt < attempts:
                    time.sleep(0.3)
        if last_exc is not None:
            raise last_exc
        raise SmartMonitorTransportError("Timed out waiting for YMODEM entry ACK from SmartMonitor")

    def upload_theme(self, theme_path: str | Path, remote_name: str = "img.dat", send_reset: bool = True, ack_timeout: float = 2.0):
        theme_path = Path(theme_path)
        if self.fd is None:
            self.open()
        else:
            self.recover(attempts=5, wait_after_close=0.5)

        reset_delays = [2.5, 3.5, 4.5] if send_reset else [0.0]
        last_exc = None
        ack_report = None
        for attempt_index, reset_delay in enumerate(reset_delays, start=1):
            try:
                if send_reset:
                    self.send_reset(reconnect_delay=reset_delay)
                else:
                    self.recover(attempts=3, wait_after_close=0.5)
                ack_report = self.enter_ymodem(timeout=max(ack_timeout, 3.0), attempts=3)
                break
            except Exception as exc:
                last_exc = exc
                if attempt_index < len(reset_delays):
                    self.recover(attempts=5, wait_after_close=1.0)
                    continue
                raise
        if ack_report is None:
            raise SmartMonitorTransportError("SmartMonitor did not acknowledge YMODEM entry") from last_exc

        theme_data = theme_path.read_bytes()

        header_payload = bytearray(128)
        header = f"{remote_name}\0{len(theme_data)}\0".encode("ascii")
        header_payload[:len(header)] = header
        self._send_ymodem_frame(
            self._build_ymodem_frame(YMODEM_SOH, 0, bytes(header_payload)),
            timeout=ack_timeout,
        )

        total_blocks = max(1, (len(theme_data) + 1023) // 1024)
        for block_index in range(total_blocks):
            start = block_index * 1024
            chunk = theme_data[start:start + 1024].ljust(1024, b"\x1A")
            block_number = (block_index + 1) & 0xFF
            self._send_ymodem_frame(
                self._build_ymodem_frame(YMODEM_STX, block_number, chunk),
                timeout=ack_timeout,
            )

        self.write_report(bytes([YMODEM_EOT]))
        self._expect_ack_report(timeout=ack_timeout)
        self._send_ymodem_frame(
            self._build_ymodem_frame(YMODEM_SOH, 0, bytes(128)),
            timeout=ack_timeout,
        )
        self.recover(attempts=6, wait_after_close=1.0)

    def send_runtime_pairs(self, command: int, pairs: list[tuple[int, int]]):
        if not 0 <= command <= 0xFF:
            raise ValueError(f"Command must fit in one byte, got {command}")
        if len(pairs) > 20:
            raise ValueError(f"SmartMonitor packets support at most 20 pairs, got {len(pairs)}")
        payload = bytearray(HID_REPORT_SIZE)
        payload[0] = command & 0xFF
        payload[1] = len(pairs) & 0xFF
        offset = 2
        for tag, value in pairs:
            if not 0 <= tag <= 0xFF:
                raise ValueError(f"Tag must fit in one byte, got {tag}")
            if not 0 <= value <= 0xFFFF:
                raise ValueError(f"Value must fit in two bytes, got {value}")
            payload[offset] = tag & 0xFF
            payload[offset + 1:offset + 3] = value.to_bytes(2, "big")
            offset += 3
        self.write_report(bytes(payload))

    def send_datetime(self, when: datetime | None = None):
        if when is None:
            when = datetime.now()
        payload = bytearray(HID_REPORT_SIZE)
        payload[0] = SMARTMONITOR_TIME_COMMAND
        payload[1] = 0x01
        payload[2] = 0x15
        payload[3] = when.year - 2000
        payload[4] = when.month
        payload[5] = when.day
        payload[6] = when.hour
        payload[7] = when.minute
        payload[8] = when.second
        payload[9] = when.isoweekday()
        payload[10] = 0x64
        self.write_report(bytes(payload))
