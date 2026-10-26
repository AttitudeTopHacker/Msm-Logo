"""1-Click System Theme Installer Modal Dialog with live progress and log terminal."""

import os
import shutil
import tempfile
from typing import Optional
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QFrame
)
from ..core.models import ThemeProject
from ..core.plymouth_generator import PlymouthGenerator
from ..core.system_manager import ApplyWorker


class RenderThread(QThread):
    progress_signal = pyqtSignal(int, int, str)
    completed_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, project: ThemeProject, staging_base_dir: str):
        super().__init__()
        self.project = project
        self.staging_base_dir = staging_base_dir

    def run(self):
        try:
            generator = PlymouthGenerator(self.project)
            theme_dir = generator.generate_theme(
                self.staging_base_dir,
                progress_callback=lambda cur, tot, msg: self.progress_signal.emit(cur, tot, msg)
            )
            self.completed_signal.emit(theme_dir)
        except Exception as e:
            self.error_signal.emit(str(e))


class ApplyDialog(QDialog):
    """Progress & authorization dialog for applying Plymouth boot theme and updating initramfs."""

    def __init__(self, project: ThemeProject, parent=None):
        super().__init__(parent)
        self.project = project
        self.staging_dir = os.path.expanduser("~/.local/share/msmlogo/staging")
        os.makedirs(self.staging_dir, exist_ok=True)
        self.worker: Optional[ApplyWorker] = None
        self.render_thread: Optional[RenderThread] = None
        self.is_finished = False

        self.setWindowTitle("Applying Boot Logo to System")
        self.setMinimumSize(560, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._init_ui()
        self._start_pipeline()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title & Subtitle
        self.lbl_title = QLabel("⚡ Installing Plymouth Boot Theme")
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")
        layout.addWidget(self.lbl_title)

        self.lbl_status = QLabel("Step 1/2: Rendering boot frames and packaging assets...")
        self.lbl_status.setStyleSheet("color: #cbd5e1; font-size: 13px;")
        layout.addWidget(self.lbl_status)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Terminal log output
        log_frame = QFrame()
        log_frame.setStyleSheet("background-color: #050811; border: 1px solid #1e293b; border-radius: 8px;")
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(8, 8, 8, 8)

        log_hdr = QLabel("Console Output:")
        log_hdr.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold;")
        log_layout.addWidget(log_hdr)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background-color: transparent; border: none; color: #38bdf8; font-family: monospace; font-size: 11px;")
        log_layout.addWidget(self.txt_log)
        layout.addWidget(log_frame, stretch=1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_done = QPushButton("Close")
        self.btn_done.setProperty("class", "btn-primary")
        self.btn_done.setEnabled(False)
        self.btn_done.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_done)

        layout.addLayout(btn_layout)

    def _start_pipeline(self):
        self.append_log(f"Starting build for theme: {self.project.name} ({self.project.width}x{self.project.height})")
        self.render_thread = RenderThread(self.project, self.staging_dir)
        self.render_thread.progress_signal.connect(self._on_render_progress)
        self.render_thread.completed_signal.connect(self._on_render_completed)
        self.render_thread.error_signal.connect(self._on_render_error)
        self.render_thread.start()

    def _on_render_progress(self, current: int, total: int, msg: str):
        pct = int((current / max(1, total)) * 50)  # rendering is 0-50%
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(f"Step 1/2: {msg}")

    def _on_render_completed(self, staged_theme_dir: str):
        self.append_log(f"Assets generated successfully in staging directory: {staged_theme_dir}")
        self.lbl_status.setText("Step 2/2: Requesting system privileges to update initramfs...")
        self.progress_bar.setValue(50)

        # Start pkexec ApplyWorker
        theme_name = self.project.name.strip().replace(" ", "-").lower()
        if not theme_name.startswith("msm-"):
            theme_name = f"msm-{theme_name}"

        self.worker = ApplyWorker(
            action="apply",
            theme_dir=staged_theme_dir,
            theme_name=theme_name,
            sync_grub=self.project.sync_grub
        )
        self.worker.progress_updated.connect(self._on_apply_progress)
        self.worker.log_line.connect(self.append_log)
        self.worker.completed.connect(self._on_apply_completed)
        self.worker.start()

    def _on_render_error(self, err: str):
        self.append_log(f"Error rendering theme: {err}")
        self.lbl_status.setText(f"Render Error: {err}")
        self.lbl_status.setStyleSheet("color: #f43f5e; font-weight: bold;")
        self.btn_cancel.setText("Close")

    def _on_apply_progress(self, progress: int, msg: str):
        mapped = 50 + int(progress * 0.5)
        self.progress_bar.setValue(mapped)
        self.lbl_status.setText(f"Step 2/2: {msg}")

    def _on_apply_completed(self, success: bool, msg: str):
        self.is_finished = True
        self.btn_cancel.setEnabled(False)
        self.btn_done.setEnabled(True)

        if success:
            shutil.rmtree(self.staging_dir, ignore_errors=True)
            self.progress_bar.setValue(100)
            self.lbl_title.setText("🎉 Boot Logo Applied Successfully!")
            self.lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #10b981;")
            self.lbl_status.setText("Your new boot logo is now live! It will display on your next boot/reboot.")
            self.lbl_status.setStyleSheet("color: #34d399;")
            self.append_log("SUCCESS: Plymouth theme registered and initramfs generated.")
        else:
            self.lbl_title.setText("❌ Installation Failed")
            self.lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f43f5e;")
            self.lbl_status.setText(f"Installation failed: {msg}")
            self.lbl_status.setStyleSheet("color: #f43f5e;")
            self.append_log(f"FAILURE: {msg}")

    def append_log(self, text: str):
        self.txt_log.append(text)
        sb = self.txt_log.verticalScrollBar()
        if sb is not None:
            sb.setValue(sb.maximum())

    def _on_cancel(self):
        if self.worker:
            self.worker.cancel()
        if self.render_thread and self.render_thread.isRunning():
            self.render_thread.terminate()
        self.reject()
