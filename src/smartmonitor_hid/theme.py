from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Geometry:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


@dataclass(slots=True)
class FontSpec:
    text: str = ""
    name: str = ""
    color_raw: str = ""
    color: int = 0
    size: int = 0
    bold_value: int = 0
    italic_value: int = 0
    bold: bool = False
    italic: bool = False


@dataclass(slots=True)
class SensorSpec:
    fast_sensor: int = -1
    sensor_type_name: str = ""
    sensor_name: str = ""
    reading_name: str = ""
    is_div_1204: bool = False


@dataclass(slots=True)
class StyleSpec:
    show_type: int = 0
    bg_color_raw: str = ""
    bg_color: int = 0
    fg_color_raw: str = ""
    fg_color: int = 0
    frame_color_raw: str = ""
    frame_color: int = 0
    bg_image_path: str = ""
    fg_image_path: str = ""


@dataclass(slots=True)
class Widget:
    global_id: int = -1
    same_type_id: int = -1
    parent_name: str = ""
    object_name: str = ""
    widget_type: int = -1
    geometry: Geometry = field(default_factory=Geometry)
    font: FontSpec | None = None
    style: StyleSpec | None = None
    sensor: SensorSpec | None = None
    datetime_format: str = ""
    raw_fields: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WidgetParent:
    object_name: str = ""
    widget_type: int = -1
    geometry: Geometry = field(default_factory=Geometry)
    background_type: int = 0
    background_color_raw: str = ""
    background_color: int = 0
    background_image_path: str = ""
    image_delay: int = 0
    raw_fields: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Theme:
    path: str = ""
    widget_parents: list[WidgetParent] = field(default_factory=list)
    widgets: list[Widget] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StartupPicSpec:
    path: str = ""
    total_ms: int = 0
    delay_ms: int = 0
    bg_color_raw: str = ""
    bg_color: int = 0


@dataclass(slots=True)
class ThemeBundle:
    ui_path: str = ""
    base_dir: str = ""
    theme: Theme = field(default_factory=Theme)
    startup_pic: StartupPicSpec | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ImgDatRecord:
    index: int
    offset: int
    record_type: int
    record_type_name: str
    raw_hex: str
    fields: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ImgDatTheme:
    path: str
    slot_count: int
    slot_size: int
    records: list[ImgDatRecord]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
