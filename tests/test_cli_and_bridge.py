from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from smartmonitor_hid._bridge import ENV_PROJECT_ROOT, configure_project_root, import_project_module
from smartmonitor_hid.cli import build_parser, main
from smartmonitor_hid.compiler import ThemeCompiler
from smartmonitor_hid.errors import SmartMonitorBridgeError, SmartMonitorCompilerError


class CliAndBridgeTests(unittest.TestCase):
    def test_build_parser_accepts_detect_command(self):
        parser = build_parser()
        args = parser.parse_args(["detect"])
        self.assertEqual(args.command, "detect")

    def test_build_parser_accepts_project_root_option(self):
        parser = build_parser()
        args = parser.parse_args(["--project-root", "/tmp/project", "detect"])
        self.assertEqual(args.project_root, "/tmp/project")

    def test_cli_compile_ui_uses_compiler_facade(self):
        with TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "out.dat"
            with patch("smartmonitor_hid.cli.ThemeCompiler.compile_ui_to_file", return_value=output) as compile_mock:
                rc = main(["compile-ui", "theme.ui", str(output)])
        self.assertEqual(rc, 0)
        compile_mock.assert_called_once()

    def test_compiler_wraps_compile_failures(self):
        compiler = ThemeCompiler()
        with patch(
            "smartmonitor_hid.compiler.compile_theme_file",
            side_effect=RuntimeError("compile failed"),
        ):
            with self.assertRaises(SmartMonitorCompilerError):
                compiler.compile_ui_file("theme.ui")

    def test_bridge_can_import_from_configured_project_root(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            library_dir = root / "library"
            library_dir.mkdir(parents=True)
            (library_dir / "__init__.py").write_text("", encoding="utf-8")
            (library_dir / "fake_module.py").write_text("VALUE = 123\n", encoding="utf-8")

            configure_project_root(root)
            try:
                module = import_project_module("library.fake_module")
            finally:
                configure_project_root(None)

        self.assertEqual(module.VALUE, 123)

    def test_bridge_uses_env_project_root(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            library_dir = root / "library"
            library_dir.mkdir(parents=True)
            (library_dir / "__init__.py").write_text("", encoding="utf-8")
            (library_dir / "env_module.py").write_text("VALUE = 456\n", encoding="utf-8")

            with patch.dict("os.environ", {ENV_PROJECT_ROOT: str(root)}, clear=False):
                configure_project_root(None)
                module = import_project_module("library.env_module")

        self.assertEqual(module.VALUE, 456)


if __name__ == "__main__":
    unittest.main()
