"""Unit tests for Plymouth package generator and system manager."""

import os
import shutil
import tempfile
import unittest
from msmlogo.core.models import ThemeProject
from msmlogo.core.plymouth_generator import PlymouthGenerator
from msmlogo.core.system_manager import SystemManager


class TestPlymouthGenerator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="msm_test_")
        self.project = ThemeProject(
            name="msm-unit-test",
            display_name="Unit Test Theme",
            width=320,
            height=180,
            fps=10,
            duration=1.0  # 10 frames
        )

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_theme_generation(self):
        gen = PlymouthGenerator(self.project)
        progress_records = []

        theme_dir = gen.generate_theme(
            self.temp_dir,
            progress_callback=lambda cur, tot, msg: progress_records.append((cur, tot))
        )

        self.assertTrue(os.path.isdir(theme_dir))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "msm-unit-test.plymouth")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "msm-unit-test.script")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "animation-0001.png")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "animation-0010.png")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "background.png")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "grub-background.png")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "preview.png")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "bullet.png")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "entry.png")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "lock.png")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "capslock.png")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "keyboard.png")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "watermark.png")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "throbber-0001.png")))
        self.assertTrue(len(progress_records) > 0)

    def test_script_module_generation(self):
        self.project.plymouth_module = "script"
        gen = PlymouthGenerator(self.project)
        theme_dir = gen.generate_theme(self.temp_dir)
        plymouth_cfg = os.path.join(theme_dir, "msm-unit-test.plymouth")
        with open(plymouth_cfg, "r") as f:
            content = f.read()
        self.assertIn("ModuleName=script", content)
        self.assertIn("ScriptFile=", content)
        # Check script content contains position offset
        with open(os.path.join(theme_dir, "msm-unit-test.script"), "r") as f:
            script_body = f.read()
        self.assertIn("anim_sprite.SetPosition", script_body)

    def test_two_step_oem_generation(self):
        self.project.plymouth_module = "two-step"
        gen = PlymouthGenerator(self.project)
        theme_dir = gen.generate_theme(self.temp_dir)
        plymouth_cfg = os.path.join(theme_dir, "msm-unit-test.plymouth")
        with open(plymouth_cfg, "r") as f:
            content = f.read()
        self.assertIn("ModuleName=two-step", content)
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "header-image.png")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "bgrt-fallback.png")))
        self.assertTrue(os.path.exists(os.path.join(theme_dir, "throbber-0001.png")))

    def test_system_theme_listing(self):
        themes = SystemManager.list_installed_themes()
        self.assertIsInstance(themes, list)
        self.assertTrue(len(themes) > 0)
        names = [t.id_name for t in themes]
        self.assertIn("mint-logo", names)

    def test_factory_default_detection(self):
        self.assertTrue(SystemManager.has_factory_backup())
        path = SystemManager.get_official_default_theme_path()
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
