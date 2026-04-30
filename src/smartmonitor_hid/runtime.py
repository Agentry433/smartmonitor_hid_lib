from __future__ import annotations

from pathlib import Path

from .protocol import ThemeWidgetSpec

METRIC_LABELS: dict[str, str] = {
    "CPU_TEMP": "CPU temperature",
    "CPU_PERCENT": "CPU usage",
    "CPU_FREQ_MHZ": "CPU frequency",
    "CPU_FAN": "CPU fan",
    "GPU_TEMP": "GPU temperature",
    "GPU_PERCENT": "GPU usage",
    "GPU_FPS": "GPU FPS",
    "GPU_MEM_PERCENT": "GPU memory %",
    "GPU_MEM_USED_MB": "GPU memory used",
    "GPU_FREQ_MHZ": "GPU frequency",
    "RAM_PERCENT": "RAM usage",
    "RAM_USED_GB": "RAM used",
    "RAM_FREE_GB": "RAM free",
    "RAM_TOTAL_GB": "RAM total",
    "DISK_PERCENT": "Disk activity",
    "DISK_USED_GB": "Disk used",
    "DISK_FREE_GB": "Disk free",
    "DISK_TOTAL_GB": "Disk total",
    "NET_UP_KBPS": "Upload KB/s",
    "NET_DOWN_KBPS": "Download KB/s",
    "SOUND_VOLUME": "Sound volume",
    "UPTIME_HOURS": "Uptime hours",
    "WEATHER_TEMP": "Weather temperature",
    "WEATHER_FEELS_LIKE": "Weather feels like",
    "WEATHER_HUMIDITY": "Weather humidity",
}


def get_runtime_metric_choices() -> list[str]:
    return sorted(METRIC_LABELS.keys())


def get_runtime_metric_label(metric_name: str) -> str:
    return METRIC_LABELS.get(metric_name, metric_name.replace("_", " ").title())


def derive_metric_name(sensor_type_name: str, sensor_name: str, reading_name: str) -> str | None:
    sensor_type = (sensor_type_name or "").strip().lower()
    sensor = (sensor_name or "").strip().lower()
    reading = (reading_name or "").strip().lower()

    if sensor_type == "temperature" and "cpu" in reading:
        return "CPU_TEMP"
    if sensor_type == "temperature" and ("gpu" in reading or "graphics" in reading):
        return "GPU_TEMP"
    if sensor_type == "usage" and "cpu" in reading:
        return "CPU_PERCENT"
    if sensor_type == "usage" and "gpu memory" in reading:
        return "GPU_MEM_PERCENT"
    if sensor_type == "usage" and "gpu" in reading:
        return "GPU_PERCENT"
    if sensor_type == "other" and "fps" in reading:
        return "GPU_FPS"
    if sensor_type == "other" and "physical memory load" in reading:
        return "RAM_PERCENT"
    if sensor_type == "other" and "physical memory used" in reading:
        return "RAM_USED_GB"
    if sensor_type == "other" and "physical memory free" in reading:
        return "RAM_FREE_GB"
    if sensor_type == "other" and "physical memory total" in reading:
        return "RAM_TOTAL_GB"
    if sensor_type == "other" and "disk load" in reading:
        return "DISK_PERCENT"
    if sensor_type == "other" and "disk used" in reading:
        return "DISK_USED_GB"
    if sensor_type == "other" and "disk free" in reading:
        return "DISK_FREE_GB"
    if sensor_type == "other" and "disk total" in reading:
        return "DISK_TOTAL_GB"
    if sensor_type == "other" and "gpu memory used" in reading:
        return "GPU_MEM_USED_MB"
    if sensor_type == "fan" and "cpu" in reading:
        return "CPU_FAN"
    if sensor_type == "frequency" and "core clock" in reading and "gpu" in sensor:
        return "GPU_FREQ_MHZ"
    if sensor_type == "frequency" and "core clock" in reading:
        return "CPU_FREQ_MHZ"
    if sensor_type == "other" and "sound volume" in reading:
        return "SOUND_VOLUME"
    if sensor_type == "other" and "system uptime hours" in reading:
        return "UPTIME_HOURS"
    if sensor_type == "other" and "weather temperature" in reading:
        return "WEATHER_TEMP"
    if sensor_type == "other" and "weather feels like" in reading:
        return "WEATHER_FEELS_LIKE"
    if sensor_type == "other" and "weather humidity" in reading:
        return "WEATHER_HUMIDITY"
    if "network:" in sensor and "current up rate" in reading:
        return "NET_UP_KBPS"
    if "network:" in sensor and "current dl rate" in reading:
        return "NET_DOWN_KBPS"
    return None


def get_theme_runtime_rows(widgets: list[ThemeWidgetSpec], theme_name_or_path: str | Path = "") -> list[dict]:
    _ = theme_name_or_path
    rows: list[dict] = []
    for widget in widgets:
        if widget.sensor is None or widget.sensor.fast_sensor < 0:
            continue
        metric_name = derive_metric_name(
            widget.sensor.sensor_type_name,
            widget.sensor.sensor_name,
            widget.sensor.reading_name,
        )
        rows.append(
            {
                "tag": int(widget.sensor.fast_sensor),
                "metric": metric_name or "",
                "metric_label": get_runtime_metric_label(metric_name) if metric_name else "",
                "sensor_type_name": widget.sensor.sensor_type_name or "",
                "sensor_name": widget.sensor.sensor_name or "",
                "reading_name": widget.sensor.reading_name or "",
                "object_name": widget.object_name or "",
                "widget_type": int(widget.widget_type),
            }
        )
    rows.sort(key=lambda item: (item["tag"], item["object_name"]))
    return rows


def build_tag_mapping(
    widgets: list[ThemeWidgetSpec],
    overrides: dict[str, int] | None = None,
    defaults: dict[str, int] | None = None,
) -> dict[str, int]:
    resolved: dict[str, int] = {}
    if overrides:
        for key, value in overrides.items():
            if value is not None:
                resolved[str(key)] = int(value)

    for widget in widgets:
        if widget.sensor is None or widget.sensor.fast_sensor < 0:
            continue
        metric_name = derive_metric_name(
            widget.sensor.sensor_type_name,
            widget.sensor.sensor_name,
            widget.sensor.reading_name,
        )
        if metric_name:
            resolved.setdefault(metric_name, int(widget.sensor.fast_sensor))

    if defaults:
        for key, value in defaults.items():
            resolved.setdefault(str(key), int(value))
    return resolved
