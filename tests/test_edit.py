from __future__ import annotations

import unittest

from smartmonitor_hid.edit import (
    add_widget,
    clear_widget_sensor,
    duplicate_widget,
    find_widget,
    move_widget,
    next_widget_ids,
    remove_widget,
    set_widget_datetime_format,
    set_widget_geometry,
    set_widget_sensor,
)
from smartmonitor_hid.theme import FontSpec, Geometry, Theme, ThemeBundle, Widget, WidgetParent


class ThemeEditApiTests(unittest.TestCase):
    def _bundle(self) -> ThemeBundle:
        return ThemeBundle(
            ui_path="edit.ui",
            base_dir=".",
            theme=Theme(
                path="edit.ui",
                widget_parents=[
                    WidgetParent(
                        object_name="Background",
                        widget_type=1,
                        geometry=Geometry(x=0, y=0, width=480, height=320),
                    )
                ],
                widgets=[
                    Widget(
                        global_id=1,
                        same_type_id=1,
                        parent_name="Background",
                        object_name="clock",
                        widget_type=6,
                        geometry=Geometry(x=10, y=10, width=100, height=24),
                        font=FontSpec(name="Sans", color_raw="0xffffffff", color=0xFFFFFFFF, size=12),
                        datetime_format="HH:mm:ss",
                    )
                ],
            ),
        )

    def test_add_and_find_widget(self):
        bundle = self._bundle()
        widget = Widget(
            global_id=0,
            same_type_id=0,
            parent_name="Background",
            object_name="cpu_temp",
            widget_type=5,
            geometry=Geometry(x=1, y=2, width=3, height=4),
        )
        added = add_widget(bundle, widget)
        found = find_widget(bundle, object_name="cpu_temp")
        self.assertEqual(added.global_id, 2)
        self.assertIs(found, added)

    def test_duplicate_widget(self):
        bundle = self._bundle()
        duplicated = duplicate_widget(bundle, object_name="clock", new_object_name="clock_copy", dx=5, dy=7)
        self.assertEqual(duplicated.object_name, "clock_copy")
        self.assertEqual(duplicated.geometry.x, 15)
        self.assertEqual(duplicated.geometry.y, 17)
        self.assertEqual(len(bundle.theme.widgets), 2)

    def test_move_and_geometry_update(self):
        bundle = self._bundle()
        move_widget(bundle, object_name="clock", dx=3, dy=4)
        widget = set_widget_geometry(bundle, object_name="clock", width=120, height=30)
        self.assertEqual(widget.geometry.x, 13)
        self.assertEqual(widget.geometry.y, 14)
        self.assertEqual(widget.geometry.width, 120)
        self.assertEqual(widget.geometry.height, 30)

    def test_set_and_clear_sensor(self):
        bundle = self._bundle()
        widget = set_widget_sensor(
            bundle,
            object_name="clock",
            fast_sensor=9,
            sensor_type_name="Other",
            sensor_name="System",
            reading_name="Sound Volume",
        )
        self.assertEqual(widget.sensor.fast_sensor, 9)
        cleared = clear_widget_sensor(bundle, object_name="clock")
        self.assertIsNone(cleared.sensor)

    def test_set_datetime_and_remove(self):
        bundle = self._bundle()
        widget = set_widget_datetime_format(bundle, object_name="clock", datetime_format="yyyy-MM-dd")
        self.assertEqual(widget.datetime_format, "yyyy-MM-dd")
        removed = remove_widget(bundle, object_name="clock")
        self.assertEqual(removed.object_name, "clock")
        self.assertEqual(len(bundle.theme.widgets), 0)

    def test_next_widget_ids(self):
        bundle = self._bundle()
        next_global, next_same_type_default = next_widget_ids(bundle)
        self.assertEqual(next_global, 2)
        self.assertEqual(next_same_type_default, 2)


if __name__ == "__main__":
    unittest.main()
