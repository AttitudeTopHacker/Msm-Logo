"""Interactive real-time Live Preview Panel simulating Linux Plymouth boot & GRUB screens."""

import math
from typing import Optional
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRect, QSize
from PyQt6.QtGui import QPainter, QImage, QPixmap, QColor, QFont, QPen, QBrush, QKeyEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QCheckBox, QFrame, QSizePolicy
)
from PIL import Image
from ..core.models import ThemeProject
from ..core.renderer import BootRenderer


class BootDisplayWidget(QWidget):
    """The central monitor screen rendering the current boot frame."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(480, 270)
        self.current_qimage: Optional[QImage] = None
        self.show_boot_log: bool = False
        self.show_grub_menu: bool = False

    def convert_to_qimage(self, pil_image: Image.Image) -> QImage:
        img_rgba = pil_image if pil_image.mode == "RGBA" else pil_image.convert("RGBA")
        data = img_rgba.tobytes("raw", "RGBA")
        qimg = QImage(data, img_rgba.width, img_rgba.height, QImage.Format.Format_RGBA8888)
        return qimg.copy()

    def set_frame_qimage(self, qimg: QImage):
        self.current_qimage = qimg
        self.update()

    def set_frame_image(self, pil_image: Image.Image):
        qimg = self.convert_to_qimage(pil_image)
        self.set_frame_qimage(qimg)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 1. Bezel / Monitor background
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor("#050811"))

        if not self.current_qimage or self.current_qimage.isNull():
            painter.setPen(QColor("#64748b"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Initializing Live Boot Preview...")
            return

        # 2. Draw scaled frame keeping aspect ratio
        img_w = self.current_qimage.width()
        img_h = self.current_qimage.height()
        scale = min(w / img_w, h / img_h)
        target_w = int(img_w * scale)
        target_h = int(img_h * scale)
        target_x = (w - target_w) // 2
        target_y = (h - target_h) // 2

        target_rect = QRect(target_x, target_y, target_w, target_h)
        painter.drawImage(target_rect, self.current_qimage)

        # Draw monitor bezel subtle inner glow
        painter.setPen(QPen(QColor(56, 189, 248, 60), 2))
        painter.drawRect(target_rect)

        # 3. Simulated Overlay: GRUB Bootloader Menu
        if self.show_grub_menu:
            self._draw_grub_overlay(painter, target_rect)

        # 4. Simulated Overlay: Systemd Boot Log (F2 / Esc mode)
        elif self.show_boot_log:
            self._draw_boot_log_overlay(painter, target_rect)

    def _draw_grub_overlay(self, painter: QPainter, rect: QRect):
        # Semi-transparent dark overlay
        painter.fillRect(rect, QColor(0, 0, 0, 160))

        # GRUB Menu Box
        box_w = int(rect.width() * 0.7)
        box_h = int(rect.height() * 0.5)
        bx = rect.x() + (rect.width() - box_w) // 2
        by = rect.y() + (rect.height() - box_h) // 2

        menu_rect = QRect(bx, by, box_w, box_h)
        painter.fillRect(menu_rect, QColor(15, 23, 42, 230))
        painter.setPen(QPen(QColor(56, 189, 248, 200), 2))
        painter.drawRect(menu_rect)

        # Title
        painter.setFont(QFont("DejaVu Sans", 13, QFont.Weight.Bold))
        painter.setPen(QColor("#38bdf8"))
        painter.drawText(bx + 20, by + 35, "GNU GRUB version 2.12")

        # Menu options
        options = [
            ("* Linux Mint 22 Cinnamon 64-bit", True),
            ("  Advanced options for Linux Mint", False),
            ("  Memory test (memtest86+x64.efi)", False),
            ("  UEFI Firmware Settings", False)
        ]
        painter.setFont(QFont("DejaVu Sans Mono", 11))
        oy = by + 75
        for text, selected in options:
            if selected:
                painter.fillRect(bx + 10, oy - 18, box_w - 20, 26, QColor(2, 132, 199, 180))
                painter.setPen(QColor("#ffffff"))
            else:
                painter.setPen(QColor("#94a3b8"))
            painter.drawText(bx + 25, oy, text)
            oy += 32

        # Footer
        painter.setFont(QFont("DejaVu Sans", 9))
        painter.setPen(QColor("#64748b"))
        painter.drawText(bx + 20, by + box_h - 15, "Use the ^ and v keys to select. Press Enter to boot.")

    def _draw_boot_log_overlay(self, painter: QPainter, rect: QRect):
        painter.setFont(QFont("DejaVu Sans Mono", 9))
        messages = [
            ("[  OK  ] Started Journal Service.", "#10b981"),
            ("[  OK  ] Started udev Kernel Device Manager.", "#10b981"),
            ("[  OK  ] Reached target System Initialization.", "#10b981"),
            ("[  OK  ] Started Disk Manager & LUKS Crypto.", "#10b981"),
            ("[  OK  ] Mounted /home and /boot/efi.", "#10b981"),
            ("[  OK  ] Started Network Time Synchronization.", "#10b981"),
            ("[  OK  ] Reached target Network (Pre).", "#10b981"),
            ("[  OK  ] Started Network Manager.", "#10b981"),
            ("[  OK  ] Reached target Graphical Interface.", "#38bdf8"),
        ]
        y = rect.y() + 25
        for msg, color in messages:
            painter.setPen(QColor(color))
            painter.drawText(rect.x() + 20, y, msg)
            y += 20


class FullscreenPreviewWindow(QWidget):
    """Full-screen immersive boot simulation window. Press Escape or Q to return."""

    closed = pyqtSignal(int, bool)

    def __init__(
        self,
        renderer: BootRenderer,
        fps: int = 30,
        initial_frame: int = 0,
        show_boot_log: bool = False,
        show_grub_menu: bool = False,
        was_playing: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.renderer = renderer
        self.fps = max(1, fps)
        self.frame_idx = initial_frame
        self.was_playing = was_playing

        self.display = BootDisplayWidget(self)
        self.display.show_boot_log = show_boot_log
        self.display.show_grub_menu = show_grub_menu

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.display)

        # Standard preview resolution (960x540) matches warmed background/logo cache for instant 60 FPS rendering
        aspect = self.renderer.project.width / max(1, self.renderer.project.height)
        self.render_w = 960
        self.render_h = max(270, int(self.render_w / aspect))

        # Pre-render the starting frame immediately so fullscreen displays content instantly with zero delay
        initial_img = self.renderer.render_frame(self.frame_idx, self.render_w, self.render_h)
        self.display.set_frame_image(initial_img)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        if self.was_playing:
            self.timer.start(int(1000 / self.fps))

    def _tick(self):
        total_f = max(1, self.renderer.project.total_frames)
        self.frame_idx = (self.frame_idx + 1) % total_f
        img = self.renderer.render_frame(self.frame_idx, self.render_w, self.render_h)
        self.display.set_frame_image(img)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Q):
            self.close()
        elif event.key() == Qt.Key.Key_Space:
            if self.timer.isActive():
                self.timer.stop()
            else:
                self.timer.start(int(1000 / self.fps))
        elif event.key() in (Qt.Key.Key_F2, Qt.Key.Key_Tab):
            self.display.show_boot_log = not self.display.show_boot_log
            if self.display.show_boot_log:
                self.display.show_grub_menu = False
            self.display.update()
        elif event.key() == Qt.Key.Key_F3:
            self.display.show_grub_menu = not self.display.show_grub_menu
            if self.display.show_grub_menu:
                self.display.show_boot_log = False
            self.display.update()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.timer.stop()
        self.closed.emit(self.frame_idx, self.was_playing)
        super().closeEvent(event)


class PreviewPanel(QFrame):
    """Comprehensive Live Preview Panel with Timeline and Control Dock."""

    frame_changed = pyqtSignal(int)

    def __init__(self, project: ThemeProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.renderer = BootRenderer(project)
        self.is_playing = True
        self.current_frame = 0
        self._qimage_cache: dict[int, QImage] = {}
        self.fullscreen_window: Optional[FullscreenPreviewWindow] = None

        self._init_ui()

        # Playback Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer_tick)
        self.start_playback()

    def _init_ui(self):
        self.setObjectName("previewPanel")
        self.setStyleSheet("""
            #previewPanel {
                background-color: #0d1322;
                border: 1px solid #1e293b;
                border-radius: 14px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # Top Control Bar: Header & Screen Toggles
        header_layout = QHBoxLayout()
        title_label = QLabel("🖥️ Live Boot Preview")
        title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #38bdf8;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Checkbox: Simulated Boot Messages (F2)
        self.chk_boot_log = QCheckBox("Kernel Boot Log (F2)")
        self.chk_boot_log.setToolTip("Simulate systemd text logs during boot")
        self.chk_boot_log.toggled.connect(self._toggle_boot_log)
        header_layout.addWidget(self.chk_boot_log)

        # Checkbox: GRUB Preview
        self.chk_grub = QCheckBox("GRUB Menu Preview")
        self.chk_grub.setToolTip("Preview matching GRUB 2.0 selection menu")
        self.chk_grub.toggled.connect(self._toggle_grub)
        header_layout.addWidget(self.chk_grub)

        # Fullscreen Button
        self.btn_fullscreen = QPushButton("⛶ Fullscreen")
        self.btn_fullscreen.setToolTip("Simulate full-screen boot monitor (Press ESC to exit)")
        self.btn_fullscreen.clicked.connect(self._launch_fullscreen)
        header_layout.addWidget(self.btn_fullscreen)

        main_layout.addLayout(header_layout)

        # Center: Monitor Display
        self.display_widget = BootDisplayWidget(self)
        main_layout.addWidget(self.display_widget, stretch=1)

        # Timeline Scrubber Bar
        timeline_layout = QHBoxLayout()
        timeline_layout.setSpacing(8)

        self.btn_play = QPushButton("⏸")
        self.btn_play.setFixedWidth(40)
        self.btn_play.clicked.connect(self.toggle_playback)
        timeline_layout.addWidget(self.btn_play)

        self.btn_rewind = QPushButton("⏮")
        self.btn_rewind.setFixedWidth(36)
        self.btn_rewind.clicked.connect(self.rewind)
        timeline_layout.addWidget(self.btn_rewind)

        self.slider_timeline = QSlider(Qt.Orientation.Horizontal)
        self.slider_timeline.setRange(0, self.project.total_frames - 1)
        self.slider_timeline.setValue(0)
        self.slider_timeline.sliderMoved.connect(self._on_scrub)
        timeline_layout.addWidget(self.slider_timeline)

        self.lbl_time = QLabel("0.0s / 3.0s")
        self.lbl_time.setStyleSheet("color: #94a3b8; font-family: monospace; font-size: 12px;")
        timeline_layout.addWidget(self.lbl_time)

        main_layout.addLayout(timeline_layout)

    def start_playback(self):
        interval_ms = int(1000 / max(1, self.project.fps))
        self.timer.start(interval_ms)
        self.is_playing = True
        self.btn_play.setText("⏸")

    def stop_playback(self):
        self.timer.stop()
        self.is_playing = False
        self.btn_play.setText("▶")

    def toggle_playback(self):
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()

    def rewind(self):
        self.current_frame = 0
        self.slider_timeline.setValue(0)
        self.render_current_frame()

    def set_project(self, project: ThemeProject):
        self.project = project
        self.renderer = BootRenderer(project)
        self.slider_timeline.setRange(0, self.project.total_frames - 1)
        self.render_current_frame()

    def notify_project_changed(self):
        """Called whenever editor settings change to immediately refresh the view."""
        self._qimage_cache.clear()
        self.renderer.invalidate_cache()
        self.slider_timeline.setRange(0, self.project.total_frames - 1)
        self.render_current_frame()

    def _on_timer_tick(self):
        total_f = max(1, self.project.total_frames)
        self.current_frame = (self.current_frame + 1) % total_f
        self.slider_timeline.blockSignals(True)
        self.slider_timeline.setValue(self.current_frame)
        self.slider_timeline.blockSignals(False)
        self.render_current_frame()

    def _on_scrub(self, value: int):
        self.current_frame = value
        self.render_current_frame()

    def render_current_frame(self):
        # Render at preview resolution (720x405 for fast and smooth live preview)
        aspect = self.project.width / max(1, self.project.height)
        render_w = 720
        render_h = max(240, int(render_w / aspect))

        if self.current_frame in self._qimage_cache:
            self.display_widget.set_frame_qimage(self._qimage_cache[self.current_frame])
        else:
            img = self.renderer.render_frame(self.current_frame, render_w, render_h)
            qimg = self.display_widget.convert_to_qimage(img)
            self._qimage_cache[self.current_frame] = qimg
            self.display_widget.set_frame_qimage(qimg)

        # Update time label
        total_f = max(1, self.project.total_frames)
        curr_sec = self.current_frame / float(max(1, self.project.fps))
        total_sec = self.project.duration
        self.lbl_time.setText(f"{curr_sec:04.1f}s / {total_sec:04.1f}s [F {self.current_frame + 1}/{total_f}]")

    def _toggle_boot_log(self, checked: bool):
        self.display_widget.show_boot_log = checked
        if checked:
            self.chk_grub.setChecked(False)
        self.display_widget.update()

    def _toggle_grub(self, checked: bool):
        self.display_widget.show_grub_menu = checked
        if checked:
            self.chk_boot_log.setChecked(False)
        self.display_widget.update()

    def _launch_fullscreen(self):
        if self.fullscreen_window and self.fullscreen_window.isVisible():
            self.fullscreen_window.raise_()
            self.fullscreen_window.activateWindow()
            return

        # Pause preview panel playback to prevent background CPU usage and timer contention
        was_playing = self.is_playing
        self.stop_playback()

        self.fullscreen_window = FullscreenPreviewWindow(
            renderer=self.renderer,
            fps=self.project.fps,
            initial_frame=self.current_frame,
            show_boot_log=self.display_widget.show_boot_log,
            show_grub_menu=self.display_widget.show_grub_menu,
            was_playing=was_playing,
            parent=None,
        )
        self.fullscreen_window.closed.connect(self._on_fullscreen_closed)
        self.fullscreen_window.showFullScreen()

    def _on_fullscreen_closed(self, last_frame: int, was_playing: bool):
        self.current_frame = last_frame
        self.slider_timeline.blockSignals(True)
        self.slider_timeline.setValue(self.current_frame)
        self.slider_timeline.blockSignals(False)
        self.render_current_frame()
        if was_playing:
            self.start_playback()
        self.fullscreen_window = None
