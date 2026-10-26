"""Global scroll protection event filter for preventing accidental input value changes."""

from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QComboBox, QAbstractSpinBox, QSlider, QScrollBar
)


class ScrollProtectorFilter(QObject):
    """
    Prevents mouse wheel and touchpad scrolling gestures from accidentally altering
    values of QComboBox, QSpinBox, QDoubleSpinBox, and QSlider when hovering over them
    inside scrollable views (QScrollArea).
    
    Instead of changing the input's value, the wheel event is redirected to scroll
    the enclosing QScrollArea smoothly.
    """

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            target = obj
            if isinstance(target, QWidget):
                # If event was targeted at an internal child of a spinbox (like QLineEdit)
                parent_spin = target.parentWidget()
                if isinstance(parent_spin, QAbstractSpinBox):
                    target = parent_spin

                # Only intercept inputs (combobox, spinbox, slider), not scrollbars themselves
                if isinstance(target, (QComboBox, QAbstractSpinBox, QSlider)) and not isinstance(target, QScrollBar):
                    # Check if this input widget is enclosed in a QScrollArea
                    parent = target.parentWidget()
                    while parent:
                        if isinstance(parent, QScrollArea):
                            event.ignore()
                            parent.wheelEvent(event)
                            return True  # Consume on input so its value is not changed
                        parent = parent.parentWidget()

        return super().eventFilter(obj, event)
