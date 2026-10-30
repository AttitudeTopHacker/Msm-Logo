"""Logo, Text, Canvas and Background Design Editor Tab."""

import os
from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFontDatabase
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSlider, QComboBox, QCheckBox, QGroupBox,
    QFileDialog, QColorDialog, QScrollArea, QFrame, QSpinBox
)
from ..core.models import ThemeProject, TextItem
from ..core.system_manager import SystemManager

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))
SAMPLES_DIR = os.path.join(ASSETS_DIR, "samples")


class EditorTab(QWidget):
    """Design and Layout editor for logo, typography, and canvas properties."""

    project_modified = pyqtSignal()

    def __init__(self, project: ThemeProject, parent=None):
        super().__init__(parent)
        self.project = project
        self._init_ui()
        self.load_project_values()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area for comfortable layout on any screen size
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        scroll_layout.setContentsMargins(12, 12, 12, 12)

        # 1. Canvas & Resolution Section
        scroll_layout.addWidget(self._create_canvas_group())

        # 2. Logo Emblem Section
        scroll_layout.addWidget(self._create_logo_group())

        # 3. Typography & Texts Section
        scroll_layout.addWidget(self._create_text_group())

        # 4. Background Section
        scroll_layout.addWidget(self._create_bg_group())

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def _create_canvas_group(self) -> QGroupBox:
        grp = QGroupBox("📐 Resolution & Aspect Ratio")
        layout = QVBoxLayout(grp)

        row = QHBoxLayout()
        row.addWidget(QLabel("Preset Resolution:"))
        self.combo_resolution = QComboBox()

        dw, dh = SystemManager.get_display_resolution()
        candidates = [
            (f"Detected Display ({dw}x{dh}) [Recommended]", dw, dh),
            ("1080p Full HD (1920x1080) - 16:9", 1920, 1080),
            ("720p HD (1280x720) - 16:9", 1280, 720),
            ("16:10 Laptop (1920x1200)", 1920, 1200),
            ("4K UHD (3840x2160) - 16:9", 3840, 2160),
            ("Custom", None, None),
        ]
        seen = set()
        self.preset_resolutions = []
        for label, w, h in candidates:
            if w is not None and (w, h) in seen:
                continue
            if w is not None:
                seen.add((w, h))
            self.preset_resolutions.append((label, w, h))

        for label, _, _ in self.preset_resolutions:
            self.combo_resolution.addItem(label)

        self.combo_resolution.currentIndexChanged.connect(self._on_resolution_changed)
        row.addWidget(self.combo_resolution, stretch=1)
        layout.addLayout(row)

        dim_row = QHBoxLayout()
        dim_row.addWidget(QLabel("Width:"))
        self.spin_width = QSpinBox()
        self.spin_width.setRange(640, 7680)
        self.spin_width.setValue(self.project.width)
        self.spin_width.valueChanged.connect(self._on_dim_changed)
        dim_row.addWidget(self.spin_width)

        dim_row.addWidget(QLabel("Height:"))
        self.spin_height = QSpinBox()
        self.spin_height.setRange(480, 4320)
        self.spin_height.setValue(self.project.height)
        self.spin_height.valueChanged.connect(self._on_dim_changed)
        dim_row.addWidget(self.spin_height)
        layout.addLayout(dim_row)

        return grp

    def _create_logo_group(self) -> QGroupBox:
        grp = QGroupBox("🎨 Logo & Emblem (PNG / SVG)")
        layout = QVBoxLayout(grp)

        # Upload / Browse Row
        btn_row = QHBoxLayout()
        self.btn_import_logo = QPushButton("📁 Import Custom Image (PNG/SVG)")
        self.btn_import_logo.clicked.connect(self._browse_logo)
        btn_row.addWidget(self.btn_import_logo)
        layout.addLayout(btn_row)

        # Quick Preset Emblems
        quick_lbl = QLabel("Or choose sample emblem:")
        quick_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(quick_lbl)

        sample_row = QHBoxLayout()
        for label, filename in [("Mint", "mint_emblem.png"), ("Ubuntu", "ubuntu_emblem.png"), ("Cyber", "cyber_emblem.png"), ("Power Ring", "minimal_power.png")]:
            btn = QPushButton(label)
            btn.setStyleSheet("padding: 4px 10px; font-size: 11px;")
            btn.clicked.connect(lambda checked, fn=filename: self._select_sample_logo(fn))
            sample_row.addWidget(btn)
        layout.addLayout(sample_row)

        # Scale Slider
        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("Scale:"))
        self.slider_logo_scale = QSlider(Qt.Orientation.Horizontal)
        self.slider_logo_scale.setRange(10, 80)
        self.slider_logo_scale.setValue(int(self.project.logo_scale * 100))
        self.slider_logo_scale.valueChanged.connect(self._on_logo_scale_changed)
        scale_row.addWidget(self.slider_logo_scale)
        self.lbl_logo_scale = QLabel(f"{int(self.project.logo_scale * 100)}%")
        self.lbl_logo_scale.setFixedWidth(40)
        scale_row.addWidget(self.lbl_logo_scale)
        layout.addLayout(scale_row)

        # Offset Y Slider
        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Vertical Offset Y:"))
        self.slider_logo_y = QSlider(Qt.Orientation.Horizontal)
        self.slider_logo_y.setRange(-300, 300)
        self.slider_logo_y.setValue(self.project.logo_offset_y)
        self.slider_logo_y.valueChanged.connect(self._on_logo_y_changed)
        pos_row.addWidget(self.slider_logo_y)
        self.lbl_logo_y = QLabel(f"{self.project.logo_offset_y}px")
        self.lbl_logo_y.setFixedWidth(45)
        pos_row.addWidget(self.lbl_logo_y)
        layout.addLayout(pos_row)

        return grp

    def _create_text_group(self) -> QGroupBox:
        grp = QGroupBox("✍️ Typography & Titles")
        layout = QVBoxLayout(grp)

        # Title Text Row
        layout.addWidget(QLabel("Primary Title / OS Name:"))
        self.txt_title = QLineEdit()
        self.txt_title.textChanged.connect(self._on_title_changed)
        layout.addWidget(self.txt_title)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Font:"))
        self.combo_font = QComboBox()
        # Scan system font families
        families = ["DejaVu Sans", "Liberation Sans", "Nimbus Sans", "FreeSans", "Ubuntu"]
        for f in QFontDatabase.families():
            if f not in families:
                families.append(f)
        self.combo_font.addItems(families[:30])
        self.combo_font.currentTextChanged.connect(self._on_font_changed)
        font_row.addWidget(self.combo_font, stretch=1)

        self.chk_bold = QCheckBox("Bold")
        self.chk_bold.toggled.connect(self._on_bold_toggled)
        font_row.addWidget(self.chk_bold)
        layout.addLayout(font_row)

        # Title Color & Glow
        color_row = QHBoxLayout()
        self.btn_title_color = QPushButton("Color")
        self.btn_title_color.clicked.connect(self._pick_title_color)
        color_row.addWidget(self.btn_title_color)

        self.chk_glow = QCheckBox("Luminous Glow")
        self.chk_glow.toggled.connect(self._on_glow_toggled)
        color_row.addWidget(self.chk_glow)

        self.btn_glow_color = QPushButton("Glow Color")
        self.btn_glow_color.clicked.connect(self._pick_glow_color)
        color_row.addWidget(self.btn_glow_color)
        layout.addLayout(color_row)

        # Title Size & Offset
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Size:"))
        self.slider_title_size = QSlider(Qt.Orientation.Horizontal)
        self.slider_title_size.setRange(16, 96)
        self.slider_title_size.valueChanged.connect(self._on_title_size_changed)
        size_row.addWidget(self.slider_title_size)

        size_row.addWidget(QLabel("Offset Y:"))
        self.slider_title_y = QSlider(Qt.Orientation.Horizontal)
        self.slider_title_y.setRange(0, 400)
        self.slider_title_y.valueChanged.connect(self._on_title_y_changed)
        size_row.addWidget(self.slider_title_y)
        layout.addLayout(size_row)

        # Subtitle Section
        layout.addWidget(QLabel("Tagline / Subtitle:"))
        self.txt_subtitle = QLineEdit()
        self.txt_subtitle.textChanged.connect(self._on_subtitle_changed)
        layout.addWidget(self.txt_subtitle)

        sub_row = QHBoxLayout()
        self.btn_subtitle_color = QPushButton("Subtitle Color")
        self.btn_subtitle_color.clicked.connect(self._pick_subtitle_color)
        sub_row.addWidget(self.btn_subtitle_color)

        sub_row.addWidget(QLabel("Size:"))
        self.slider_subtitle_size = QSlider(Qt.Orientation.Horizontal)
        self.slider_subtitle_size.setRange(12, 48)
        self.slider_subtitle_size.valueChanged.connect(self._on_subtitle_size_changed)
        sub_row.addWidget(self.slider_subtitle_size)
        layout.addLayout(sub_row)

        return grp

    def _create_bg_group(self) -> QGroupBox:
        grp = QGroupBox("🌌 Background & GRUB Sync")
        layout = QVBoxLayout(grp)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Background Style:"))
        self.combo_bg_style = QComboBox()
        self.combo_bg_style.addItems(["Radial Spotlight Vignette", "Vertical Gradient", "Solid Dark Color", "Custom Wallpaper Image"])
        self.combo_bg_style.currentIndexChanged.connect(self._on_bg_style_changed)
        mode_row.addWidget(self.combo_bg_style, stretch=1)
        layout.addLayout(mode_row)

        color_row = QHBoxLayout()
        self.btn_bg_c1 = QPushButton("Center / Top Color")
        self.btn_bg_c1.clicked.connect(lambda: self._pick_bg_color(1))
        color_row.addWidget(self.btn_bg_c1)

        self.btn_bg_c2 = QPushButton("Edge / Bottom Color")
        self.btn_bg_c2.clicked.connect(lambda: self._pick_bg_color(2))
        color_row.addWidget(self.btn_bg_c2)
        layout.addLayout(color_row)

        self.btn_bg_img = QPushButton("🖼️ Choose Custom Wallpaper Image")
        self.btn_bg_img.clicked.connect(self._browse_bg_image)
        layout.addWidget(self.btn_bg_img)

        self.chk_sync_grub = QCheckBox("Sync with GRUB Background (1-Click GRUB Theme)")
        self.chk_sync_grub.setChecked(self.project.sync_grub)
        self.chk_sync_grub.toggled.connect(self._on_sync_grub_toggled)
        layout.addWidget(self.chk_sync_grub)

        return grp

    def load_project_values(self):
        # Canvas
        self.spin_width.blockSignals(True)
        self.spin_height.blockSignals(True)
        self.spin_width.setValue(self.project.width)
        self.spin_height.setValue(self.project.height)
        self.spin_width.blockSignals(False)
        self.spin_height.blockSignals(False)

        matched = False
        for idx, (_, w, h) in enumerate(self.preset_resolutions):
            if w == self.project.width and h == self.project.height:
                self.combo_resolution.blockSignals(True)
                self.combo_resolution.setCurrentIndex(idx)
                self.combo_resolution.blockSignals(False)
                matched = True
                break
        if not matched:
            self.combo_resolution.blockSignals(True)
            self.combo_resolution.setCurrentIndex(len(self.preset_resolutions) - 1)
            self.combo_resolution.blockSignals(False)

        # Logo
        self.slider_logo_scale.setValue(int(self.project.logo_scale * 100))
        self.lbl_logo_scale.setText(f"{int(self.project.logo_scale * 100)}%")
        self.slider_logo_y.setValue(self.project.logo_offset_y)
        self.lbl_logo_y.setText(f"{self.project.logo_offset_y}px")

        # Texts
        if len(self.project.texts) > 0:
            t1 = self.project.texts[0]
            self.txt_title.setText(t1.text)
            self.combo_font.setCurrentText(t1.font_family)
            self.chk_bold.setChecked(t1.is_bold)
            self.chk_glow.setChecked(t1.glow_enabled)
            self.slider_title_size.setValue(t1.font_size)
            self.slider_title_y.setValue(t1.offset_y)
            self._update_color_button(self.btn_title_color, t1.color)
            self._update_color_button(self.btn_glow_color, t1.glow_color)

        if len(self.project.texts) > 1:
            t2 = self.project.texts[1]
            self.txt_subtitle.setText(t2.text)
            self.slider_subtitle_size.setValue(t2.font_size)
            self._update_color_button(self.btn_subtitle_color, t2.color)

        # Background
        self._update_color_button(self.btn_bg_c1, self.project.bg_color_1)
        self._update_color_button(self.btn_bg_c2, self.project.bg_color_2)
        style_idx = {"gradient_radial": 0, "gradient_linear": 1, "solid": 2, "image": 3}.get(self.project.bg_type, 0)
        self.combo_bg_style.setCurrentIndex(style_idx)
        self.chk_sync_grub.setChecked(self.project.sync_grub)

    def _update_color_button(self, btn: QPushButton, hex_color: str):
        btn.setStyleSheet(f"background-color: {hex_color}; color: {'#000' if hex_color.lower() in ['#ffffff', '#f8fafc', '#fed7aa', '#a3e635'] else '#fff'}; border: 1px solid #64748b; font-weight: bold;")
        btn.setText(hex_color)

    def _on_resolution_changed(self, idx: int):
        if 0 <= idx < len(self.preset_resolutions):
            _, w, h = self.preset_resolutions[idx]
            if w is not None and h is not None:
                self.spin_width.blockSignals(True)
                self.spin_height.blockSignals(True)
                self.spin_width.setValue(w)
                self.spin_height.setValue(h)
                self.spin_width.blockSignals(False)
                self.spin_height.blockSignals(False)
                self.project.width = w
                self.project.height = h
                self.project_modified.emit()

    def _on_dim_changed(self):
        self.project.width = self.spin_width.value()
        self.project.height = self.spin_height.value()
        matched = False
        for idx, (_, w, h) in enumerate(self.preset_resolutions):
            if w == self.project.width and h == self.project.height:
                self.combo_resolution.blockSignals(True)
                self.combo_resolution.setCurrentIndex(idx)
                self.combo_resolution.blockSignals(False)
                matched = True
                break
        if not matched:
            self.combo_resolution.blockSignals(True)
            self.combo_resolution.setCurrentIndex(len(self.preset_resolutions) - 1)
            self.combo_resolution.blockSignals(False)
        self.project_modified.emit()

    def _browse_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Logo Image", "", "Image Files (*.png *.svg *.jpg *.jpeg *.webp)")
        if path:
            self.project.logo_path = path
            self.project_modified.emit()

    def _select_sample_logo(self, filename: str):
        sample_path = os.path.join(SAMPLES_DIR, filename)
        if os.path.exists(sample_path):
            self.project.logo_path = sample_path
            self.project_modified.emit()

    def _on_logo_scale_changed(self, val: int):
        self.project.logo_scale = val / 100.0
        self.lbl_logo_scale.setText(f"{val}%")
        self.project_modified.emit()

    def _on_logo_y_changed(self, val: int):
        self.project.logo_offset_y = val
        self.lbl_logo_y.setText(f"{val}px")
        self.project_modified.emit()

    def _on_title_changed(self, text: str):
        if len(self.project.texts) > 0:
            self.project.texts[0].text = text
            self.project_modified.emit()

    def _on_font_changed(self, font_name: str):
        if len(self.project.texts) > 0:
            self.project.texts[0].font_family = font_name
            self.project_modified.emit()

    def _on_bold_toggled(self, checked: bool):
        if len(self.project.texts) > 0:
            self.project.texts[0].is_bold = checked
            self.project_modified.emit()

    def _on_glow_toggled(self, checked: bool):
        if len(self.project.texts) > 0:
            self.project.texts[0].glow_enabled = checked
            self.project_modified.emit()

    def _on_title_size_changed(self, val: int):
        if len(self.project.texts) > 0:
            self.project.texts[0].font_size = val
            self.project_modified.emit()

    def _on_title_y_changed(self, val: int):
        if len(self.project.texts) > 0:
            self.project.texts[0].offset_y = val
            self.project_modified.emit()

    def _pick_title_color(self):
        col = QColorDialog.getColor(QColor(self.project.texts[0].color), self, "Select Title Color")
        if col.isValid():
            self.project.texts[0].color = col.name()
            self._update_color_button(self.btn_title_color, col.name())
            self.project_modified.emit()

    def _pick_glow_color(self):
        col = QColorDialog.getColor(QColor(self.project.texts[0].glow_color), self, "Select Glow Color")
        if col.isValid():
            self.project.texts[0].glow_color = col.name()
            self._update_color_button(self.btn_glow_color, col.name())
            self.project_modified.emit()

    def _on_subtitle_changed(self, text: str):
        if len(self.project.texts) > 1:
            self.project.texts[1].text = text
            self.project_modified.emit()

    def _on_subtitle_size_changed(self, val: int):
        if len(self.project.texts) > 1:
            self.project.texts[1].font_size = val
            self.project_modified.emit()

    def _pick_subtitle_color(self):
        col = QColorDialog.getColor(QColor(self.project.texts[1].color), self, "Select Subtitle Color")
        if col.isValid():
            self.project.texts[1].color = col.name()
            self._update_color_button(self.btn_subtitle_color, col.name())
            self.project_modified.emit()

    def _on_bg_style_changed(self, idx: int):
        mapping = {0: "gradient_radial", 1: "gradient_linear", 2: "solid", 3: "image"}
        self.project.bg_type = mapping.get(idx, "gradient_radial")
        self.project_modified.emit()

    def _pick_bg_color(self, index: int):
        curr = self.project.bg_color_1 if index == 1 else self.project.bg_color_2
        col = QColorDialog.getColor(QColor(curr), self, f"Select Background Color {index}")
        if col.isValid():
            if index == 1:
                self.project.bg_color_1 = col.name()
                self._update_color_button(self.btn_bg_c1, col.name())
            else:
                self.project.bg_color_2 = col.name()
                self._update_color_button(self.btn_bg_c2, col.name())
            self.project_modified.emit()

    def _browse_bg_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Background Wallpaper", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if path:
            self.project.bg_image_path = path
            self.combo_bg_style.setCurrentIndex(3)
            self.project.bg_type = "image"
            self.project_modified.emit()

    def _on_sync_grub_toggled(self, checked: bool):
        self.project.sync_grub = checked
        self.project_modified.emit()
