"""Preset Templates Gallery Tab."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout
)
from ..core.models import ThemeProject
from ..core.templates import get_preset_templates


class PresetCard(QFrame):
    """Visual card displaying a preset template with description and load action."""

    load_requested = pyqtSignal(ThemeProject)

    def __init__(self, key: str, template: ThemeProject, parent=None):
        super().__init__(parent)
        self.key = key
        self.template = template
        self.setObjectName("presetCard")
        self.setStyleSheet("""
            #presetCard {
                background-color: #111827;
                border: 1px solid #1f293d;
                border-radius: 12px;
                padding: 14px;
            }
            #presetCard:hover {
                border-color: #38bdf8;
                background-color: #131d31;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header Row: Title & Badge
        hdr = QHBoxLayout()
        title_lbl = QLabel(self.template.display_name)
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #f8fafc;")
        hdr.addWidget(title_lbl)

        hdr.addStretch()

        badge_text = {
            "neon_pulse": "NEON CYBER",
            "mint_glow": "MINT CLEAN",
            "ubuntu_aurora": "AUBERGINE",
            "minimal_power": "MINIMAL"
        }.get(self.key, "PRESET")

        badge = QLabel(badge_text)
        badge.setStyleSheet("""
            background-color: #0369a1;
            color: #ffffff;
            font-size: 10px;
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 6px;
        """)
        hdr.addWidget(badge)
        layout.addLayout(hdr)

        # Specs info
        specs_row = QHBoxLayout()
        fps_info = QLabel(f"⏱️ {self.template.fps} FPS · {self.template.duration}s")
        fps_info.setStyleSheet("color: #94a3b8; font-size: 12px;")
        specs_row.addWidget(fps_info)

        spinner_info = QLabel(f"🔄 {self.template.effects.spinner_type}")
        spinner_info.setStyleSheet("color: #38bdf8; font-size: 12px;")
        specs_row.addWidget(spinner_info)

        specs_row.addStretch()
        layout.addLayout(specs_row)

        # Action Button
        btn_load = QPushButton("⚡ Load Template into Editor")
        btn_load.setProperty("class", "btn-primary")
        btn_load.clicked.connect(lambda: self.load_requested.emit(self.template))
        layout.addWidget(btn_load)


class PresetsTab(QWidget):
    """Presets Gallery panel."""

    preset_loaded = pyqtSignal(ThemeProject)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        scroll_layout.setContentsMargins(14, 14, 14, 14)

        header = QLabel("📦 Ready-made Boot Logo Templates")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")
        scroll_layout.addWidget(header)

        sub = QLabel("Select any pre-designed template to immediately load its logo, effects, typography, and color palette.")
        sub.setStyleSheet("color: #94a3b8; font-size: 12px;")
        sub.setWordWrap(True)
        scroll_layout.addWidget(sub)

        templates = get_preset_templates()
        for key, tmpl in templates.items():
            card = PresetCard(key, tmpl)
            card.load_requested.connect(self.preset_loaded.emit)
            scroll_layout.addWidget(card)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
