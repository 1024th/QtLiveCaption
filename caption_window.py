import itertools
from typing import Optional

from PyQt6.QtCore import QPoint, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QCloseEvent,
    QCursor,
    QFont,
    QFontMetrics,
    QMouseEvent,
    QPainter,
    QResizeEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from scrolling_label import ScrollingLabel

__all__ = ["CaptionWindow", "CaptionUpdaterThread", "connect_caption_thread"]


class ElidedLabel(QLabel):
    """QLabel with elide support similar to QML Text.ElideLeft"""

    def __init__(self, elide_mode: Qt.TextElideMode, text="", parent=None):
        super().__init__(text, parent)
        self.elide_mode = elide_mode

    def paintEvent(self, a0):  # pyright: ignore[reportIncompatibleMethodOverride]
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())

        # Calculate how many lines can fit in the widget height
        line_height = metrics.lineSpacing()
        available_lines = self.height() // line_height if line_height > 0 else 1

        # Use the smaller of max_lines or available_lines
        effective_lines = available_lines - 0.2

        # Calculate text width limit based on effective lines
        # Each line can be up to widget width, so total text can be effective_lines * width
        max_width = int(effective_lines * self.width())

        elided = metrics.elidedText(self.text(), self.elide_mode, max_width)

        painter.drawText(
            self.rect(),
            self.alignment() | Qt.TextFlag.TextWordWrap if self.wordWrap() else 0,
            elided,
        )


class CaptionWindow(QMainWindow):
    """
    A frameless, translucent caption display window that stays on top.

    This window provides a customizable overlay for displaying live captions
    with drag-to-move and edge-resize functionality.

    Signals:
        caption_updated (str): Emitted when caption text should be updated

    Attributes:
        caption_thread: Optional reference to the background thread updating captions
    """

    # Signal for thread-safe caption updates
    caption_updated = pyqtSignal(str)

    def __init__(
        self, font_size: int = 14, background_color: str = "rgba(0, 0, 0, 0.6)"
    ) -> None:
        """Initialize the caption window."""
        super().__init__()
        self.font_size = font_size
        self.background_color = background_color
        self.init_ui()
        self.caption_thread: Optional[QThread] = None  # Store reference to QThread
        self.resize_margin = 10  # Pixel margin for resize detection

        # Connect the signal to the update method
        self.caption_updated.connect(self.update_caption_display)

    def init_ui(self) -> None:
        self.setWindowTitle("Qt Live Caption")
        self.resize(600, 100)

        # Hide title bar by adding FramelessWindowHint
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Enable mouse tracking for resize functionality
        self.setMouseTracking(True)

        # Create a background widget
        self.bg_widget = QFrame(self)
        # Use object name for styling to avoid affecting child widgets
        self.bg_widget.setObjectName("bg_widget")
        self.bg_widget.setStyleSheet(f"""
            #bg_widget {{
                background-color: {self.background_color};
                border-radius: 8px;
            }}
        """)
        self.bg_widget.setGeometry(self.rect())
        self.bg_widget.setMouseTracking(True)
        self.setCentralWidget(self.bg_widget)

        # Create caption label with elide support
        # self.caption_label = ElidedLabel(
        #     Qt.TextElideMode.ElideLeft,
        #     "Caption text will appear here.",
        #     self.bg_widget,
        # )
        self.caption_label = ScrollingLabel(
            font=QFont("sans-serif", self.font_size),
            visible_lines=2,
            line_height_multiplier=1.2,
            parent=self.bg_widget,
        )
        self.caption_label.setMouseTracking(True)
        self.caption_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Center the label in the background widget
        self.caption_layout = QVBoxLayout(self.bg_widget)
        self.caption_layout.setContentsMargins(self.font_size, 6, self.font_size, 6)
        self.caption_layout.addWidget(self.caption_label)
        print(f"Window size: {self.size()}, Label size: {self.caption_label.size()}")

        # Set font
        font = QFont("sans-serif", self.font_size, weight=QFont.Weight.Medium)
        self.caption_label.setFont(font)

        # Make label background transparent and style text only
        self.caption_label.setStyleSheet("""
            QLabel {
                color: white;
                line-height: 1.6;
                background: transparent;
            }
        """)

        # Add black shadow to the text
        shadow = QGraphicsDropShadowEffect(self.caption_label)
        shadow.setBlurRadius(6)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(1, 1)
        self.caption_label.setGraphicsEffect(shadow)

        # Add close button
        self.button_radius = 14
        self.close_button = QPushButton("✕", self.bg_widget)
        self.close_button.setToolTip("Close window")
        self.close_button.setFixedSize(2 * self.button_radius, 2 * self.button_radius)
        self.update_close_button_position()
        self.close_button.setFlat(True)
        self.close_button.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.close_button.setStyleSheet(f"""
            QPushButton {{
                color: white;
                border: none;
                border-radius: {self.button_radius}px;
                font-size: {self.button_radius}px;
                background-color: rgba(0, 0, 0, 0.2);
            }}
            QPushButton:hover {{
                background-color: rgba(255, 0, 0, 0.6);
            }}
        """)
        self.close_button.clicked.connect(self.close)
        # Workaround to ensure the background of button repaints correctly on Wayland
        QTimer.singleShot(40, self.close_button.update)

    # def update_label_alignment(self):
    #     """根据文本大小更新 caption_label 的对齐方式"""
    #     hint = self.caption_label.sizeHint()
    #     parent_height = self.height()

    #     if hint.height() <= parent_height:
    #         print("Centering label vertically")
    #         self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    #     else:
    #         print("Aligning label to bottom")
    #         self.caption_label.setAlignment(
    #             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom
    #         )

    def update_close_button_position(self) -> None:
        """Update close button position based on window size."""
        self.close_button.move(self.width() - 8 - 2 * self.button_radius, 8)

    def resizeEvent(self, event: QResizeEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle window resize events."""
        self.bg_widget.setGeometry(self.rect())
        self.update_close_button_position()
        # self.update_label_alignment()
        super().resizeEvent(event)

    def get_resize_edges(self, pos: QPoint) -> Qt.Edge:
        """Determine which edges the mouse position is near for resizing."""
        edges = Qt.Edge(0)  # No edges initially
        margin = self.resize_margin

        # Check left edge
        if pos.x() <= margin:
            edges |= Qt.Edge.LeftEdge
        # Check right edge
        elif pos.x() >= self.width() - margin:
            edges |= Qt.Edge.RightEdge

        # Check top edge
        if pos.y() <= margin:
            edges |= Qt.Edge.TopEdge
        # Check bottom edge
        elif pos.y() >= self.height() - margin:
            edges |= Qt.Edge.BottomEdge

        return edges

    def update_caption_display(
        self, new_caption: str, is_new_content: bool = False
    ) -> None:
        """Thread-safe method to update caption display."""
        self.caption_label.set_text(new_caption, is_new_content)
        # self.update_label_alignment()

    def closeEvent(self, event: QCloseEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle window close event to ensure proper cleanup."""
        print("Window is being closed, cleaning up...")

        # Properly cleanup QThread if it exists
        if self.caption_thread and self.caption_thread.isRunning():
            self.caption_thread.requestInterruption()  # Qt-native way to request thread stop
            self.caption_thread.quit()  # Ask thread to quit
            self.caption_thread.wait(1000)  # Wait up to 1 second for thread to finish

        event.accept()  # Accept the close event
        QApplication.quit()  # Ensure the application exits

    def mousePressEvent(self, event: QMouseEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle mouse press events for window dragging and resizing."""
        if event.button() == Qt.MouseButton.LeftButton:
            window_handle = self.windowHandle()
            if not window_handle:
                return
            # Check if mouse is near an edge for resizing
            edges = self.get_resize_edges(event.position().toPoint())
            if edges:
                # Start system resize if near an edge
                window_handle.startSystemResize(edges)
            else:
                # Move the window by dragging if not near an edge
                window_handle.startSystemMove()

    def mouseMoveEvent(self, event: Optional[QMouseEvent]) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Change cursor when hovering over resize edges."""
        if not event:
            return
        edges = self.get_resize_edges(event.position().toPoint())

        if edges == (Qt.Edge.LeftEdge | Qt.Edge.TopEdge) or edges == (
            Qt.Edge.RightEdge | Qt.Edge.BottomEdge
        ):
            # Top-left or bottom-right corner
            self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        elif edges == (Qt.Edge.RightEdge | Qt.Edge.TopEdge) or edges == (
            Qt.Edge.LeftEdge | Qt.Edge.BottomEdge
        ):
            # Top-right or bottom-left corner
            self.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
        elif edges & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge):
            # Left or right edge
            self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
        elif edges & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge):
            # Top or bottom edge
            self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
        else:
            # Not near any edge - normal cursor
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))


class CaptionUpdaterThread(QThread):
    """
    QThread class that updates caption from a background thread.

    This is a basic implementation that emits sample caption updates.
    Subclass this to implement custom caption generation logic.

    Override run() to implement the main thread logic.
    Call update_caption(new_caption) to emit new captions.
    """

    caption_updated = pyqtSignal(str)

    def __init__(self, parent: CaptionWindow) -> None:
        """Initialize the caption updater thread."""
        super().__init__(parent)

    def update_caption(self, new_caption: str) -> None:
        """Emit a new caption from the thread."""
        self.caption_updated.emit(new_caption)

    def run(self) -> None:
        """
        Override QThread run method - this is where the work happens.

        This basic implementation emits sample captions. Override this method
        to implement your own caption generation logic.
        """
        for i in itertools.count():
            # Use Qt's built-in interruption mechanism instead of custom flag
            if self.isInterruptionRequested():
                break

            # Emit the caption immediately
            self.update_caption(f"Sample caption update {i}")

            # Wait 1 second with frequent interruption checks (every 100ms)
            for _ in range(10):
                if self.isInterruptionRequested():
                    print("QThread background thread interrupted during sleep")
                    return
                self.msleep(100)  # Short sleep intervals for responsive interruption

        print("QThread background thread finished")


def connect_caption_thread(window: CaptionWindow, thread: CaptionUpdaterThread) -> None:
    """
    Connect a CaptionUpdaterThread to a CaptionWindow.

    Raises:
        RuntimeError: If a thread is already running for this window
        ValueError: If inputs are invalid
    """
    # Validate inputs
    if not isinstance(window, CaptionWindow):
        raise ValueError("window must be an instance of CaptionWindow")
    if not isinstance(thread, CaptionUpdaterThread):
        raise ValueError("thread must be an instance of CaptionUpdaterThread")

    # Check if a thread is already running
    if window.caption_thread and window.caption_thread.isRunning():
        raise RuntimeError("A caption thread is already running for this window")

    window.caption_thread = thread
    # Connect the thread's signal to the window's update method
    thread.caption_updated.connect(window.caption_updated)

    # Close the window when the thread finishes
    thread.finished.connect(window.close)
