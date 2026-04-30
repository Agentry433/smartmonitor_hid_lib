from __future__ import annotations

import unittest

from smartmonitor_hid.protocol import ThemeSensorSpec, ThemeWidgetSpec
from smartmonitor_hid.runtime import build_tag_mapping, derive_metric_name, get_theme_runtime_rows


class RuntimeMappingTests(unittest.TestCase):
    def test_derive_metric_name_for_common_metrics(self):
        self.assertEqual(
            derive_metric_name("Temperature", "CPU Package", "CPU Temperature"),
            "CPU_TEMP",
        )
        self.assertEqual(
            derive_metric_name("Usage", "GPU Core", "GPU Usage"),
            "GPU_PERCENT",
        )
        self.assertEqual(
            derive_metric_name("Other", "Memory", "Physical Memory Load"),
            "RAM_PERCENT",
        )
        self.assertEqual(
            derive_metric_name("Other", "Network: eth0", "Current UP rate"),
            "NET_UP_KBPS",
        )

    def test_build_tag_mapping_respects_overrides_then_theme_then_defaults(self):
        widgets = [
            ThemeWidgetSpec(
                object_name="cpu_temp_widget",
                widget_type=1,
                sensor=ThemeSensorSpec(
                    fast_sensor=1,
                    sensor_type_name="Temperature",
                    sensor_name="CPU Package",
                    reading_name="CPU Temperature",
                ),
            ),
            ThemeWidgetSpec(
                object_name="cpu_usage_widget",
                widget_type=1,
                sensor=ThemeSensorSpec(
                    fast_sensor=3,
                    sensor_type_name="Usage",
                    sensor_name="CPU Total",
                    reading_name="CPU Usage",
                ),
            ),
        ]

        mapping = build_tag_mapping(
            widgets,
            overrides={"CPU_PERCENT": 99},
            defaults={"GPU_TEMP": 5, "CPU_TEMP": 77},
        )

        self.assertEqual(mapping["CPU_PERCENT"], 99)
        self.assertEqual(mapping["CPU_TEMP"], 1)
        self.assertEqual(mapping["GPU_TEMP"], 5)

    def test_get_theme_runtime_rows_sorts_by_tag_then_name(self):
        widgets = [
            ThemeWidgetSpec(
                object_name="z_cpu",
                widget_type=1,
                sensor=ThemeSensorSpec(
                    fast_sensor=3,
                    sensor_type_name="Usage",
                    sensor_name="CPU Total",
                    reading_name="CPU Usage",
                ),
            ),
            ThemeWidgetSpec(
                object_name="a_cpu_temp",
                widget_type=1,
                sensor=ThemeSensorSpec(
                    fast_sensor=1,
                    sensor_type_name="Temperature",
                    sensor_name="CPU Package",
                    reading_name="CPU Temperature",
                ),
            ),
        ]

        rows = get_theme_runtime_rows(widgets)

        self.assertEqual([row["tag"] for row in rows], [1, 3])
        self.assertEqual(rows[0]["metric"], "CPU_TEMP")
        self.assertEqual(rows[1]["metric"], "CPU_PERCENT")


if __name__ == "__main__":
    unittest.main()
