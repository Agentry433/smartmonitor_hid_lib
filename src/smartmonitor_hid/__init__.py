"""Standalone SmartMonitor HID prototype package."""

from ._bridge import configure_project_root, get_project_root
from .client import SmartMonitorClient
from .compiler import ThemeCompiler, compile_theme_bundle, compile_theme_file
from .errors import (
    SmartMonitorBridgeError,
    SmartMonitorCompilerError,
    SmartMonitorError,
    SmartMonitorTransportError,
)
from .imgdat import parse_imgdat, parse_imgdat_file, pack_record_fields, resource_payload_size
from .protocol import ThemeSensorSpec, ThemeWidgetSpec
from .render import render_datetime_preview_payload, render_number_glyph_payload, render_static_text_payload
from .runtime import (
    METRIC_LABELS,
    build_tag_mapping,
    get_runtime_metric_label,
    get_runtime_metric_choices,
    get_theme_runtime_rows,
)
from .theme import ImgDatRecord, ImgDatTheme, ThemeBundle
from .transport import SmartMonitorHidTransport
from .ui import decode_ui_bytes, decode_ui_file, encode_ui_bytes, encode_ui_file, parse_theme_bundle, write_theme_file

__all__ = [
    "METRIC_LABELS",
    "ImgDatRecord",
    "ImgDatTheme",
    "SmartMonitorBridgeError",
    "SmartMonitorClient",
    "SmartMonitorCompilerError",
    "SmartMonitorError",
    "SmartMonitorHidTransport",
    "SmartMonitorTransportError",
    "ThemeBundle",
    "ThemeCompiler",
    "ThemeSensorSpec",
    "ThemeWidgetSpec",
    "build_tag_mapping",
    "compile_theme_bundle",
    "compile_theme_file",
    "configure_project_root",
    "decode_ui_bytes",
    "decode_ui_file",
    "encode_ui_bytes",
    "encode_ui_file",
    "get_project_root",
    "get_runtime_metric_choices",
    "get_runtime_metric_label",
    "get_theme_runtime_rows",
    "pack_record_fields",
    "parse_imgdat",
    "parse_imgdat_file",
    "parse_theme_bundle",
    "render_datetime_preview_payload",
    "render_number_glyph_payload",
    "render_static_text_payload",
    "resource_payload_size",
    "write_theme_file",
]
