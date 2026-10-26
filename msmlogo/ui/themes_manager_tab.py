"""Active Themes List and System Plymouth Theme Manager Tab."""

import os
import shutil
import tarfile
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox, QFileDialog
)
from ..core.system_manager import SystemManager, InstalledThemeInfo


class ThemeCard(QFrame):
    """Card representing an installed Plymouth boot theme."""

    activate_requested = pyqtSignal(str)  # plymouth_path
    delete_requested = pyqtSignal(str)    # theme_id
    export_requested = pyqtSignal(str)    # theme_id

    def __init__(self, theme: InstalledThemeInfo, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setObjectName("themeCard")
        self.setStyleSheet("""
            #themeCard {
                background-color: #111827;
                border: 1px solid #1f293d;
                border-radius: 12px;
                padding: 12px;
            }
            #themeCard:hover {
                border-color: #38bdf8;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header Row
        hdr = QHBoxLayout()
        title_lbl = QLabel(self.theme.display_name)
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #f8fafc;")
        hdr.addWidget(title_lbl)

        hdr.addStretch()

        if self.theme.is_active:
            active_badge = QLabel("🟢 CURRENTLY ACTIVE")
            active_badge.setStyleSheet("""
                background-color: #065f46;
                color: #34d399;
                font-size: 10px;
                font-weight: bold;
                padding: 3px 8px;
                border-radius: 6px;
            """)
            hdr.addWidget(active_badge)

        if self.theme.is_custom:
            custom_badge = QLabel("MSMLOGO")
            custom_badge.setStyleSheet("""
                background-color: #0369a1;
                color: #7dd3fc;
                font-size: 10px;
                font-weight: bold;
                padding: 3px 8px;
                border-radius: 6px;
            """)
            hdr.addWidget(custom_badge)

        layout.addLayout(hdr)

        # Details
        det_lbl = QLabel(f"ID: {self.theme.id_name} · Module: {self.theme.module_name}")
        det_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(det_lbl)

        if self.theme.description:
            desc_lbl = QLabel(self.theme.description)
            desc_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px;")
            desc_lbl.setWordWrap(True)
            layout.addWidget(desc_lbl)

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        if not self.theme.is_active:
            btn_activate = QPushButton("⭐ Set as Active Theme")
            btn_activate.setProperty("class", "btn-primary")
            btn_activate.clicked.connect(lambda: self.activate_requested.emit(self.theme.plymouth_path))
            btn_row.addWidget(btn_activate)

        if self.theme.is_custom:
            btn_export = QPushButton("📦 Export")
            btn_export.clicked.connect(lambda: self.export_requested.emit(self.theme.id_name))
            btn_row.addWidget(btn_export)

            if not self.theme.is_active:
                btn_delete = QPushButton("🗑️ Remove")
                btn_delete.setProperty("class", "btn-danger")
                btn_delete.clicked.connect(lambda: self.delete_requested.emit(self.theme.id_name))
                btn_row.addWidget(btn_delete)
            else:
                btn_revert = QPushButton("↺ Remove & Restore Linux Default")
                btn_revert.setStyleSheet("""
                    QPushButton {
                        background-color: #991b1b;
                        color: #fecaca;
                        font-weight: bold;
                        border: 1px solid #ef4444;
                        border-radius: 6px;
                        padding: 5px 12px;
                    }
                    QPushButton:hover {
                        background-color: #b91c1c;
                        color: #ffffff;
                    }
                """)
                btn_revert.clicked.connect(lambda: self.delete_requested.emit(self.theme.id_name))
                btn_row.addWidget(btn_revert)

        btn_row.addStretch()
        layout.addLayout(btn_row)


class ThemesManagerTab(QWidget):
    """System Plymouth Themes Management Tab."""

    request_switch_theme = pyqtSignal(str)   # plymouth_path
    request_restore_backup = pyqtSignal()
    request_delete_theme = pyqtSignal(str)   # theme_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh_themes()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # Top Bar
        top_bar = QHBoxLayout()
        header = QLabel("⚙️ Installed System Themes")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")
        top_bar.addWidget(header)
        top_bar.addStretch()

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.clicked.connect(self.refresh_themes)
        top_bar.addWidget(btn_refresh)

        btn_import = QPushButton("📂 Import .msmtheme")
        btn_import.clicked.connect(self._import_theme_archive)
        top_bar.addWidget(btn_import)

        self.btn_restore = QPushButton("↺ Restore Linux Default Logo")
        self.btn_restore.setToolTip("Remove any custom logo and restore the official Linux system boot theme")
        self.btn_restore.setStyleSheet("""
            QPushButton {
                background-color: #065f46;
                color: #34d399;
                font-weight: bold;
                border: 1px solid #10b981;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #047857;
                color: #ffffff;
            }
        """)
        self.btn_restore.clicked.connect(self._on_restore_clicked)
        top_bar.addWidget(self.btn_restore)

        main_layout.addLayout(top_bar)

        # Scroll area for cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setWidget(self.cards_container)
        main_layout.addWidget(self.scroll_area)

    def refresh_themes(self):
        # Clear existing
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Check if custom theme is currently active
        if SystemManager.is_custom_theme_active():
            banner = QFrame()
            banner.setStyleSheet("""
                QFrame {
                    background-color: #1e1b4b;
                    border: 1px solid #6366f1;
                    border-radius: 10px;
                    padding: 8px 14px;
                }
            """)
            b_layout = QHBoxLayout(banner)
            b_layout.setContentsMargins(10, 8, 10, 8)
            b_lbl = QLabel("✨ A custom MsmLogo boot theme is currently ACTIVE on your system.")
            b_lbl.setStyleSheet("color: #e0e7ff; font-weight: bold; font-size: 13px;")
            b_layout.addWidget(b_lbl)
            b_layout.addStretch()
            b_btn = QPushButton("↺ Reset to Linux Official Logo")
            b_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4f46e5;
                    color: #ffffff;
                    font-weight: bold;
                    border-radius: 6px;
                    padding: 5px 14px;
                }
                QPushButton:hover {
                    background-color: #4338ca;
                }
            """)
            b_btn.clicked.connect(self._on_restore_clicked)
            b_layout.addWidget(b_btn)
            self.cards_layout.addWidget(banner)

        themes = SystemManager.list_installed_themes()
        if not themes:
            lbl = QLabel("No Plymouth themes found in /usr/share/plymouth/themes/")
            lbl.setStyleSheet("color: #94a3b8;")
            self.cards_layout.addWidget(lbl)
            return

        for th in themes:
            card = ThemeCard(th)
            card.activate_requested.connect(self.request_switch_theme.emit)
            card.delete_requested.connect(self.request_delete_theme.emit)
            card.export_requested.connect(self._export_theme_archive)
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()
        self.btn_restore.setEnabled(SystemManager.has_factory_backup())

    def _on_restore_clicked(self):
        reply = QMessageBox.question(
            self,
            "Restore Official Linux Boot Logo",
            "Are you sure you want to remove any custom boot logo and restore the system's official Linux default boot theme (rebuilding initramfs)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.request_restore_backup.emit()

    def _export_theme_archive(self, theme_id: str):
        src_dir = f"/usr/share/plymouth/themes/{theme_id}"
        if not os.path.exists(src_dir):
            QMessageBox.warning(self, "Export Failed", f"Directory {src_dir} does not exist.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Export Theme Archive", f"{theme_id}.msmtheme", "MsmLogo Theme (*.msmtheme *.tar.gz)")
        if not save_path:
            return

        try:
            with tarfile.open(save_path, "w:gz") as tar:
                tar.add(src_dir, arcname=theme_id)
            QMessageBox.information(self, "Export Complete", f"Successfully exported theme to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export theme: {e}")

    def _import_theme_archive(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Theme Archive", "", "MsmLogo Theme (*.msmtheme *.tar.gz)")
        if not file_path:
            return

        staging_dir = os.path.expanduser("~/.local/share/msmlogo/staging_import")
        os.makedirs(staging_dir, exist_ok=True)

        try:
            with tarfile.open(file_path, "r:gz") as tar:
                tar.extractall(staging_dir)
            extracted_items = os.listdir(staging_dir)
            if not extracted_items:
                raise ValueError("Archive is empty.")
            extracted_theme_dir = os.path.join(staging_dir, extracted_items[0])
            theme_name = extracted_items[0]

            # Prompt to apply
            reply = QMessageBox.question(
                self,
                "Import Theme",
                f"Theme '{theme_name}' extracted successfully. Would you like to apply it to your system now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # Trigger apply via main window
                # Let's emit a switch or apply
                pass
            self.refresh_themes()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import theme archive: {e}")
