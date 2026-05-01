from __future__ import annotations

import argparse
import json
from pathlib import Path

from ._bridge import configure_project_root
from .client import SmartMonitorClient
from .compiler import ThemeCompiler
from .imgdat import parse_imgdat_file
from .protocol import ThemeSensorSpec, ThemeWidgetSpec
from .report import compile_report, describe_theme_bundle, list_supported_metrics, validate_theme_bundle
from .runtime import build_tag_mapping, get_theme_runtime_rows
from .transport import SmartMonitorHidTransport
from .ui import parse_theme_bundle


def _cmd_detect(_args: argparse.Namespace) -> int:
    path = SmartMonitorHidTransport.auto_detect_path()
    if path:
        print(path)
        return 0
    print("SmartMonitor HID device not detected")
    return 1


def _cmd_upload(args: argparse.Namespace) -> int:
    client = SmartMonitorClient.auto()
    client.upload_theme(Path(args.theme), remote_name=args.remote_name)
    print(f"Uploaded: {args.theme}")
    return 0


def _cmd_send_time(_args: argparse.Namespace) -> int:
    client = SmartMonitorClient.auto()
    client.send_datetime()
    print("Sent current date/time")
    return 0


def _cmd_inspect_ui(args: argparse.Namespace) -> int:
    bundle = parse_theme_bundle(args.ui)
    payload = bundle.to_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _cmd_inspect_imgdat(args: argparse.Namespace) -> int:
    parsed = parse_imgdat_file(args.imgdat)
    payload = parsed.to_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _cmd_compile(args: argparse.Namespace) -> int:
    compiler = ThemeCompiler()
    output = Path(args.output)
    compiler.compile_ui_to_file(args.ui, output)
    print(f"Wrote: {output}")
    return 0


def _cmd_map_ui(args: argparse.Namespace) -> int:
    bundle = parse_theme_bundle(args.ui)
    rows = get_theme_runtime_rows(
        [
            ThemeWidgetSpec(
                object_name=widget.object_name,
                widget_type=widget.widget_type,
                sensor=(
                    None
                    if widget.sensor is None
                    else ThemeSensorSpec(
                        fast_sensor=widget.sensor.fast_sensor,
                        sensor_type_name=widget.sensor.sensor_type_name,
                        sensor_name=widget.sensor.sensor_name,
                        reading_name=widget.sensor.reading_name,
                    )
                ),
            )
            for widget in bundle.theme.widgets
        ]
    )
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def _cmd_describe_ui(args: argparse.Namespace) -> int:
    bundle = parse_theme_bundle(args.ui)
    print(json.dumps(describe_theme_bundle(bundle).to_dict(), ensure_ascii=False, indent=2))
    return 0


def _cmd_validate_ui(args: argparse.Namespace) -> int:
    bundle = parse_theme_bundle(args.ui)
    report = validate_theme_bundle(bundle)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0 if report.ok else 1


def _cmd_compile_report(args: argparse.Namespace) -> int:
    bundle = parse_theme_bundle(args.ui)
    print(json.dumps(compile_report(bundle).to_dict(), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="smartmonitor-hid")
    parser.add_argument(
        "--project-root",
        help="Path to the surrounding project root that contains the reverse-engineered bridge modules",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect = subparsers.add_parser("detect", help="Auto-detect HID device path")
    detect.set_defaults(func=_cmd_detect)

    upload = subparsers.add_parser("upload-theme", help="Upload img.dat/theme file to the monitor")
    upload.add_argument("theme", help="Path to img.dat or .dat file")
    upload.add_argument("--remote-name", default="img.dat", help="Remote file name on the device")
    upload.set_defaults(func=_cmd_upload)

    send_time = subparsers.add_parser("send-time", help="Send current date/time packet")
    send_time.set_defaults(func=_cmd_send_time)

    inspect_ui = subparsers.add_parser("inspect-ui", help="Parse and print a vendor .ui file")
    inspect_ui.add_argument("ui", help="Path to .ui file")
    inspect_ui.set_defaults(func=_cmd_inspect_ui)

    inspect_imgdat = subparsers.add_parser("inspect-imgdat", help="Parse and print an img.dat file")
    inspect_imgdat.add_argument("imgdat", help="Path to img.dat/.dat file")
    inspect_imgdat.set_defaults(func=_cmd_inspect_imgdat)

    compile_ui = subparsers.add_parser("compile-ui", help="Compile .ui into img.dat")
    compile_ui.add_argument("ui", help="Path to .ui file")
    compile_ui.add_argument("output", help="Output img.dat path")
    compile_ui.set_defaults(func=_cmd_compile)

    map_ui = subparsers.add_parser("map-ui", help="Show runtime tag mapping rows for a .ui theme")
    map_ui.add_argument("ui", help="Path to .ui file")
    map_ui.set_defaults(func=_cmd_map_ui)

    describe_ui = subparsers.add_parser("describe-ui", help="Show a structured summary for a .ui theme")
    describe_ui.add_argument("ui", help="Path to .ui file")
    describe_ui.set_defaults(func=_cmd_describe_ui)

    validate_ui = subparsers.add_parser("validate-ui", help="Validate a .ui theme and report warnings/errors")
    validate_ui.add_argument("ui", help="Path to .ui file")
    validate_ui.set_defaults(func=_cmd_validate_ui)

    compile_report_ui = subparsers.add_parser("compile-report", help="Compile a .ui theme and show a structured report")
    compile_report_ui.add_argument("ui", help="Path to .ui file")
    compile_report_ui.set_defaults(func=_cmd_compile_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "project_root", None):
        configure_project_root(args.project_root)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
