from dashscope.audio.asr import Recognition, RecognitionCallback, RecognitionResult

from audio import AudioStream
from caption_window import CaptionUpdaterThread, CaptionWindow

# Set DASHSCOPE_API_KEY in the environment before running this model.


class ParaformerCaptionThread(CaptionUpdaterThread):
    def __init__(self, audio_stream: AudioStream, parent: CaptionWindow):
        super().__init__(parent)
        self.audio_stream = audio_stream

    class Callback(RecognitionCallback):
        def __init__(self, caption_updater: CaptionUpdaterThread) -> None:
            super().__init__()
            self.caption_updater = caption_updater

        def on_event(
            self,
            result: RecognitionResult,
        ) -> None:
            print("request id: ", result.request_id)
            # print("output: ", result.output)
            print("sentence: ", result.get_sentence())
            self.caption_updater.update_caption(result.get_sentence().get("text"))

    def run(self) -> None:
        callback = self.Callback(self)

        engine = Recognition(
            model="paraformer-realtime-v2",
            format="pcm",
            sample_rate=16000,
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
