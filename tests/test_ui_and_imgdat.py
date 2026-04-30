from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from smartmonitor_hid.imgdat import parse_imgdat, parse_imgdat_file, pack_record_fields
from smartmonitor_hid.theme import FontSpec, Geometry, SensorSpec, Theme, ThemeBundle, Widget, WidgetParent
from smartmonitor_hid.ui import decode_ui_file, parse_theme_bundle, theme_to_xml, write_theme_file


class UiAndImgDatTests(unittest.TestCase):
    def test_theme_bundle_roundtrip(self):
        bundle = ThemeBundle(
            ui_path="theme.ui",
            base_dir=".",
            theme=Theme(
                path="theme.ui",
                widget_parents=[
                    WidgetParent(
                        object_name="Background",
                        widget_type=1,
                        geometry=Geometry(x=0, y=0, width=480, height=320),
                        background_type=0,
                        background_color_raw="0xff000000",
                        background_color=0xFF000000,
                    )
                ],
                widgets=[
                    Widget(
                        global_id=1,
                        same_type_id=1,
                        parent_name="Background",
                        object_name="cpu_temp",
                        widget_type=5,
                        geometry=Geometry(x=10, y=20, width=100, height=24),
                        font=FontSpec(
                            text="42",
                            name="Arial",
                            color_raw="0xffffffff",
                            color=0xFFFFFFFF,
                            size=12,
                        ),
                        sensor=SensorSpec(
                            fast_sensor=1,
                            sensor_type_name="Temperature",
                            sensor_name="CPU Package",
                            reading_name="CPU Temperature",
                        ),
                    )
                ],
            ),
        )

        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "theme.ui"
            write_theme_file(path, bundle)
            decoded = decode_ui_file(path).decode("utf-8")
            reparsed = parse_theme_bundle(path)

        self.assertIn("<ui>", decoded)
        self.assertEqual(reparsed.theme.widgets[0].object_name, "cpu_temp")
        self.assertEqual(reparsed.theme.widgets[0].sensor.fast_sensor, 1)

    def test_theme_to_xml_contains_expected_fields(self):
        theme = Theme(
            widgets=[
                Widget(
                    global_id=2,
                    same_type_id=1,
                    parent_name="Background",
                    object_name="clock",
                    widget_type=6,
                    geometry=Geometry(x=1, y=2, width=3, height=4),
                    datetime_format="HH:mm:ss",
                )
            ]
        )
        xml_text = theme_to_xml(theme)
        self.assertIn('objectName="clock"', xml_text)
        self.assertIn("dateTimeFormat", xml_text)

    def test_parse_imgdat_from_bytes(self):
        slot_count = 1
        header = slot_count.to_bytes(4, "little") + b"\x00" * 60
        record = pack_record_fields(
            0x92,
            {
                "widget_id": 1,
                "fast_sensor": 3,
                "x": 10,
                "y": 20,
                "width": 100,
                "height": 24,
                "h_align": 0,
                "font_color_rgb565": 0xFFFF,
                "is_div_1204": False,
                "font_alpha": 255,
                "glyph_bitmap_offset": 0x1000,
                "glyph_bitmap_height": 12,
                "glyph_widths": [6] * 12,
            },
        )
        data = header + record

        parsed = parse_imgdat(data, path="memory")

        self.assertEqual(parsed.slot_count, 1)
        self.assertEqual(parsed.records[0].record_type_name, "number_widget")
        self.assertEqual(parsed.records[0].fields["fast_sensor"], 3)

    def test_parse_imgdat_file(self):
        slot_count = 1
        header = slot_count.to_bytes(4, "little") + b"\x00" * 60
        record = pack_record_fields(
            0x84,
            {
                "widget_id": 1,
                "reserved_2": 0,
                "x": 1,
                "y": 2,
                "width": 3,
                "height": 4,
                "asset_offset": 0x1000,
                "frame_count": 1,
                "is_png": False,
                "delay_ms": 0,
            },
        )
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "img.dat"
            path.write_bytes(header + record)
            parsed = parse_imgdat_file(path)

        self.assertEqual(parsed.records[0].record_type_name, "image_widget")


if __name__ == "__main__":
    unittest.main()
