"""Animation and Visual Effects Configuration Tab."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QCheckBox, QGroupBox, QColorDialog,
    QScrollArea, QFrame, QDoubleSpinBox
)
from ..core.models import ThemeProject


class EffectsTab(QWidget):
    """Animation and visual effects customization panel."""

    effects_modified = pyqtSignal()

    def __init__(self, project: ThemeProject, parent=None):
        super().__init__(parent)
        self.project = project
        self._init_ui()
        self.load_values()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        scroll_layout.setContentsMargins(12, 12, 12, 12)

        # 1. Shimmer Beam Effect
        scroll_layout.addWidget(self._create_shimmer_group())

        # 2. Pulse Glow Aura
        scroll_layout.addWidget(self._create_glow_group())

        # 3. Boot Spinner / Throbber
        scroll_layout.addWidget(self._create_spinner_group())

        # 4. Transitions & Motion
        scroll_layout.addWidget(self._create_motion_group())

        # 5. Speed, FPS & Frame Rate Controller
        scroll_layout.addWidget(self._create_timing_group())

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def _create_shimmer_group(self) -> QGroupBox:
        grp = QGroupBox("✨ Shimmer & Light Sweep Effect")
        layout = QVBoxLayout(grp)

        self.chk_shimmer = QCheckBox("Enable Shimmer Light Reflection Sweep")
        self.chk_shimmer.toggled.connect(self._on_shimmer_toggled)
        layout.addWidget(self.chk_shimmer)

        color_row = QHBoxLayout()
        self.btn_shimmer_color = QPushButton("Shimmer Color")
        self.btn_shimmer_color.clicked.connect(self._pick_shimmer_color)
        color_row.addWidget(self.btn_shimmer_color)

        color_row.addWidget(QLabel("Angle:"))
        self.slider_shimmer_angle = QSlider(Qt.Orientation.Horizontal)
        self.slider_shimmer_angle.setRange(0, 90)
        self.slider_shimmer_angle.valueChanged.connect(self._on_shimmer_angle_changed)
        color_row.addWidget(self.slider_shimmer_angle)
        self.lbl_shimmer_angle = QLabel("45°")
        color_row.addWidget(self.lbl_shimmer_angle)
        layout.addLayout(color_row)

        intensity_row = QHBoxLayout()
        intensity_row.addWidget(QLabel("Intensity:"))
        self.slider_shimmer_intensity = QSlider(Qt.Orientation.Horizontal)
        self.slider_shimmer_intensity.setRange(0, 100)
        self.slider_shimmer_intensity.valueChanged.connect(self._on_shimmer_intensity_changed)
        intensity_row.addWidget(self.slider_shimmer_intensity)
        self.lbl_shimmer_intensity = QLabel("85%")
        intensity_row.addWidget(self.lbl_shimmer_intensity)
        layout.addLayout(intensity_row)

        width_row = QHBoxLayout()
        width_row.addWidget(QLabel("Beam Width:"))
        self.slider_shimmer_width = QSlider(Qt.Orientation.Horizontal)
        self.slider_shimmer_width.setRange(10, 60)
        self.slider_shimmer_width.valueChanged.connect(self._on_shimmer_width_changed)
        width_row.addWidget(self.slider_shimmer_width)
        self.lbl_shimmer_width = QLabel("25%")
        width_row.addWidget(self.lbl_shimmer_width)
        layout.addLayout(width_row)

        return grp

    def _create_glow_group(self) -> QGroupBox:
        grp = QGroupBox("🌟 Pulse Glow Aura")
        layout = QVBoxLayout(grp)

        self.chk_glow = QCheckBox("Enable Breathing Glow Aura")
        self.chk_glow.toggled.connect(self._on_glow_toggled)
        layout.addWidget(self.chk_glow)

        row = QHBoxLayout()
        self.btn_glow_color = QPushButton("Glow Color")
        self.btn_glow_color.clicked.connect(self._pick_glow_color)
        row.addWidget(self.btn_glow_color)

        row.addWidget(QLabel("Radius:"))
        self.slider_glow_radius = QSlider(Qt.Orientation.Horizontal)
        self.slider_glow_radius.setRange(5, 70)
        self.slider_glow_radius.valueChanged.connect(self._on_glow_radius_changed)
        row.addWidget(self.slider_glow_radius)
        self.lbl_glow_radius = QLabel("36px")
        row.addWidget(self.lbl_glow_radius)
        layout.addLayout(row)

        return grp

    def _create_spinner_group(self) -> QGroupBox:
        grp = QGroupBox("🔄 Boot Spinner / Throbber")
        layout = QVBoxLayout(grp)

        self.chk_spinner = QCheckBox("Enable Boot Loading Spinner")
        self.chk_spinner.toggled.connect(self._on_spinner_toggled)
        layout.addWidget(self.chk_spinner)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Spinner Style:"))
        self.combo_spinner_type = QComboBox()
        self.combo_spinner_type.addItems(["Sleek Arc (arc)", "Orbiting Dots (dots)", "Segmented Ring (ring)", "Dual Rings (dual_ring)"])
        self.combo_spinner_type.currentIndexChanged.connect(self._on_spinner_type_changed)
        type_row.addWidget(self.combo_spinner_type, stretch=1)
        layout.addLayout(type_row)

        color_row = QHBoxLayout()
        self.btn_spinner_c1 = QPushButton("Primary Color")
        self.btn_spinner_c1.clicked.connect(lambda: self._pick_spinner_color(1))
        color_row.addWidget(self.btn_spinner_c1)

        self.btn_spinner_c2 = QPushButton("Secondary Color")
        self.btn_spinner_c2.clicked.connect(lambda: self._pick_spinner_color(2))
        color_row.addWidget(self.btn_spinner_c2)
        layout.addLayout(color_row)

        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Size:"))
        self.slider_spinner_size = QSlider(Qt.Orientation.Horizontal)
        self.slider_spinner_size.setRange(24, 120)
        self.slider_spinner_size.valueChanged.connect(self._on_spinner_size_changed)
        size_row.addWidget(self.slider_spinner_size)
        self.lbl_spinner_size = QLabel("60px")
        size_row.addWidget(self.lbl_spinner_size)
        layout.addLayout(size_row)

        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Vertical Offset Y:"))
        self.slider_spinner_y = QSlider(Qt.Orientation.Horizontal)
        self.slider_spinner_y.setRange(50, 450)
        self.slider_spinner_y.valueChanged.connect(self._on_spinner_y_changed)
        pos_row.addWidget(self.slider_spinner_y)
        self.lbl_spinner_y = QLabel("220px")
        pos_row.addWidget(self.lbl_spinner_y)
        layout.addLayout(pos_row)

        return grp

    def _create_motion_group(self) -> QGroupBox:
        grp = QGroupBox("🌀 Motion & Transitions")
        layout = QVBoxLayout(grp)

        zoom_row = QHBoxLayout()
        zoom_row.addWidget(QLabel("Scale Motion:"))
        self.combo_zoom = QComboBox()
        self.combo_zoom.addItems(["Breathing Pulse (breathe)", "Gentle Zoom In (zoom_in)", "Static / None (none)"])
        self.combo_zoom.currentIndexChanged.connect(self._on_zoom_changed)
        zoom_row.addWidget(self.combo_zoom, stretch=1)
        layout.addLayout(zoom_row)

        fade_row = QHBoxLayout()
        self.chk_fade_in = QCheckBox("Fade In")
        self.chk_fade_in.toggled.connect(self._on_fade_toggled)
        fade_row.addWidget(self.chk_fade_in)

        self.chk_fade_out = QCheckBox("Fade Out")
        self.chk_fade_out.toggled.connect(self._on_fade_toggled)
        fade_row.addWidget(self.chk_fade_out)
        layout.addLayout(fade_row)

        return grp

    def _create_timing_group(self) -> QGroupBox:
        grp = QGroupBox("⏱️ Speed & Frame Rate Controller")
        layout = QVBoxLayout(grp)

        row = QHBoxLayout()
        row.addWidget(QLabel("Frame Rate (FPS):"))
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["30 FPS (Recommended)", "60 FPS (Ultra Smooth)", "24 FPS (Cinematic)", "15 FPS (Lightweight)"])
        self.combo_fps.currentIndexChanged.connect(self._on_fps_changed)
        row.addWidget(self.combo_fps)

        row.addWidget(QLabel("Loop Duration:"))
        self.combo_duration = QComboBox()
        self.combo_duration.addItems(["3.0 Seconds", "2.0 Seconds", "4.0 Seconds", "5.0 Seconds"])
        self.combo_duration.currentIndexChanged.connect(self._on_duration_changed)
        row.addWidget(self.combo_duration)
        layout.addLayout(row)

        engine_row = QHBoxLayout()
        engine_row.addWidget(QLabel("Boot Engine Architecture:"))
        self.combo_engine = QComboBox()
        self.combo_engine.addItems([
            "⚡ Auto (Optimal Smooth Layered - Zero Lag)",
            "🎬 Cinematic Script Engine (Rich Shimmer/Glow)",
            "🛡️ Native Two-Step OEM (Stock Mint/Ubuntu Standard)"
        ])
        self.combo_engine.currentIndexChanged.connect(self._on_engine_changed)
        engine_row.addWidget(self.combo_engine)
        layout.addLayout(engine_row)

        self.lbl_frame_info = QLabel("Total: 90 frames rendered per loop")
        self.lbl_frame_info.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.lbl_frame_info)

        return grp

    def load_values(self):
        eff = self.project.effects
        # Shimmer
        self.chk_shimmer.setChecked(eff.shimmer_enabled)
        self.slider_shimmer_angle.setValue(int(eff.shimmer_angle))
        self.lbl_shimmer_angle.setText(f"{int(eff.shimmer_angle)}°")
        self.slider_shimmer_intensity.setValue(int(eff.shimmer_intensity * 100))
        self.lbl_shimmer_intensity.setText(f"{int(eff.shimmer_intensity * 100)}%")
        self.slider_shimmer_width.setValue(int(eff.shimmer_width * 100))
        self.lbl_shimmer_width.setText(f"{int(eff.shimmer_width * 100)}%")
        self._update_color_button(self.btn_shimmer_color, eff.shimmer_color)

        # Glow
        self.chk_glow.setChecked(eff.glow_pulse_enabled)
        self.slider_glow_radius.setValue(eff.glow_radius)
        self.lbl_glow_radius.setText(f"{eff.glow_radius}px")
        self._update_color_button(self.btn_glow_color, eff.glow_color)

        # Spinner
        self.chk_spinner.setChecked(eff.spinner_enabled)
        spinner_types = {"arc": 0, "dots": 1, "ring": 2, "dual_ring": 3}
        self.combo_spinner_type.setCurrentIndex(spinner_types.get(eff.spinner_type, 0))
        self.slider_spinner_size.setValue(eff.spinner_size)
        self.lbl_spinner_size.setText(f"{eff.spinner_size}px")
        self.slider_spinner_y.setValue(eff.spinner_offset_y)
        self.lbl_spinner_y.setText(f"{eff.spinner_offset_y}px")
        self._update_color_button(self.btn_spinner_c1, eff.spinner_color)
        self._update_color_button(self.btn_spinner_c2, eff.spinner_secondary_color)

        # Motion
        zoom_map = {"breathe": 0, "zoom_in": 1, "none": 2}
        self.combo_zoom.setCurrentIndex(zoom_map.get(eff.zoom_effect, 0))
        self.chk_fade_in.setChecked(eff.fade_in)
        self.chk_fade_out.setChecked(eff.fade_out)

        # Timing
        fps_map = {30: 0, 60: 1, 24: 2, 15: 3}
        self.combo_fps.setCurrentIndex(fps_map.get(self.project.fps, 0))
        dur_map = {3.0: 0, 2.0: 1, 4.0: 2, 5.0: 3}
        self.combo_duration.setCurrentIndex(dur_map.get(self.project.duration, 0))

        engine_map = {"auto": 0, "script": 1, "two-step": 2}
        self.combo_engine.setCurrentIndex(engine_map.get(getattr(self.project, "plymouth_module", "auto"), 0))
        self._update_frame_info()

    def _on_engine_changed(self, idx: int):
        engines = ["auto", "script", "two-step"]
        self.project.plymouth_module = engines[idx]
        self.effects_modified.emit()

    def _update_color_button(self, btn: QPushButton, hex_color: str):
        btn.setStyleSheet(f"background-color: {hex_color}; color: {'#000' if hex_color.lower() in ['#ffffff', '#f8fafc', '#fed7aa', '#a3e635'] else '#fff'}; border: 1px solid #64748b; font-weight: bold;")
        btn.setText(hex_color)

    def _update_frame_info(self):
        f = self.project.total_frames
        self.lbl_frame_info.setText(f"Total: {f} frames rendered per loop ({self.project.fps} FPS × {self.project.duration}s)")

    def _on_shimmer_toggled(self, checked: bool):
        self.project.effects.shimmer_enabled = checked
        self.effects_modified.emit()

    def _on_shimmer_angle_changed(self, val: int):
        self.project.effects.shimmer_angle = float(val)
        self.lbl_shimmer_angle.setText(f"{val}°")
        self.effects_modified.emit()

    def _on_shimmer_intensity_changed(self, val: int):
        self.project.effects.shimmer_intensity = val / 100.0
        self.lbl_shimmer_intensity.setText(f"{val}%")
        self.effects_modified.emit()

    def _on_shimmer_width_changed(self, val: int):
        self.project.effects.shimmer_width = val / 100.0
        self.lbl_shimmer_width.setText(f"{val}%")
        self.effects_modified.emit()

    def _pick_shimmer_color(self):
        col = QColorDialog.getColor(QColor(self.project.effects.shimmer_color), self, "Select Shimmer Color")
        if col.isValid():
            self.project.effects.shimmer_color = col.name()
            self._update_color_button(self.btn_shimmer_color, col.name())
            self.effects_modified.emit()

    def _on_glow_toggled(self, checked: bool):
        self.project.effects.glow_pulse_enabled = checked
        self.effects_modified.emit()

    def _on_glow_radius_changed(self, val: int):
        self.project.effects.glow_radius = val
        self.lbl_glow_radius.setText(f"{val}px")
        self.effects_modified.emit()

    def _pick_glow_color(self):
        col = QColorDialog.getColor(QColor(self.project.effects.glow_color), self, "Select Glow Color")
        if col.isValid():
            self.project.effects.glow_color = col.name()
            self._update_color_button(self.btn_glow_color, col.name())
            self.effects_modified.emit()

    def _on_spinner_toggled(self, checked: bool):
        self.project.effects.spinner_enabled = checked
        self.effects_modified.emit()

    def _on_spinner_type_changed(self, idx: int):
        types = ["arc", "dots", "ring", "dual_ring"]
        self.project.effects.spinner_type = types[idx]
        self.effects_modified.emit()

    def _on_spinner_size_changed(self, val: int):
        self.project.effects.spinner_size = val
        self.lbl_spinner_size.setText(f"{val}px")
        self.effects_modified.emit()

    def _on_spinner_y_changed(self, val: int):
        self.project.effects.spinner_offset_y = val
        self.lbl_spinner_y.setText(f"{val}px")
        self.effects_modified.emit()

    def _pick_spinner_color(self, index: int):
        curr = self.project.effects.spinner_color if index == 1 else self.project.effects.spinner_secondary_color
        col = QColorDialog.getColor(QColor(curr), self, f"Select Spinner Color {index}")
        if col.isValid():
            if index == 1:
                self.project.effects.spinner_color = col.name()
                self._update_color_button(self.btn_spinner_c1, col.name())
            else:
                self.project.effects.spinner_secondary_color = col.name()
                self._update_color_button(self.btn_spinner_c2, col.name())
            self.effects_modified.emit()

    def _on_zoom_changed(self, idx: int):
        zooms = ["breathe", "zoom_in", "none"]
        self.project.effects.zoom_effect = zooms[idx]
        self.effects_modified.emit()

    def _on_fade_toggled(self):
        self.project.effects.fade_in = self.chk_fade_in.isChecked()
        self.project.effects.fade_out = self.chk_fade_out.isChecked()
        self.effects_modified.emit()

    def _on_fps_changed(self, idx: int):
        fps_values = [30, 60, 24, 15]
        self.project.fps = fps_values[idx]
        self._update_frame_info()
        self.effects_modified.emit()

    def _on_duration_changed(self, idx: int):
        durations = [3.0, 2.0, 4.0, 5.0]
        self.project.duration = durations[idx]
        self._update_frame_info()
        self.effects_modified.emit()
