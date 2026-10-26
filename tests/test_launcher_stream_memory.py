"""The TLOU launcher keeps worker and staging defaults portable across hosts."""
import sys
import tkinter as tk
import unittest
from pathlib import Path

from paths import ROOT
sys.path.insert(0, str(ROOT.parent / "launcher"))
import tlou_launcher as launcher  # noqa: E402


def make_settings_app():
    interp = tk.Tcl()
    app = launcher.Launcher.__new__(launcher.Launcher)
    app.settings = launcher.DEFAULTS.copy()
    app.vars = {
        key: tk.StringVar(master=interp, value=str(value))
        for key, value in launcher.DEFAULTS.items() if not isinstance(value, bool)
    }
    app.bools = {
        key: tk.BooleanVar(master=interp, value=value)
        for key, value in launcher.DEFAULTS.items() if isinstance(value, bool)
    }
    app.switch_vars = {
        key: tk.BooleanVar(master=interp, value=str(value) in {"1", "true", "yes", "on"})
        for key, value in launcher.DEFAULTS.items() if key in launcher.SWITCH_KEYS
    }
    return app


class LauncherPortableSizingTest(unittest.TestCase):
    def test_motion_help_and_language_selectors_cover_only_launcher_locales(self):
        locales = {"es", "pt", "en", "fr"}
        self.assertEqual(set(launcher.MOTION_HELP_TEXT), locales)
        self.assertEqual(set(launcher.LAUNCHER_LANGUAGE_CODES.values()), locales)
        self.assertEqual(len(launcher.LANGUAGE_PRESETS), 4)
        for text in launcher.MOTION_HELP_TEXT.values():
            self.assertTrue(text["link"])
            self.assertTrue(text["stick"])
            self.assertTrue(text["shake"])
            self.assertTrue(text["note"])

    def test_defaults_delegate_thread_and_staging_sizing_to_runtime(self):
        settings = make_settings_app()._collect_settings()
        self.assertEqual(settings["copy_threads"], "auto")
        self.assertEqual(settings["staging_keep"], "auto")
        self.assertEqual(settings["phys_cores"], "0")
        self.assertEqual(settings["hot_pages"], "0")

    def test_explicit_valid_overrides_are_preserved(self):
        app = make_settings_app()
        app.vars["copy_threads"].set("3")
        app.vars["staging_keep"].set("384")
        app.switch_vars["phys_cores"].set(True)
        settings = app._collect_settings()
        self.assertEqual(settings["copy_threads"], "3")
        self.assertEqual(settings["staging_keep"], "384")
        self.assertEqual(settings["phys_cores"], "1")

    def test_boolean_advanced_values_are_collected_from_switch_state(self):
        app = make_settings_app()
        app.switch_vars["async_shaders"].set(True)
        app.switch_vars["hot_pages"].set(False)
        settings = app._collect_settings()
        self.assertEqual(settings["async_shaders"], "1")
        self.assertEqual(settings["hot_pages"], "0")

    def test_boolean_core_mode_is_serialized_as_a_switch(self):
        app = make_settings_app()
        app.switch_vars["phys_cores"].set(True)
        app.vars["copy_threads"].set("auto")
        app.vars["staging_keep"].set("auto")
        settings = app._collect_settings()
        self.assertEqual(settings["phys_cores"], "1")
        self.assertEqual(settings["copy_threads"], "auto")
        self.assertEqual(settings["staging_keep"], "auto")

    def test_audio_volume_is_clamped_and_upscaler_names_match_runtime(self):
        app = make_settings_app()
        app.vars["audio_volume"].set("140")
        settings = app._collect_settings()
        self.assertEqual(settings["audio_volume"], "100")
        self.assertEqual(settings["gpu_device"], "auto")
        self.assertEqual(launcher.UPSCALER_RUNTIME_NAME,
                         {"0": "off", "1": "fsr3", "2": "fsr4", "4": "taa"})

    def test_fullscreen_game_restores_the_launcher_window(self):
        class FakeRoot:
            def __init__(self):
                self.calls = []

            def state(self): return "normal"
            def lower(self): self.calls.append("lower")
            def deiconify(self): self.calls.append("deiconify")
            def attributes(self, *args): self.calls.append(("attributes", *args))
            def lift(self): self.calls.append("lift")
            def focus_force(self): self.calls.append("focus")

        app = launcher.Launcher.__new__(launcher.Launcher)
        app.root = FakeRoot()
        app.app_fullscreen = False
        app.minimized_for_game = True
        app._ensure_minimized_for_game()
        self.assertIn("lower", app.root.calls)
        app._restore_window_after_game()
        self.assertFalse(app.minimized_for_game)
        self.assertIn("deiconify", app.root.calls)
        self.assertIn("lift", app.root.calls)
        self.assertNotIn("destroy", app.root.calls)


if __name__ == "__main__":
    unittest.main()
