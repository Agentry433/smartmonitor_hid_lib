"""Standalone SmartMonitor HID prototype package."""

from ._bridge import configure_project_root, get_project_root
from .client import SmartMonitorClient
from .compiler import ThemeCompiler, compile_theme_bundle, compile_theme_file
from .edit import (
    add_widget,
    clear_widget_sensor,
    clone_widget,
    duplicate_widget,
    find_widget,
    move_widget,
    next_widget_ids,
    remove_widget,
    set_widget_datetime_format,
    set_widget_geometry,
    set_widget_sensor,
)
from .errors import (
    SmartMonitorBridgeError,
    SmartMonitorCompilerError,
    SmartMonitorError,
    SmartMonitorTransportError,
)
from .imgdat import parse_imgdat, parse_imgdat_file, pack_record_fields, resource_payload_size
from .protocol import ThemeSensorSpec, ThemeWidgetSpec
from .report import (
    ThemeCompileReport,
    ThemeDescription,
    ThemeValidationReport,
    ValidationIssue,
    compile_report,
    describe_theme_bundle,
    list_runtime_tags,
    list_supported_metrics,
    validate_theme_bundle,
)
from .render import render_datetime_preview_payload, render_number_glyph_payload, render_static_text_payload
from .runtime import (
    METRIC_LABELS,
    build_tag_mapping,
    get_runtime_metric_label,
    get_runtime_metric_choices,
    get_theme_runtime_rows,
)
from .service import RuntimeServiceConfig, RuntimeServiceStats, SmartMonitorRuntimeService
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
    "ThemeCompileReport",
    "ThemeBundle",
    "ThemeCompiler",
    "ThemeDescription",
    "ThemeSensorSpec",
    "ThemeValidationReport",
    "ThemeWidgetSpec",
    "ValidationIssue",
    "RuntimeServiceConfig",
    "RuntimeServiceStats",
    "SmartMonitorRuntimeService",
    "add_widget",
    "build_tag_mapping",
    "clear_widget_sensor",
    "clone_widget",
    "compile_theme_bundle",
    "compile_theme_file",
    "compile_report",
    "configure_project_root",
    "decode_ui_bytes",
    "decode_ui_file",
    "describe_theme_bundle",
    "encode_ui_bytes",
    "encode_ui_file",
    "find_widget",
    "get_project_root",
    "get_runtime_metric_choices",
    "get_runtime_metric_label",
    "get_theme_runtime_rows",
    "list_runtime_tags",
    "list_supported_metrics",
    "move_widget",
    "next_widget_ids",
    "pack_record_fields",
    "parse_imgdat",
    "parse_imgdat_file",
    "parse_theme_bundle",
    "remove_widget",
    "render_datetime_preview_payload",
    "render_number_glyph_payload",
    "render_static_text_payload",
    "resource_payload_size",
    "set_widget_datetime_format",
    "set_widget_geometry",
    "set_widget_sensor",
    "validate_theme_bundle",
    "write_theme_file",
]
