"""Unit tests for ScrollProtectorFilter."""

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import (
    QApplication, QScrollArea, QWidget, QVBoxLayout,
    QComboBox, QSpinBox, QSlider
)
from PyQt6.QtCore import Qt, QPoint, QPointF
from PyQt6.QtGui import QWheelEvent
from msmlogo.ui.scroll_filter import ScrollProtectorFilter


class TestScrollProtectorFilter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        cls.app = QApplication.instance() or QApplication(sys.argv or ["test_scroll_filter"])
        cls.filter = ScrollProtectorFilter(cls.app)
        cls.app.installEventFilter(cls.filter)

    def setUp(self):
        self.scroll = QScrollArea()
        self.scroll.resize(400, 300)
        self.content = QWidget()
        self.layout = QVBoxLayout(self.content)

        self.combo = QComboBox()
        self.combo.addItems(["1920x1080 (16:9)", "2560x1440 (16:9)", "3840x2160 (4K)"])
        self.layout.addWidget(self.combo)

        self.spin = QSpinBox()
        self.spin.setRange(0, 5000)
        self.spin.setValue(1920)
        self.layout.addWidget(self.spin)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(45)
        self.layout.addWidget(self.slider)

        spacer = QWidget()
        spacer.setFixedHeight(1200)
        self.layout.addWidget(spacer)

        self.scroll.setWidget(self.content)
        self.scroll.show()

    def tearDown(self):
        self.scroll.close()

    def test_combobox_wheel_redirected_to_scroll(self):
        initial_index = self.combo.currentIndex()
        initial_scroll = self.scroll.verticalScrollBar().value()

        # Send wheel down event over combobox
        wheel_evt = QWheelEvent(
            QPointF(10, 10), QPointF(10, 10), QPoint(0, 0), QPoint(0, -120),
            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase, False
        )
        self.app.sendEvent(self.combo, wheel_evt)

        # Combobox value must remain unchanged
        self.assertEqual(self.combo.currentIndex(), initial_index)
        # Scroll area must have scrolled down
        self.assertGreater(self.scroll.verticalScrollBar().value(), initial_scroll)

    def test_spinbox_wheel_redirected_to_scroll(self):
        initial_value = self.spin.value()
        initial_scroll = self.scroll.verticalScrollBar().value()

        wheel_evt = QWheelEvent(
            QPointF(10, 10), QPointF(10, 10), QPoint(0, 0), QPoint(0, -120),
            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase, False
        )
        self.app.sendEvent(self.spin, wheel_evt)

        # Spinbox value must remain unchanged
        self.assertEqual(self.spin.value(), initial_value)
        # Scroll area must have scrolled down
        self.assertGreater(self.scroll.verticalScrollBar().value(), initial_scroll)

    def test_slider_wheel_redirected_to_scroll(self):
        initial_value = self.slider.value()
        initial_scroll = self.scroll.verticalScrollBar().value()

        wheel_evt = QWheelEvent(
            QPointF(10, 10), QPointF(10, 10), QPoint(0, 0), QPoint(0, -120),
            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase, False
        )
        self.app.sendEvent(self.slider, wheel_evt)

        # Slider value must remain unchanged
        self.assertEqual(self.slider.value(), initial_value)
        # Scroll area must have scrolled down
        self.assertGreater(self.scroll.verticalScrollBar().value(), initial_scroll)


if __name__ == "__main__":
    unittest.main()
