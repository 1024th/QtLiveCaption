from typing import Optional

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt
from PyQt6.QtGui import QFont, QFontMetrics, QTextLayout
from PyQt6.QtWidgets import QLabel, QWidget


class ScrollingLabel(QWidget):
    """
    A widget that displays text with smooth scrolling animation when content exceeds visible lines.
    """

    def __init__(
        self,
        font: Optional[QFont] = None,
        visible_lines: int = 2,
        line_height_multiplier: float = 1.2,
        animation_duration: int = 200,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the ScrollingLabel widget.

        Args:
            font: Font to use for text. If None, uses default font.
            visible_lines: Number of lines visible at once
            line_height_multiplier: Multiplier for line spacing
            animation_duration: Animation duration in milliseconds
            parent: Parent widget
        """
        super().__init__(parent)

        self._visible_lines = visible_lines
        self._line_height_multiplier = line_height_multiplier
        self._animation_duration = animation_duration
        self._text_alignment = (
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        # Set font and calculate metrics
        if font is None:
            font = QFont()
        self.setFont(font)
        self._update_font_metrics()

        # Initialize internal state
        self._labels: list[QLabel] = []
        self._label_index = 0
        self._current_animations: list[QPropertyAnimation] = []
        self._current_text: str = ""
        self._current_lines: list[str] = []

        self._create_labels()

    def _update_font_metrics(self):
        """Update font metrics and line height calculations."""
        font_metrics = QFontMetrics(self.font())
        base_height = font_metrics.height()
        self._line_height = int(base_height * self._line_height_multiplier)
        self.setFixedHeight(self._line_height * self._visible_lines)

    def _create_labels(self):
        """Create and configure internal labels."""
        # Clear existing labels
        for label in self._labels:
            label.deleteLater()

        # Create labels (visible_lines + 1 for smooth animation)
        self._labels = []
        self._label_index = 0
        for i in range(self._visible_lines + 1):
            lbl = QLabel("", self)
            self._labels.append(lbl)
            lbl.setFont(self.font())
            lbl.setStyleSheet("line-height: 1;")
            lbl.setWordWrap(False)
            lbl.setAlignment(self._text_alignment)
            lbl.setGeometry(0, i * self._line_height, self.width(), self._line_height)

    def _get_label(self, index: int) -> QLabel:
        """Get label by relative index."""
        return self._labels[(self._label_index + index) % len(self._labels)]

    def clear(self):
        """Clear all text content."""
        self._current_lines.clear()
        for lbl in self._labels:
            lbl.clear()
        self._stop_animations()

    def set_text(self, text: str, is_new_content: bool):
        old_line_count = len(self._current_lines)
        self._current_text = text
        self._current_lines = self.wrap_text_to_width(text)
        line_count = len(self._current_lines)

        if (
            is_new_content
            or line_count <= self._visible_lines
            or line_count <= old_line_count
            or line_count > old_line_count + 1
        ):
            # No scroll needed - just display the lines
            self._stop_animations()
            for lbl in self._labels:
                lbl.clear()

            start_index = max(0, line_count - self._visible_lines)
            end_index = min(line_count, start_index + self._visible_lines)
            for i, index in enumerate(range(start_index, end_index)):
                self._get_label(i).setText(self._current_lines[index])
                self._get_label(i).setGeometry(
                    0, i * self._line_height, self.width(), self._line_height
                )
            return

        # Scroll animation needed
        self._stop_animations()
        # Display last visible_lines + 1 lines and animate scroll up
        for i in range(self._visible_lines + 1):
            index = line_count - (self._visible_lines + 1) + i
            label = self._get_label(i)
            label.setText(self._current_lines[index])
            label.setGeometry(0, i * self._line_height, self.width(), self._line_height)
            # Create animation
            anim = QPropertyAnimation(label, b"geometry")
            anim.setDuration(self._animation_duration)
            anim.setEasingCurve(QEasingCurve.Type.InQuad)
            anim.setEndValue(
                QRect(0, (i - 1) * self._line_height, self.width(), self._line_height)
            )
            self._current_animations.append(anim)
        # Start all animations
        for anim in self._current_animations:
            anim.start()

        # Connect to know when animation finishes
        if self._current_animations:
            self._current_animations[0].finished.connect(self._on_animation_finished)

        self._label_index = (self._label_index + 1) % len(self._labels)

    def _stop_animations(self):
        """Stop all running animations."""
        for anim in self._current_animations:
            anim.stop()
        self._current_animations.clear()

    def _on_animation_finished(self):
        """Called when scroll animation finishes."""
        # Clean up the label that scrolled out of view
        self._get_label(-1).clear()

    # Public properties
    def visible_lines(self) -> int:
        """Get the number of visible lines."""
        return self._visible_lines

    def set_visible_lines(self, lines: int):
        """Set the number of visible lines."""
        if lines != self._visible_lines:
            self._visible_lines = max(1, lines)
            self.clear()
            self._update_font_metrics()
            self._create_labels()
            self.set_text(self._current_text, is_new_content=True)

    def animation_duration(self) -> int:
        """Get animation duration in milliseconds."""
        return self._animation_duration

    def set_animation_duration(self, duration: int):
        """Set animation duration in milliseconds."""
        self._animation_duration = max(0, duration)

    def resizeEvent(self, a0):
        """Handle widget resize by updating label geometries."""
        super().resizeEvent(a0)
        self.set_text(self._current_text, is_new_content=True)

    def wrap_text_to_width(self, text: str) -> list[str]:
        """Wrap text to fit within the specified width using QTextLayout"""
        lines = []
        text_layout = QTextLayout(text, self.font())

        text_layout.beginLayout()
        while True:
            line = text_layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(self.width())
            start = line.textStart()
            length = line.textLength()
            lines.append(text[start : start + length])
        text_layout.endLayout()

        return lines
