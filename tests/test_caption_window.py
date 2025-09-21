#!/usr/bin/env python3

import sys
from PyQt6.QtWidgets import QApplication
from caption_window import CaptionWindow, CaptionUpdaterThread, connect_caption_thread


class CustomCaptionThread(CaptionUpdaterThread):
    """Custom caption thread that generates different content."""

    def run(self) -> None:
        """Generate custom captions."""
        messages = [
            "Welcome to custom captions!",
            "This is a custom thread implementation",
            "You can create your own caption generators",
            "Connect to speech recognition APIs",
            "Or any other real-time text source",
        ]

        for i, message in enumerate(messages):
            if self.isInterruptionRequested():
                break

            self.update_caption(f"{i + 1}: {message}")

            # Wait 2 seconds between messages
            for _ in range(20):
                if self.isInterruptionRequested():
                    return
                self.msleep(100)


def test_default_updater() -> int:
    """
    Demo application showing how to use the CaptionWindow and CaptionUpdaterThread.

    This function is only called when the module is run directly, not when imported as a library.
    """
    app = QApplication(sys.argv)

    # Ensure the application quits when the last window is closed
    app.setQuitOnLastWindowClosed(True)

    # Create window with custom styling
    window = CaptionWindow()
    window.show()

    # Start the background thread to update caption (optional demo)
    thread = CaptionUpdaterThread(window)
    connect_caption_thread(window, thread)
    thread.start()

    # Run the application and exit with the same code
    return app.exec()


def test_custom_updater():
    """Example application using the caption_window library."""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    # Create a custom styled window
    window = CaptionWindow(font_size=18, background_color="rgba(0, 100, 200, 0.7)")
    window.setWindowTitle("Custom Caption Example")
    window.resize(600, 120)
    window.show()

    # Start with custom thread
    try:
        thread = CustomCaptionThread(window)
        connect_caption_thread(window, thread)
        thread.start()
        print("Custom caption thread started successfully!")
    except Exception as e:
        print(f"Error starting thread: {e}")
        return 1

    return app.exec()


if __name__ == "__main__":
    test_default_updater()
    test_custom_updater()
