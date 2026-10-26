"""Unit tests for MsmLogo rendering engine and data models."""

import os
import unittest
from PIL import Image
from msmlogo.core.models import ThemeProject, EffectConfig, TextItem
from msmlogo.core.renderer import BootRenderer
from msmlogo.core.templates import get_preset_templates


class TestBootRenderer(unittest.TestCase):
    def setUp(self):
        self.project = ThemeProject(
            name="test-boot",
            width=640,
            height=360,
            fps=15,
            duration=1.0,
            bg_type="gradient_radial",
            bg_color_1="#0a192f",
            bg_color_2="#020c1b",
            texts=[
                TextItem(text="Test Linux", font_size=28, offset_y=60, color="#ffffff"),
                TextItem(text="Testing Subtitle", font_size=14, offset_y=90, color="#64748b")
            ],
            effects=EffectConfig(
                shimmer_enabled=True,
                shimmer_angle=45.0,
                shimmer_intensity=0.8,
                glow_pulse_enabled=True,
                spinner_enabled=True,
                spinner_type="arc",
                zoom_effect="breathe"
            )
        )
        self.renderer = BootRenderer(self.project)

    def test_total_frames(self):
        self.assertEqual(self.project.total_frames, 15)

    def test_render_single_frame(self):
        frame = self.renderer.render_frame(0, 640, 360)
        self.assertIsInstance(frame, Image.Image)
        self.assertEqual(frame.size, (640, 360))
        self.assertEqual(frame.mode, "RGBA")

    def test_all_frames_renderable(self):
        for f in range(self.project.total_frames):
            frame = self.renderer.render_frame(f, 320, 180)
            self.assertEqual(frame.size, (320, 180))

    def test_preset_templates_validity(self):
        presets = get_preset_templates()
        self.assertIn("neon_pulse", presets)
        self.assertIn("mint_glow", presets)
        self.assertIn("ubuntu_aurora", presets)
        self.assertIn("minimal_power", presets)
        for name, p in presets.items():
            self.assertTrue(len(p.name) > 0)
            self.assertTrue(p.total_frames > 0)
            r = BootRenderer(p)
            img = r.render_frame(0, 320, 180)
            self.assertEqual(img.size, (320, 180))

    def test_multi_resolution_caching(self):
        # Frame at 640x360
        f1 = self.renderer.render_frame(0, 640, 360)
        # Frame at 480x270
        f2 = self.renderer.render_frame(0, 480, 270)
        self.assertEqual(f1.size, (640, 360))
        self.assertEqual(f2.size, (480, 270))
        # Both resolutions should be in cache
        self.assertGreaterEqual(len(self.renderer._cached_bgs), 2)

        # Invalidate cache
        self.renderer.invalidate_cache()
        self.assertEqual(len(self.renderer._cached_bgs), 0)
        self.assertEqual(len(self.renderer._cached_logos), 0)
        self.assertEqual(len(self.renderer._frame_cache), 0)

    def test_linear_gradient_rendering(self):
        self.project.bg_type = "gradient_linear"
        self.renderer.invalidate_cache()
        frame = self.renderer.render_frame(0, 320, 180)
        self.assertEqual(frame.size, (320, 180))
        self.assertEqual(frame.mode, "RGBA")

    def test_foreground_and_bbox_rendering(self):
        fg = self.renderer.render_foreground_frame(0, 640, 360)
        self.assertEqual(fg.size, (640, 360))
        self.assertEqual(fg.mode, "RGBA")
        bbox = self.renderer.get_unified_foreground_bbox(640, 360)
        self.assertEqual(len(bbox), 4)
        self.assertLess(bbox[0], bbox[2])
        self.assertLess(bbox[1], bbox[3])

    def test_static_emblem_and_isolated_spinner(self):
        emblem = self.renderer.render_static_emblem(640, 360)
        self.assertIsInstance(emblem, Image.Image)
        self.assertGreater(emblem.width, 0)
        self.assertGreater(emblem.height, 0)

        spinner = self.renderer.render_isolated_spinner_frame(0, 30)
        self.assertIsNotNone(spinner)
        self.assertIsInstance(spinner, Image.Image)
        self.assertGreaterEqual(spinner.width, self.project.effects.spinner_size)


if __name__ == "__main__":
    unittest.main()
