from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from scrolling_label import ScrollingLabel

if __name__ == "__main__":
    app = QApplication([])

    widget = ScrollingLabel(font=QFont("Arial", 16), visible_lines=2)
    widget.resize(300, 100)
    widget.show()

    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    split_text = text.split(" ")

    i = 0

    def update():
        global i
        text = " ".join(split_text[:i])
        widget.set_text(text, i == 0)
        i = (i + 1) % len(split_text)

    timer = QTimer()
    timer.timeout.connect(update)
    timer.start(200)

    app.exec()
