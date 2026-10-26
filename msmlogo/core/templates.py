"""Pre-built ready-to-edit templates for MsmLogo."""

import os
from typing import List, Dict
from .models import ThemeProject, EffectConfig, TextItem

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))
SAMPLES_DIR = os.path.join(ASSETS_DIR, "samples")


def get_preset_templates() -> Dict[str, ThemeProject]:
    templates = {}

    # 1. Cyberpunk Neon Pulse
    p1 = ThemeProject(
        name="msm-neon-pulse",
        display_name="Cyberpunk Neon Pulse",
        author="MsmLogo",
        version="1.0.0",
        width=1920,
        height=1080,
        fps=30,
        duration=3.0,
        bg_type="gradient_radial",
        bg_color_1="#0a0f1d",
        bg_color_2="#030712",
        logo_path=os.path.join(SAMPLES_DIR, "cyber_emblem.png"),
        logo_scale=0.36,
        logo_offset_y=-50,
        texts=[
            TextItem(text="CYBER LINUX", font_size=44, is_bold=True, offset_y=140, color="#22d3ee", glow_enabled=True, glow_color="#06b6d4"),
            TextItem(text="CORE INITIALIZED", font_size=16, is_bold=False, offset_y=185, color="#f472b6", glow_enabled=True, glow_color="#ec4899")
        ],
        effects=EffectConfig(
            shimmer_enabled=True,
            shimmer_angle=60.0,
            shimmer_color="#38bdf8",
            shimmer_intensity=0.9,
            glow_pulse_enabled=True,
            glow_color="#06b6d4",
            glow_radius=40,
            spinner_enabled=True,
            spinner_type="dual_ring",
            spinner_color="#22d3ee",
            spinner_secondary_color="#ec4899",
            spinner_size=64,
            spinner_offset_y=230,
            zoom_effect="breathe",
            zoom_intensity=0.04
        ),
        sync_grub=True
    )
    templates["neon_pulse"] = p1

    # 2. Linux Mint Modern Glow
    p2 = ThemeProject(
        name="msm-mint-glow",
        display_name="Linux Mint Modern Glow",
        author="MsmLogo",
        version="1.0.0",
        width=1920,
        height=1080,
        fps=30,
        duration=3.0,
        bg_type="gradient_radial",
        bg_color_1="#0a1a0f",
        bg_color_2="#020804",
        logo_path=os.path.join(SAMPLES_DIR, "mint_emblem.png"),
        logo_scale=0.38,
        logo_offset_y=-50,
        texts=[
            TextItem(text="Linux Mint", font_size=42, is_bold=True, offset_y=135, color="#ffffff", glow_enabled=True, glow_color="#87cf3e"),
            TextItem(text="Freedom in Elegance", font_size=17, is_bold=False, offset_y=178, color="#a3e635", glow_enabled=False)
        ],
        effects=EffectConfig(
            shimmer_enabled=True,
            shimmer_angle=45.0,
            shimmer_color="#ffffff",
            shimmer_intensity=0.8,
            glow_pulse_enabled=True,
            glow_color="#87cf3e",
            glow_radius=35,
            spinner_enabled=True,
            spinner_type="dots",
            spinner_color="#87cf3e",
            spinner_size=56,
            spinner_offset_y=225,
            zoom_effect="breathe",
            zoom_intensity=0.03
        ),
        sync_grub=True
    )
    templates["mint_glow"] = p2

    # 3. Ubuntu Cosmic Aurora
    p3 = ThemeProject(
        name="msm-ubuntu-aurora",
        display_name="Ubuntu Cosmic Aurora",
        author="MsmLogo",
        version="1.0.0",
        width=1920,
        height=1080,
        fps=30,
        duration=3.0,
        bg_type="gradient_radial",
        bg_color_1="#240c2e",
        bg_color_2="#0c0211",
        logo_path=os.path.join(SAMPLES_DIR, "ubuntu_emblem.png"),
        logo_scale=0.35,
        logo_offset_y=-50,
        texts=[
            TextItem(text="Ubuntu Linux", font_size=42, is_bold=True, offset_y=135, color="#ffffff", glow_enabled=True, glow_color="#e95420"),
            TextItem(text="I am because we are", font_size=16, is_bold=False, offset_y=178, color="#fdba74", glow_enabled=False)
        ],
        effects=EffectConfig(
            shimmer_enabled=True,
            shimmer_angle=50.0,
            shimmer_color="#fed7aa",
            shimmer_intensity=0.85,
            glow_pulse_enabled=True,
            glow_color="#e95420",
            glow_radius=38,
            spinner_enabled=True,
            spinner_type="arc",
            spinner_color="#e95420",
            spinner_size=58,
            spinner_offset_y=225,
            zoom_effect="breathe",
            zoom_intensity=0.03
        ),
        sync_grub=True
    )
    templates["ubuntu_aurora"] = p3

    # 4. Minimal Power Shimmer
    p4 = ThemeProject(
        name="msm-minimal-power",
        display_name="Minimal Power Shimmer",
        author="MsmLogo",
        version="1.0.0",
        width=1920,
        height=1080,
        fps=30,
        duration=3.0,
        bg_type="gradient_radial",
        bg_color_1="#0f172a",
        bg_color_2="#020617",
        logo_path=os.path.join(SAMPLES_DIR, "minimal_power.png"),
        logo_scale=0.38,
        logo_offset_y=-50,
        texts=[
            TextItem(text="SYSTEM READY", font_size=38, is_bold=True, offset_y=135, color="#f8fafc", glow_enabled=True, glow_color="#6366f1"),
            TextItem(text="Starting Services...", font_size=16, is_bold=False, offset_y=175, color="#94a3b8", glow_enabled=False)
        ],
        effects=EffectConfig(
            shimmer_enabled=True,
            shimmer_angle=45.0,
            shimmer_color="#ffffff",
            shimmer_intensity=0.9,
            glow_pulse_enabled=True,
            glow_color="#818cf8",
            glow_radius=30,
            spinner_enabled=True,
            spinner_type="ring",
            spinner_color="#6366f1",
            spinner_size=54,
            spinner_offset_y=220,
            zoom_effect="breathe",
            zoom_intensity=0.02
        ),
        sync_grub=True
    )
    templates["minimal_power"] = p4

    return templates
