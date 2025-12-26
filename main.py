import sys
from caption_window import CaptionWindow, connect_caption_thread
from audio import SysAudioStream
from models import (
    GummyCaptionThread,
    ParaformerCaptionThread,
    QwenRealtimeCaptionThread,
)
from PyQt6.QtWidgets import QApplication


def main():
    audio_stream = SysAudioStream.from_user_choice()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    window = CaptionWindow(font_size=18)
    window.show()

    thread = ParaformerCaptionThread(audio_stream, window)
    connect_caption_thread(window, thread)
    thread.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
