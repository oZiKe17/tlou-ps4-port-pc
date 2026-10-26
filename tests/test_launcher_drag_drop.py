"""Regression tests for dropping game folders and PKG files onto the launcher."""
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from paths import ROOT
sys.path.insert(0, str(ROOT / "launcher"))
import tlou_launcher as launcher  # noqa: E402


class LauncherDragDropTest(unittest.TestCase):
    def make_launcher(self):
        app = launcher.Launcher.__new__(launcher.Launcher)
        app.root = SimpleNamespace(tk=tk.Tcl())
        app.vars = {"game_dir": mock.Mock()}
        app._set_status = mock.Mock()
        app._log = mock.Mock()
        return app

    def test_dropped_game_folder_with_spaces_sets_path(self):
        with tempfile.TemporaryDirectory(prefix="tlou drop folder ") as temp:
            folder = Path(temp) / "Extracted Game"
            folder.mkdir()
            (folder / "eboot.bin").write_bytes(b"test marker")
            app = self.make_launcher()
            event = SimpleNamespace(data="{" + str(folder) + "}")
            self.assertEqual(app._handle_game_drop(event), "copy")
            app.vars["game_dir"].set.assert_called_once_with(str(folder))

    def test_dropped_pkg_skips_file_picker_and_uses_extraction_flow(self):
        with tempfile.TemporaryDirectory(prefix="tlou drop pkg ") as temp:
            package = Path(temp) / "Game Update.PKG"
            package.write_bytes(b"test marker")
            app = self.make_launcher()
            app.extract_pkg = mock.Mock()
            event = SimpleNamespace(data="{" + str(package) + "}")
            self.assertEqual(app._handle_game_drop(event), "copy")
            app.extract_pkg.assert_called_once_with(str(package))

    def test_tkdnd_runtime_is_bundled_for_linux_and_windows(self):
        vendor = ROOT / "launcher" / "vendor" / "tkinterdnd2"
        self.assertTrue((vendor / "TkinterDnD.py").is_file())
        self.assertTrue((vendor / "tkdnd/linux-x64/libtkdnd2.10.3.so").is_file())
        self.assertTrue((vendor / "tkdnd/win-x64/libtkdnd2.10.3.dll").is_file())

    def test_open_source_pkg_extractor_can_be_selected_by_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            executable = Path(temp) / "ps4-pkg-tool"
            executable.write_bytes(b"test marker")
            executable.chmod(0o755)
            with mock.patch.dict("os.environ", {"TLG_PKG_EXTRACTOR": str(executable)}, clear=True):
                self.assertEqual(launcher.find_pkg_extractor(), executable)

    def test_linux_pkg_extractor_is_included_with_source(self):
        binaries = ROOT / "launcher/vendor/pkgtool/bin"
        executable = binaries / "ps4-pkg-tool"
        self.assertTrue(executable.is_file())
        self.assertTrue(executable.stat().st_mode & 0o111)
        self.assertTrue((binaries / "ps4-pkg-tool.exe").is_file())


if __name__ == "__main__":
    unittest.main()
