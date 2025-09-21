import sys
import time

from caption_window import CaptionWindow, CaptionUpdaterThread, connect_caption_thread
from audio import AudioStream, SysAudioStream
from PyQt6.QtWidgets import QApplication

from dashscope.audio.asr import (
    TranslationRecognizerRealtime,
    TranslationRecognizerCallback,
    TranscriptionResult,
    TranslationResult,
)


# Set your DashScope API key in the environment variable DASHSCOPE_API_KEY,
# or uncomment and set it here directly:
# dashscope.api_key = "your-api-key"


class GummyCaptionThread(CaptionUpdaterThread):
    def __init__(self, audio_stream: AudioStream, parent: CaptionWindow):
        super().__init__(parent)
        self.audio_stream = audio_stream

    class Callback(TranslationRecognizerCallback):
        def __init__(self, caption_updater: CaptionUpdaterThread) -> None:
            super().__init__()
            self.caption_updater = caption_updater

        def on_event(
            self,
            request_id,
            transcription_result: TranscriptionResult,
            translation_result: TranslationResult,
            usage,
        ) -> None:
            print("request id: ", request_id)
            print("usage: ", usage)
            if translation_result is not None:
                print(
                    "translation_languages: ",
                    translation_result.get_language_list(),
                )
                english_translation = translation_result.get_translation("en")
                print("sentence id: ", english_translation.sentence_id)
                print("translate to english: ", english_translation.text)
            if transcription_result is not None:
                print("sentence id: ", transcription_result.sentence_id)
                print("transcription: ", transcription_result.text)
                self.caption_updater.update_caption(transcription_result.text)

    def run(self) -> None:
        self.audio_stream.open_stream()
        callback = self.Callback(self)

        engine = TranslationRecognizerRealtime(
            model="gummy-realtime-v1",
            format="pcm",
            sample_rate=16000,
            # transcription_enabled=True,
            # source_language="auto",
            # source_language="zh",
            # translation_enabled=False,
            # translation_target_languages=["en"],
            max_end_silence=400,
            callback=callback,
        )
        engine.start()
        print("Voice recognition started...")
        while True:
            if self.isInterruptionRequested():
                break
            data = self.audio_stream.read_chunk()

            print(f"Read audio chunk, time: {time.time()}")
            if data:
                engine.send_audio_frame(data)
            else:
                break

        engine.stop()
        self.audio_stream.close_stream()


def main():
    audio_stream = SysAudioStream.from_user_choice()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    window = CaptionWindow(font_size=18)
    window.show()

    thread = GummyCaptionThread(audio_stream, window)
    connect_caption_thread(window, thread)
    thread.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
