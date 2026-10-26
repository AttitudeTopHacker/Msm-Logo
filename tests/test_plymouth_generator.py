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
        mock_theme_dir = os.path.join(self.temp_dir, "themes")
        os.makedirs(os.path.join(mock_theme_dir, "sample-theme"), exist_ok=True)
        sample_plymouth = os.path.join(mock_theme_dir, "sample-theme", "sample-theme.plymouth")
        with open(sample_plymouth, "w") as f:
            f.write("[Plymouth Theme]\nName=Sample Display\nDescription=Sample Desc\nModuleName=script\n")

        orig_dir = SystemManager.PLYMOUTH_THEMES_DIR
        try:
            SystemManager.PLYMOUTH_THEMES_DIR = mock_theme_dir
            themes = SystemManager.list_installed_themes()
            self.assertIsInstance(themes, list)
            self.assertEqual(len(themes), 1)
            self.assertEqual(themes[0].id_name, "sample-theme")
            self.assertEqual(themes[0].display_name, "Sample Display")
            self.assertEqual(themes[0].description, "Sample Desc")
            self.assertEqual(themes[0].module_name, "script")
            self.assertFalse(themes[0].is_custom)
        finally:
            SystemManager.PLYMOUTH_THEMES_DIR = orig_dir

        # Also verify listing on current host system returns a valid list
        real_themes = SystemManager.list_installed_themes()
        self.assertIsInstance(real_themes, list)

    def test_factory_default_detection(self):
        # 1. Test detection when backup file is present
        mock_backup = os.path.join(self.temp_dir, "backup.json")
        dummy_theme = os.path.join(self.temp_dir, "mock-default.plymouth")
        with open(dummy_theme, "w") as f:
            f.write("[Plymouth Theme]\nName=Mock\n")
        with open(mock_backup, "w") as f:
            import json
            json.dump({"original_theme": dummy_theme}, f)

        orig_backup = SystemManager.BACKUP_FILE
        try:
            SystemManager.BACKUP_FILE = mock_backup
            self.assertTrue(SystemManager.has_factory_backup())
            self.assertEqual(SystemManager.get_official_default_theme_path(), dummy_theme)
        finally:
            SystemManager.BACKUP_FILE = orig_backup

        # 2. Test fallback behavior when no backup file exists
        try:
            SystemManager.BACKUP_FILE = "/nonexistent_test_backup.json"
            has_backup = SystemManager.has_factory_backup()
            self.assertIsInstance(has_backup, bool)
            path = SystemManager.get_official_default_theme_path()
            if path is not None:
                self.assertTrue(os.path.exists(path))
        finally:
            SystemManager.BACKUP_FILE = orig_backup


if __name__ == "__main__":
    unittest.main()
