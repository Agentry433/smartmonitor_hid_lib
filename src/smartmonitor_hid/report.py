from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .compiler import compile_theme_bundle
from .imgdat import parse_imgdat
from .protocol import ThemeSensorSpec, ThemeWidgetSpec
from .runtime import get_theme_runtime_rows
from .theme import ThemeBundle, Widget
from .ui import SMARTMONITOR_WIDGET_TYPE_NAMES


SUPPORTED_WIDGET_TYPES = {1, 2, 3, 4, 5, 6}


@dataclass(slots=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
    object_name: str = ""
    widget_type: int = -1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ThemeDescription:
    ui_path: str
    base_dir: str
    widget_count: int
    widget_counts_by_type: dict[str, int]
    runtime_widget_count: int
    datetime_widget_count: int
    startup_configured: bool
    image_dependencies: list[str]
    supported_metrics: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ThemeValidationReport:
    ok: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": [item.to_dict() for item in self.errors],
            "warnings": [item.to_dict() for item in self.warnings],
        }


@dataclass(slots=True)
class ThemeCompileReport:
    success: bool
    compiled_size: int
    resource_bytes_estimate: int
    record_counts_by_type: dict[str, int]
    supported_widget_count: int
    skipped_widget_count: int
    skipped_widgets: list[str]
    validation: ThemeValidationReport
    description: ThemeDescription

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "compiled_size": self.compiled_size,
            "resource_bytes_estimate": self.resource_bytes_estimate,
            "record_counts_by_type": dict(self.record_counts_by_type),
            "supported_widget_count": self.supported_widget_count,
            "skipped_widget_count": self.skipped_widget_count,
            "skipped_widgets": list(self.skipped_widgets),
            "validation": self.validation.to_dict(),
            "description": self.description.to_dict(),
        }


def _widget_to_runtime_spec(widget: Widget) -> ThemeWidgetSpec:
    return ThemeWidgetSpec(
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


def list_runtime_tags(bundle: ThemeBundle) -> list[dict[str, Any]]:
    return get_theme_runtime_rows([_widget_to_runtime_spec(widget) for widget in bundle.theme.widgets], bundle.ui_path)


def list_supported_metrics(bundle: ThemeBundle) -> list[str]:
    metrics = sorted({row["metric"] for row in list_runtime_tags(bundle) if row.get("metric")})
    return metrics


def _widget_image_dependencies(widget: Widget) -> list[str]:
    paths: list[str] = []
    image_path = str(widget.raw_fields.get("imagePath", "")).strip()
    if image_path:
        paths.append(image_path)
    if widget.style is not None:
        if widget.style.bg_image_path:
            paths.append(widget.style.bg_image_path)
        if widget.style.fg_image_path:
            paths.append(widget.style.fg_image_path)
    return paths


def describe_theme_bundle(bundle: ThemeBundle) -> ThemeDescription:
    type_counts = Counter(
        SMARTMONITOR_WIDGET_TYPE_NAMES.get(widget.widget_type, f"unknown_{widget.widget_type}")
        for widget in bundle.theme.widgets
    )
    image_dependencies: list[str] = []
    for parent in bundle.theme.widget_parents:
        if parent.background_image_path:
            image_dependencies.append(parent.background_image_path)
    for widget in bundle.theme.widgets:
        image_dependencies.extend(_widget_image_dependencies(widget))
    deduped_dependencies = sorted({item for item in image_dependencies if item})
    return ThemeDescription(
        ui_path=bundle.ui_path,
        base_dir=bundle.base_dir,
        widget_count=len(bundle.theme.widgets),
        widget_counts_by_type=dict(sorted(type_counts.items())),
        runtime_widget_count=len(list_runtime_tags(bundle)),
        datetime_widget_count=sum(1 for widget in bundle.theme.widgets if widget.widget_type == 6),
        startup_configured=bool(bundle.startup_pic and bundle.startup_pic.path),
        image_dependencies=deduped_dependencies,
        supported_metrics=list_supported_metrics(bundle),
    )


def validate_theme_bundle(bundle: ThemeBundle) -> ThemeValidationReport:
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    base_dir = Path(bundle.base_dir)

    for widget in bundle.theme.widgets:
        if widget.widget_type not in SUPPORTED_WIDGET_TYPES:
            warnings.append(
                ValidationIssue(
                    severity="warning",
                    code="unsupported_widget_type",
                    message=f"Widget type {widget.widget_type} is not currently supported by the compiler",
                    object_name=widget.object_name,
                    widget_type=widget.widget_type,
                )
            )

        if widget.geometry.width <= 0 or widget.geometry.height <= 0:
            errors.append(
                ValidationIssue(
                    severity="error",
                    code="invalid_geometry",
                    message="Widget geometry must have positive width and height",
                    object_name=widget.object_name,
                    widget_type=widget.widget_type,
                )
            )

        if widget.widget_type in {3, 5}:
            if widget.sensor is None or widget.sensor.fast_sensor < 0:
                warnings.append(
                    ValidationIssue(
                        severity="warning",
                        code="missing_sensor_mapping",
                        message="Runtime-capable widget does not define a valid sensor/tag mapping",
                        object_name=widget.object_name,
                        widget_type=widget.widget_type,
                    )
                )

        if widget.widget_type == 6 and not (widget.datetime_format or "").strip():
            warnings.append(
                ValidationIssue(
                    severity="warning",
                    code="empty_datetime_format",
                    message="DateTime widget does not define a format string",
                    object_name=widget.object_name,
                    widget_type=widget.widget_type,
                )
            )

        for raw_path in _widget_image_dependencies(widget):
            candidate = base_dir / raw_path
            if not candidate.is_file():
                errors.append(
                    ValidationIssue(
                        severity="error",
                        code="missing_widget_asset",
                        message=f"Referenced widget asset is missing: {raw_path}",
                        object_name=widget.object_name,
                        widget_type=widget.widget_type,
                    )
                )

    for parent in bundle.theme.widget_parents:
        if parent.geometry.width <= 0 or parent.geometry.height <= 0:
            errors.append(
                ValidationIssue(
                    severity="error",
                    code="invalid_parent_geometry",
                    message="Widget parent geometry must have positive width and height",
                    object_name=parent.object_name,
                    widget_type=parent.widget_type,
                )
            )
        if parent.background_image_path:
            candidate = base_dir / parent.background_image_path
            if not candidate.is_file():
                errors.append(
                    ValidationIssue(
                        severity="error",
                        code="missing_background_asset",
                        message=f"Referenced background asset is missing: {parent.background_image_path}",
                        object_name=parent.object_name,
                        widget_type=parent.widget_type,
                    )
                )

    if bundle.startup_pic is not None and bundle.startup_pic.path:
        candidate = base_dir / bundle.startup_pic.path
        if not candidate.is_file():
            errors.append(
                ValidationIssue(
                    severity="error",
                    code="missing_startup_asset",
                    message=f"Referenced startup asset is missing: {bundle.startup_pic.path}",
                )
            )

    return ThemeValidationReport(ok=not errors, errors=errors, warnings=warnings)


def compile_report(bundle: ThemeBundle) -> ThemeCompileReport:
    validation = validate_theme_bundle(bundle)
    payload = compile_theme_bundle(bundle)
    parsed = parse_imgdat(payload, path=bundle.ui_path)
    record_counts = Counter(record.record_type_name for record in parsed.records)
    supported_widgets = [widget for widget in bundle.theme.widgets if widget.widget_type in SUPPORTED_WIDGET_TYPES]
    skipped_widgets = [
        widget.object_name or f"id={widget.global_id}"
        for widget in bundle.theme.widgets
        if widget.widget_type not in SUPPORTED_WIDGET_TYPES
    ]
    resource_start = max((record.offset for record in parsed.records), default=0) + 64 if parsed.records else 0
    resource_bytes_estimate = max(0, len(payload) - resource_start)
    return ThemeCompileReport(
        success=True,
        compiled_size=len(payload),
        resource_bytes_estimate=resource_bytes_estimate,
        record_counts_by_type=dict(sorted(record_counts.items())),
        supported_widget_count=len(supported_widgets),
        skipped_widget_count=len(skipped_widgets),
        skipped_widgets=skipped_widgets,
        validation=validation,
        description=describe_theme_bundle(bundle),
    )
