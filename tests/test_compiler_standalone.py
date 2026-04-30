from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from smartmonitor_hid import ThemeCompiler, parse_imgdat_file
from smartmonitor_hid.theme import FontSpec, Geometry, Theme, ThemeBundle, Widget, WidgetParent
from smartmonitor_hid.ui import write_theme_file


class StandaloneCompilerTests(unittest.TestCase):
    def test_compile_ui_file_without_bridge_or_external_vendor_files(self):
        bundle = ThemeBundle(
            ui_path="standalone.ui",
            base_dir=".",
            theme=Theme(
                path="standalone.ui",
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
                        object_name="title",
                        widget_type=2,
                        geometry=Geometry(x=20, y=20, width=120, height=24),
                        font=FontSpec(
                            text="CPU",
                            name="Sans",
                            color_raw="0xffffffff",
                            color=0xFFFFFFFF,
                            size=14,
                        ),
                    ),
                    Widget(
                        global_id=2,
                        same_type_id=1,
                        parent_name="Background",
                        object_name="cpu_temp",
                        widget_type=5,
                        geometry=Geometry(x=20, y=60, width=100, height=24),
                        font=FontSpec(
                            text="42",
                            name="Sans",
                            color_raw="0xffffffff",
                            color=0xFFFFFFFF,
                            size=14,
                        ),
                    ),
                    Widget(
                        global_id=3,
                        same_type_id=1,
                        parent_name="Background",
                        object_name="clock",
                        widget_type=6,
                        geometry=Geometry(x=20, y=100, width=140, height=28),
                        font=FontSpec(
                            text="",
                            name="Sans",
                            color_raw="0xffffffff",
                            color=0xFFFFFFFF,
                            size=14,
                        ),
                        datetime_format="HH:mm:ss",
                    ),
                ],
            ),
        )

        compiler = ThemeCompiler()
        with TemporaryDirectory() as temp_dir:
            ui_path = Path(temp_dir) / "standalone.ui"
            dat_path = Path(temp_dir) / "standalone.dat"
            write_theme_file(ui_path, bundle)

            compiler.compile_ui_to_file(ui_path, dat_path)
            parsed = parse_imgdat_file(dat_path)

        type_names = {record.record_type_name for record in parsed.records}
        self.assertIn("static_text_widget", type_names)
        self.assertIn("number_widget", type_names)
        self.assertIn("datetime_widget", type_names)
        self.assertGreater(len(dat_path.name), 0)


if __name__ == "__main__":
    unittest.main()
