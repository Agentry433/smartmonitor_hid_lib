from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Mapping

from .protocol import ThemeWidgetSpec
from .runtime import build_tag_mapping, get_theme_runtime_rows
from .transport import SmartMonitorHidTransport


class SmartMonitorClient:
    """Small high-level wrapper around the standalone HID transport."""

    def __init__(self, transport: SmartMonitorHidTransport):
        self.transport = transport

    @classmethod
    def auto(cls) -> "SmartMonitorClient":
        return cls(SmartMonitorHidTransport.auto())

    def upload_theme(self, theme_path: str | Path, remote_name: str = "img.dat"):
        self.transport.upload_theme(theme_path=theme_path, remote_name=remote_name)

    def close(self):
        self.transport.close()

    def __enter__(self) -> "SmartMonitorClient":
        self.transport.open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def send_datetime(self, when: datetime | None = None):
        self.transport.send_datetime(when=when)

    def build_theme_tag_mapping(
        self,
        widgets: list[ThemeWidgetSpec],
        overrides: dict[str, int] | None = None,
        defaults: dict[str, int] | None = None,
    ) -> dict[str, int]:
        return build_tag_mapping(widgets, overrides=overrides, defaults=defaults)

    def describe_theme_widgets(self, widgets: list[ThemeWidgetSpec]) -> list[dict]:
        return get_theme_runtime_rows(widgets)

    def send_runtime_metrics(
        self,
        tag_mapping: Mapping[str, int],
        metric_values: Mapping[str, int | float],
        command: int = 0x02,
    ) -> list[tuple[int, int]]:
        pairs: list[tuple[int, int]] = []
        for metric_name, tag in tag_mapping.items():
            if metric_name not in metric_values:
                continue
            value = int(round(float(metric_values[metric_name])))
            value = max(0, min(0xFFFF, value))
            pairs.append((int(tag), value))
        if pairs:
            self.transport.send_runtime_pairs(command=command, pairs=pairs)
        return pairs
