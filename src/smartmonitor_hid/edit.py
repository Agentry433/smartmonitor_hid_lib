from __future__ import annotations

from copy import deepcopy

from .theme import Geometry, SensorSpec, Theme, ThemeBundle, Widget


def _theme_from_target(target: Theme | ThemeBundle) -> Theme:
    return target.theme if isinstance(target, ThemeBundle) else target


def next_widget_ids(target: Theme | ThemeBundle) -> tuple[int, int]:
    theme = _theme_from_target(target)
    next_global = max((widget.global_id for widget in theme.widgets), default=0) + 1
    same_type_counters: dict[int, int] = {}
    for widget in theme.widgets:
        same_type_counters[widget.widget_type] = max(
            same_type_counters.get(widget.widget_type, 0),
            widget.same_type_id,
        )
    next_same_type_default = max(same_type_counters.values(), default=0) + 1
    return next_global, next_same_type_default


def find_widget(target: Theme | ThemeBundle, *, object_name: str | None = None, global_id: int | None = None) -> Widget:
    theme = _theme_from_target(target)
    for widget in theme.widgets:
        if object_name is not None and widget.object_name == object_name:
            return widget
        if global_id is not None and widget.global_id == global_id:
            return widget
    raise KeyError(f"Widget not found: object_name={object_name!r}, global_id={global_id!r}")


def clone_widget(widget: Widget) -> Widget:
    return deepcopy(widget)


def add_widget(target: Theme | ThemeBundle, widget: Widget, *, assign_ids: bool = True) -> Widget:
    theme = _theme_from_target(target)
    new_widget = clone_widget(widget)
    if assign_ids:
        next_global, _ = next_widget_ids(theme)
        next_same_type = max(
            (item.same_type_id for item in theme.widgets if item.widget_type == new_widget.widget_type),
            default=0,
        ) + 1
        new_widget.global_id = next_global
        new_widget.same_type_id = next_same_type
    theme.widgets.append(new_widget)
    return new_widget


def remove_widget(target: Theme | ThemeBundle, *, object_name: str | None = None, global_id: int | None = None) -> Widget:
    theme = _theme_from_target(target)
    for index, widget in enumerate(theme.widgets):
        if object_name is not None and widget.object_name == object_name:
            return theme.widgets.pop(index)
        if global_id is not None and widget.global_id == global_id:
            return theme.widgets.pop(index)
    raise KeyError(f"Widget not found: object_name={object_name!r}, global_id={global_id!r}")


def duplicate_widget(
    target: Theme | ThemeBundle,
    *,
    object_name: str | None = None,
    global_id: int | None = None,
    new_object_name: str | None = None,
    dx: int = 0,
    dy: int = 0,
) -> Widget:
    source = find_widget(target, object_name=object_name, global_id=global_id)
    duplicated = add_widget(target, source, assign_ids=True)
    if new_object_name:
        duplicated.object_name = new_object_name
    duplicated.geometry.x += dx
    duplicated.geometry.y += dy
    return duplicated


def move_widget(
    target: Theme | ThemeBundle,
    *,
    object_name: str | None = None,
    global_id: int | None = None,
    dx: int = 0,
    dy: int = 0,
) -> Widget:
    widget = find_widget(target, object_name=object_name, global_id=global_id)
    widget.geometry.x += dx
    widget.geometry.y += dy
    return widget


def set_widget_geometry(
    target: Theme | ThemeBundle,
    *,
    object_name: str | None = None,
    global_id: int | None = None,
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> Widget:
    widget = find_widget(target, object_name=object_name, global_id=global_id)
    if x is not None:
        widget.geometry.x = int(x)
    if y is not None:
        widget.geometry.y = int(y)
    if width is not None:
        widget.geometry.width = int(width)
    if height is not None:
        widget.geometry.height = int(height)
    return widget


def set_widget_sensor(
    target: Theme | ThemeBundle,
    *,
    object_name: str | None = None,
    global_id: int | None = None,
    fast_sensor: int,
    sensor_type_name: str = "",
    sensor_name: str = "",
    reading_name: str = "",
    is_div_1204: bool = False,
) -> Widget:
    widget = find_widget(target, object_name=object_name, global_id=global_id)
    widget.sensor = SensorSpec(
        fast_sensor=int(fast_sensor),
        sensor_type_name=sensor_type_name,
        sensor_name=sensor_name,
        reading_name=reading_name,
        is_div_1204=bool(is_div_1204),
    )
    return widget


def clear_widget_sensor(
    target: Theme | ThemeBundle,
    *,
    object_name: str | None = None,
    global_id: int | None = None,
) -> Widget:
    widget = find_widget(target, object_name=object_name, global_id=global_id)
    widget.sensor = None
    return widget


def set_widget_datetime_format(
    target: Theme | ThemeBundle,
    *,
    object_name: str | None = None,
    global_id: int | None = None,
    datetime_format: str,
) -> Widget:
    widget = find_widget(target, object_name=object_name, global_id=global_id)
    widget.datetime_format = datetime_format
    return widget
