"""Main Application Window for MsmLogo Boot Logo Manager & Creator."""

import os
import tarfile
from typing import Optional
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QLineEdit, QTabWidget, QStatusBar,
    QMessageBox, QFileDialog, QToolBar
)
from ..core.models import ThemeProject
from ..core.templates import get_preset_templates
from ..core.system_manager import SystemManager, ApplyWorker
from .preview_canvas import PreviewPanel
from .editor_tab import EditorTab
from .effects_tab import EffectsTab
from .presets_tab import PresetsTab
from .themes_manager_tab import ThemesManagerTab
from .apply_dialog import ApplyDialog
from .scroll_filter import ScrollProtectorFilter

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")


class MainWindow(QMainWindow):
    """Main window hosting the editors, live boot preview, and system installer."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MsmLogo - Linux Boot Logo Manager & Creator")
        self.resize(1340, 840)
        self.setMinimumSize(1024, 680)

        # Set Window Icon
        icon_path = os.path.join(ICONS_DIR, "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Default to Linux Mint preset
        presets = get_preset_templates()
        self.project = presets.get("mint_glow", ThemeProject())

        self._init_ui()
        self._update_status_bar()

        # Install scroll protector filter on application to prevent inputs from capturing page scrolls
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app and not getattr(app, "_scroll_protector_installed", False):
            self._scroll_protector = ScrollProtectorFilter(app)
            app.installEventFilter(self._scroll_protector)
            app._scroll_protector_installed = True

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(10)

        # 1. Top Header Bar
        main_layout.addLayout(self._create_header_bar())

        # 2. Main Content: Splitter (Left: Tabs, Right: Live Preview)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)

        # Left: Tabs container
        self.tabs = QTabWidget()
        self.editor_tab = EditorTab(self.project)
        self.editor_tab.project_modified.connect(self._on_project_modified)

        self.effects_tab = EffectsTab(self.project)
        self.effects_tab.effects_modified.connect(self._on_project_modified)

        self.presets_tab = PresetsTab()
        self.presets_tab.preset_loaded.connect(self._on_preset_loaded)

        self.themes_tab = ThemesManagerTab()
        self.themes_tab.request_switch_theme.connect(self._on_switch_system_theme)
        self.themes_tab.request_restore_backup.connect(self._on_restore_system_backup)
        self.themes_tab.request_delete_theme.connect(self._on_delete_system_theme)

        self.tabs.addTab(self.editor_tab, "🎨 Design & Logo")
        self.tabs.addTab(self.effects_tab, "✨ Animation & Effects")
        self.tabs.addTab(self.presets_tab, "📦 Preset Templates")
        self.tabs.addTab(self.themes_tab, "⚙️ System Theme Manager")

        splitter.addWidget(self.tabs)

        # Right: Live Preview Panel
        self.preview_panel = PreviewPanel(self.project)
        splitter.addWidget(self.preview_panel)

        # Set balanced splitter ratios (52% left, 48% right)
        splitter.setSizes([680, 620])
        main_layout.addWidget(splitter, stretch=1)

        # 3. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _create_header_bar(self) -> QHBoxLayout:
        hdr = QHBoxLayout()
        hdr.setSpacing(12)

        # App Brand & Icon
        icon_path = os.path.join(ICONS_DIR, "app_icon.png")
        if os.path.exists(icon_path):
            icon_lbl = QLabel()
            pix = QPixmap(icon_path).scaled(34, 34, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_lbl.setPixmap(pix)
            hdr.addWidget(icon_lbl)

        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(1)
        brand_title = QLabel("MsmLogo")
        brand_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #38bdf8;")
        brand_sub = QLabel("Linux Boot Logo & GRUB Manager")
        brand_sub.setStyleSheet("font-size: 11px; color: #94a3b8;")
        brand_layout.addWidget(brand_title)
        brand_layout.addWidget(brand_sub)
        hdr.addLayout(brand_layout)

        hdr.addSpacing(20)

        # Theme Name Edit
        hdr.addWidget(QLabel("Theme Name:"))
        self.txt_theme_name = QLineEdit(self.project.name)
        self.txt_theme_name.setFixedWidth(180)
        self.txt_theme_name.textChanged.connect(self._on_name_changed)
        hdr.addWidget(self.txt_theme_name)

        hdr.addStretch()

        # Action Buttons
        btn_save = QPushButton("💾 Save")
        btn_save.setToolTip("Save theme project file (.json)")
        btn_save.clicked.connect(self._save_project)
        hdr.addWidget(btn_save)

        btn_open = QPushButton("📂 Open")
        btn_open.setToolTip("Open existing theme project")
        btn_open.clicked.connect(self._open_project)
        hdr.addWidget(btn_open)

        btn_export = QPushButton("📦 Export")
        btn_export.setToolTip("Export complete Plymouth theme archive (.msmtheme)")
        btn_export.clicked.connect(self._export_archive)
        hdr.addWidget(btn_export)

        # Prominent Apply Button
        self.btn_apply = QPushButton("⚡ Apply Theme to System")
        self.btn_apply.setProperty("class", "btn-primary")
        self.btn_apply.setToolTip("Render and apply theme to system boot via update-initramfs")
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #06b6d4);
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 18px;
                border: 1px solid #38bdf8;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:1 #0891b2);
                border-color: #7dd3fc;
            }
        """)
        self.btn_apply.clicked.connect(self._launch_apply_dialog)
        hdr.addWidget(self.btn_apply)

        # Quick Restore Linux Default Button
        self.btn_restore_header = QPushButton("↺ Restore Linux Default")
        self.btn_restore_header.setToolTip("Remove custom logo and restore official Linux default boot theme")
        self.btn_restore_header.setStyleSheet("""
            QPushButton {
                background-color: #064e3b;
                color: #a7f3d0;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 14px;
                border: 1px solid #059669;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #047857;
                color: #ffffff;
                border-color: #34d399;
            }
        """)
        self.btn_restore_header.clicked.connect(self._on_header_restore_clicked)
        hdr.addWidget(self.btn_restore_header)

        return hdr

    def _update_status_bar(self):
        active_theme = SystemManager.get_active_theme_path()
        active_name = os.path.basename(active_theme) if active_theme else "Unknown"
        is_custom = SystemManager.is_custom_theme_active()
        theme_tag = "CUSTOM LOGO" if is_custom else "OFFICIAL DEFAULT"
        self.status_bar.showMessage(
            f"Active Plymouth Theme: {active_name} [{theme_tag}]  |  Canvas: {self.project.width}x{self.project.height} ({self.project.fps} FPS)  |  MsmLogo Ready"
        )

    def _on_name_changed(self, text: str):
        self.project.name = text

    def _on_project_modified(self):
        self.preview_panel.notify_project_changed()
        self._update_status_bar()

    def _on_preset_loaded(self, template: ThemeProject):
        # Deep copy template values
        self.project = ThemeProject.from_dict(template.to_dict())
        self.txt_theme_name.setText(self.project.name)
        self.editor_tab.project = self.project
        self.editor_tab.load_project_values()
        self.effects_tab.project = self.project
        self.effects_tab.load_values()
        self.preview_panel.set_project(self.project)
        self.tabs.setCurrentIndex(0)  # switch to editor
        self._update_status_bar()
        self.status_bar.showMessage(f"Loaded preset: {self.project.display_name}", 4000)

    def _save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", f"{self.project.name}.json", "JSON Projects (*.json)")
        if path:
            try:
                self.project.save_to_file(path)
                QMessageBox.information(self, "Saved", f"Project saved successfully to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save project: {e}")

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "JSON Projects (*.json)")
        if path:
            try:
                proj = ThemeProject.load_from_file(path)
                self._on_preset_loaded(proj)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open project: {e}")

    def _export_archive(self):
        save_path, _ = QFileDialog.getSaveFileName(self, "Export Plymouth Theme Archive", f"{self.project.name}.msmtheme", "MsmLogo Theme (*.msmtheme *.tar.gz)")
        if not save_path:
            return

        staging_dir = os.path.expanduser("~/.local/share/msmlogo/staging_export")
        os.makedirs(staging_dir, exist_ok=True)

        from ..core.plymouth_generator import PlymouthGenerator
        gen = PlymouthGenerator(self.project)
        theme_dir = gen.generate_theme(staging_dir)
        theme_folder_name = os.path.basename(theme_dir)

        try:
            with tarfile.open(save_path, "w:gz") as tar:
                tar.add(theme_dir, arcname=theme_folder_name)
            QMessageBox.information(self, "Exported", f"Theme archive exported to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export theme archive: {e}")

    def _launch_apply_dialog(self):
        dialog = ApplyDialog(self.project, self)
        dialog.exec()
        self._update_status_bar()
        self.themes_tab.refresh_themes()

    def _on_switch_system_theme(self, plymouth_path: str):
        reply = QMessageBox.question(
            self,
            "Switch Boot Theme",
            f"Are you sure you want to activate '{os.path.basename(plymouth_path)}' as your system boot theme and rebuild initramfs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        worker = ApplyWorker(action="switch", plymouth_path=plymouth_path)
        # Show mini progress dialog or wait
        from PyQt6.QtWidgets import QProgressDialog
        prog = QProgressDialog("Switching theme and updating initramfs...", "Cancel", 0, 0, self)
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.show()

        worker.completed.connect(lambda success, msg: (
            prog.close(),
            self._update_status_bar(),
            self.themes_tab.refresh_themes(),
            QMessageBox.information(self, "Theme Switched", "Active boot theme updated successfully!") if success else QMessageBox.critical(self, "Error", msg)
        ))
        worker.start()

    def _on_restore_system_backup(self):
        worker = ApplyWorker(action="restore")
        from PyQt6.QtWidgets import QProgressDialog
        prog = QProgressDialog("Restoring factory boot theme and rebuilding initramfs...", "Cancel", 0, 0, self)
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.show()

        worker.completed.connect(lambda success, msg: (
            prog.close(),
            self._update_status_bar(),
            self.themes_tab.refresh_themes(),
            QMessageBox.information(self, "Restored", "Factory boot theme restored successfully!") if success else QMessageBox.critical(self, "Error", msg)
        ))
        worker.start()

    def _on_header_restore_clicked(self):
        reply = QMessageBox.question(
            self,
            "Restore Linux Official Default Boot Logo",
            "Are you sure you want to remove any custom boot theme and restore the official Linux default boot logo?\n\nThis will reconfigure Plymouth and rebuild your initramfs.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._on_restore_system_backup()

    def _on_delete_system_theme(self, theme_name: str):
        is_active = (theme_name in (SystemManager.get_active_theme_path() or ""))
        msg = (
            f"Custom theme '{theme_name}' is currently your ACTIVE boot theme.\n\n"
            f"Deleting it will automatically restore Linux's official default boot logo and rebuild initramfs. Continue?"
            if is_active else
            f"Are you sure you want to permanently delete custom theme '{theme_name}' from /usr/share/plymouth/themes/?"
        )

        reply = QMessageBox.question(
            self,
            "Delete / Restore Theme",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        from PyQt6.QtWidgets import QProgressDialog
        prog = QProgressDialog(f"Removing '{theme_name}' and updating system...", "Cancel", 0, 0, self)
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.show()

        worker = ApplyWorker(action="delete", theme_name=theme_name)
        worker.completed.connect(lambda success, msg: (
            prog.close(),
            self.themes_tab.refresh_themes(),
            self._update_status_bar(),
            QMessageBox.information(self, "Theme Removed", "Theme removed and default boot logo restored successfully!") if success else QMessageBox.critical(self, "Error", msg)
        ))
        worker.start()
