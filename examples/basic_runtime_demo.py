from pathlib import Path

from smartmonitor_hid import SmartMonitorClient, ThemeSensorSpec, ThemeWidgetSpec


def main():
    client = SmartMonitorClient.auto()

    widgets = [
        ThemeWidgetSpec(
            object_name="cpu_temp",
            widget_type=5,
            sensor=ThemeSensorSpec(
                fast_sensor=1,
                sensor_type_name="Temperature",
                sensor_name="CPU Package",
                reading_name="CPU Temperature",
            ),
        ),
        ThemeWidgetSpec(
            object_name="cpu_usage",
            widget_type=5,
            sensor=ThemeSensorSpec(
                fast_sensor=3,
                sensor_type_name="Usage",
                sensor_name="CPU Total",
                reading_name="CPU Total",
            ),
        ),
    ]

    mapping = client.build_theme_tag_mapping(widgets)
    client.upload_theme(Path("img.dat"))
    client.send_datetime()
    client.send_runtime_metrics(mapping, {"CPU_TEMP": 42, "CPU_PERCENT": 17})


if __name__ == "__main__":
    main()
