"""Modern dark theme stylesheet and styling tokens for MsmLogo."""

MODERN_DARK_QSS = """
/* Global Window & Fonts */
QWidget {
    background-color: #0b0f19;
    color: #f1f5f9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Liberation Sans", "DejaVu Sans", sans-serif;
    font-size: 13px;
    outline: none;
}

/* Header & Toolbars */
QToolBar {
    background: #0f172a;
    border-bottom: 1px solid #1e293b;
    padding: 8px 16px;
    spacing: 12px;
}

/* Group Boxes & Panels */
QGroupBox {
    background-color: #111827;
    border: 1px solid #1f293d;
    border-radius: 10px;
    margin-top: 24px;
    padding: 18px 14px 14px 14px;
    font-weight: bold;
    font-size: 13px;
    color: #38bdf8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 10px;
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #e2e8f0;
}

/* Card Frames */
QFrame.card {
    background-color: #131d31;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 12px;
}

QFrame.card:hover {
    border-color: #38bdf8;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #1e293b;
    background: #0d1322;
    border-radius: 10px;
    top: -1px;
}

QTabBar::tab {
    background: #0f172a;
    color: #94a3b8;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border: 1px solid #1e293b;
    border-bottom: none;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: #0d1322;
    color: #38bdf8;
    border-top: 2px solid #38bdf8;
}

QTabBar::tab:hover:!selected {
    background: #1e293b;
    color: #e2e8f0;
}

/* Buttons */
QPushButton {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #27354f;
    border-color: #38bdf8;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #0f172a;
}

QPushButton:disabled {
    background-color: #1e293b;
    color: #64748b;
    border-color: #1e293b;
}

/* Primary Accent Button */
QPushButton.btn-primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #06b6d4);
    border: 1px solid #38bdf8;
    color: #ffffff;
    font-weight: bold;
    padding: 10px 20px;
}

QPushButton.btn-primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:1 #0891b2);
    border-color: #7dd3fc;
}

/* Success Button */
QPushButton.btn-success {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
    border: 1px solid #34d399;
    color: #ffffff;
    font-weight: bold;
}

QPushButton.btn-success:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
}

/* Danger Button */
QPushButton.btn-danger {
    background-color: #881337;
    border: 1px solid #f43f5e;
    color: #ffffff;
}

QPushButton.btn-danger:hover {
    background-color: #9f1239;
}

/* Inputs & Line Edits */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f8fafc;
    font-size: 13px;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #38bdf8;
    background-color: #131d31;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #0f172a;
    border: 1px solid #334155;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
    color: #f1f5f9;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 6px;
    background: #1e293b;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #38bdf8;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 2px solid #0284c7;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #38bdf8;
    border-color: #ffffff;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
    color: #e2e8f0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #475569;
    background: #0f172a;
}

QCheckBox::indicator:checked {
    background-color: #0284c7;
    border-color: #38bdf8;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #0b0f19;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #1e293b;
    min-height: 24px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #334155;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Status Bar */
QStatusBar {
    background: #0f172a;
    border-top: 1px solid #1e293b;
    color: #94a3b8;
    padding: 4px 12px;
}

/* Progress Bar */
QProgressBar {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
    height: 20px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
    border-radius: 7px;
}
"""
