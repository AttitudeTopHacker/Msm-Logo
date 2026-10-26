#!/usr/bin/env python3
"""Application entry point for MsmLogo."""

import sys
import os
import ctypes

# Ensure package root is in sys.path
SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SCRIPT_DIR)

# Pre-load libxcb-cursor.so.0 if needed by Qt 6.5+ on Linux
candidate_paths = [
    os.path.join(SCRIPT_DIR, "libs", "libxcb-cursor.so.0"),
    os.path.expanduser("~/.local/lib/libxcb-cursor.so.0"),
    "/usr/lib/x86_64-linux-gnu/libxcb-cursor.so.0",
]
for lib_path in candidate_paths:
    if os.path.exists(lib_path):
        try:
            ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
            break
        except Exception:
            pass

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from msmlogo.ui.styles import MODERN_DARK_QSS
from msmlogo.ui.main_window import MainWindow

ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")


def main():
    # Enable high-DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName("MsmLogo")
    app.setApplicationDisplayName("MsmLogo - Linux Boot Logo Manager")
    app.setOrganizationName("MsmLogo")

    # Set Application Icon
    icon_path = os.path.join(ICONS_DIR, "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Apply modern dark styling
    app.setStyleSheet(MODERN_DARK_QSS)

    # Install scroll protector filter so touchpad/mouse wheel gestures scroll pages smoothly
    from msmlogo.ui.scroll_filter import ScrollProtectorFilter
    scroll_filter = ScrollProtectorFilter(app)
    app.installEventFilter(scroll_filter)
    app._scroll_protector_installed = True

    # Launch Main Window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
