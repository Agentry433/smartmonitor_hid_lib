from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from smartmonitor_hid.report import compile_report, describe_theme_bundle, list_runtime_tags, list_supported_metrics, validate_theme_bundle
from smartmonitor_hid.theme import FontSpec, Geometry, SensorSpec, Theme, ThemeBundle, Widget, WidgetParent


class ReportApiTests(unittest.TestCase):
    def _build_bundle(self, base_dir: str = ".") -> ThemeBundle:
        return ThemeBundle(
            ui_path="report.ui",
            base_dir=base_dir,
            theme=Theme(
                path="report.ui",
                widget_parents=[
                    WidgetParent(
                        object_name="Background",
                        widget_type=1,
                        geometry=Geometry(x=0, y=0, width=480, height=320),
                        background_type=1,
                        background_color_raw="0xff000000",
                        background_color=0xFF000000,
                    )
                ],
                widgets=[
                    Widget(
                        global_id=1,
                        same_type_id=1,
                        parent_name="Background",
                        object_name="cpu_text",
                        widget_type=2,
                        geometry=Geometry(x=10, y=20, width=120, height=24),
                        font=FontSpec(text="CPU", name="Sans", color_raw="0xffffffff", color=0xFFFFFFFF, size=14),
                    ),
                    Widget(
                        global_id=2,
                        same_type_id=1,
                        parent_name="Background",
                        object_name="cpu_temp",
                        widget_type=5,
                        geometry=Geometry(x=10, y=60, width=100, height=24),
                        font=FontSpec(text="42", name="Sans", color_raw="0xffffffff", color=0xFFFFFFFF, size=14),
                        sensor=SensorSpec(
                            fast_sensor=1,
                            sensor_type_name="Temperature",
                            sensor_name="CPU Package",
                            reading_name="CPU Temperature",
                        ),
                    ),
                    Widget(
                        global_id=3,
                        same_type_id=1,
                        parent_name="Background",
                        object_name="clock",
                        widget_type=6,
                        geometry=Geometry(x=10, y=100, width=140, height=28),
                        font=FontSpec(text="", name="Sans", color_raw="0xffffffff", color=0xFFFFFFFF, size=14),
                        datetime_format="HH:mm:ss",
                    ),
                    Widget(
                        global_id=4,
                        same_type_id=1,
                        parent_name="Background",
                        object_name="mystery",
                        widget_type=77,
                        geometry=Geometry(x=10, y=140, width=20, height=20),
                    ),
                ],
            ),
        )

    def test_describe_theme_bundle(self):
        bundle = self._build_bundle()
        description = describe_theme_bundle(bundle)
        self.assertEqual(description.widget_count, 4)
        self.assertEqual(description.runtime_widget_count, 1)
        self.assertEqual(description.datetime_widget_count, 1)
        self.assertIn("CPU_TEMP", description.supported_metrics)

    def test_list_runtime_tags_and_metrics(self):
        bundle = self._build_bundle()
        rows = list_runtime_tags(bundle)
        metrics = list_supported_metrics(bundle)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["metric"], "CPU_TEMP")
        self.assertEqual(metrics, ["CPU_TEMP"])

    def test_validate_theme_bundle_reports_warnings(self):
        bundle = self._build_bundle()
        report = validate_theme_bundle(bundle)
        self.assertTrue(report.ok)
        warning_codes = {item.code for item in report.warnings}
        self.assertIn("unsupported_widget_type", warning_codes)

    def test_validate_theme_bundle_reports_missing_assets_as_errors(self):
        with TemporaryDirectory() as temp_dir:
            bundle = self._build_bundle(base_dir=temp_dir)
            bundle.theme.widget_parents[0].background_image_path = "missing.png"
            report = validate_theme_bundle(bundle)
        self.assertFalse(report.ok)
        error_codes = {item.code for item in report.errors}
        self.assertIn("missing_background_asset", error_codes)

    def test_compile_report_returns_structured_summary(self):
        bundle = self._build_bundle()
        report = compile_report(bundle)
        self.assertTrue(report.success)
        self.assertGreater(report.compiled_size, 0)
        self.assertIn("datetime_widget", report.record_counts_by_type)
        self.assertEqual(report.skipped_widget_count, 1)


if __name__ == "__main__":
    unittest.main()
