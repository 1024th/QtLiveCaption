from dashscope.audio.asr import (
    TranslationRecognizerRealtime,
    TranslationRecognizerCallback,
    TranscriptionResult,
    TranslationResult,
)

from audio import AudioStream
from caption_window import CaptionUpdaterThread, CaptionWindow

# Set DASHSCOPE_API_KEY in the environment before running this model.


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
        self.audio_stream.open_stream()

        print("Voice recognition started...")
        while True:
            if self.isInterruptionRequested():
                break
            data = self.audio_stream.read_chunk()
            if data:
                engine.send_audio_frame(data)
            else:
                break

        engine.stop()
        self.audio_stream.close_stream()
