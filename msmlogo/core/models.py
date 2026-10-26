"""Data models and configuration schema for MsmLogo project and theme definitions."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
import json
import os


@dataclass
class TextItem:
    text: str = "Linux"
    font_family: str = "DejaVu Sans"
    font_size: int = 40
    color: str = "#FFFFFF"
    is_bold: bool = True
    is_italic: bool = False
    offset_y: int = 140
    offset_x: int = 0
    glow_enabled: bool = True
    glow_color: str = "#38bdf8"
    letter_spacing: int = 2

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class EffectConfig:
    # Shimmer sweep
    shimmer_enabled: bool = True
    shimmer_angle: float = 45.0  # degrees
    shimmer_width: float = 0.25  # fraction of width
    shimmer_color: str = "#FFFFFF"
    shimmer_intensity: float = 0.85
    shimmer_speed_mult: float = 1.0

    # Pulse / radial glow
    glow_pulse_enabled: bool = True
    glow_color: str = "#38bdf8"
    glow_radius: int = 36
    glow_min_intensity: float = 0.3
    glow_max_intensity: float = 0.9

    # Spinner / throbber
    spinner_enabled: bool = True
    spinner_type: str = "arc"  # "arc", "ring", "dots", "dual_ring", "none"
    spinner_color: str = "#38bdf8"
    spinner_secondary_color: str = "#818cf8"
    spinner_size: int = 60
    spinner_offset_y: int = 220
    spinner_offset_x: int = 0
    spinner_speed_mult: float = 1.0

    # Transitions
    fade_in: bool = True
    fade_out: bool = True
    fade_duration_ratio: float = 0.15  # fraction of total duration for fade in/out

    # Scale / Breathe / Zoom
    zoom_effect: str = "breathe"  # "none", "breathe", "zoom_in", "zoom_out"
    zoom_intensity: float = 0.04

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ThemeProject:
    name: str = "msm-custom-boot"
    display_name: str = "Custom Boot Theme"
    author: str = "MsmLogo Creator"
    version: str = "1.0.0"

    # Canvas & Video specs
    width: int = 1920
    height: int = 1080
    fps: int = 30
    duration: float = 3.0  # seconds

    # Background
    bg_type: str = "gradient_radial"  # "solid", "gradient_linear", "gradient_radial", "image"
    bg_color_1: str = "#0b0f19"
    bg_color_2: str = "#020617"
    bg_image_path: Optional[str] = None

    # Logo
    logo_path: Optional[str] = None
    logo_scale: float = 0.45  # relative to screen height
    logo_offset_x: int = 0
    logo_offset_y: int = -50

    # Texts
    texts: List[TextItem] = field(default_factory=lambda: [
        TextItem(text="Linux Mint", font_size=42, is_bold=True, offset_y=130, color="#FFFFFF"),
        TextItem(text="Booting System...", font_size=18, is_bold=False, offset_y=175, color="#94A3B8")
    ])

    # Effects
    effects: EffectConfig = field(default_factory=EffectConfig)

    # Integration flags
    sync_grub: bool = True
    plymouth_module: str = "auto"  # "auto", "script", or "two-step"

    @property
    def total_frames(self) -> int:
        return max(1, int(round(self.fps * self.duration)))

    def to_dict(self) -> dict:
        data = asdict(self)
        data["texts"] = [t.to_dict() for t in self.texts]
        data["effects"] = self.effects.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ThemeProject":
        project = cls()
        for k, v in data.items():
            if k == "texts":
                project.texts = [TextItem.from_dict(t) for t in v]
            elif k == "effects":
                project.effects = EffectConfig.from_dict(v)
            elif hasattr(project, k):
                setattr(project, k, v)
        return project

    def save_to_file(self, filepath: str):
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "ThemeProject":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
