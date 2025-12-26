import base64
import logging
import os
import sys
import threading
import time

import dashscope
from dashscope.audio.qwen_omni import OmniRealtimeCallback, OmniRealtimeConversation
from dashscope.audio.qwen_omni.omni_realtime import MultiModality, TranscriptionParams

from audio import AudioStream
from caption_window import CaptionUpdaterThread, CaptionWindow

LOGGER = logging.getLogger(__name__)

MODEL_NAME = "qwen3-asr-flash-realtime"
BASE_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"


def setup_logging():
    """配置日志输出"""
    # 配置当前模块的logger
    LOGGER.setLevel(logging.DEBUG)
    if not LOGGER.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        LOGGER.addHandler(handler)


class CaptionCallback(OmniRealtimeCallback):
    """处理实时识别回调"""

    def __init__(self, caption_thread: "QwenRealtimeCaptionThread"):
        self.caption_thread = caption_thread
        self.conversation = None

    def on_open(self):
        LOGGER.info("Qwen realtime connection opened.")

    def on_close(self, close_status_code, close_msg):
        LOGGER.info("Qwen realtime closed: %s %s", close_status_code, close_msg)

    def on_event(self, response):
        try:
            event_type = response.get("type")
            LOGGER.debug("Qwen realtime event: %s", response)

            # 处理最终识别结果
            if event_type == "conversation.item.input_audio_transcription.completed":
                text = response.get("transcript")
                if text:
                    self.caption_thread.update_caption(text)

            # 处理临时识别结果
            elif event_type == "conversation.item.input_audio_transcription.text":
                text = response.get("text") + response.get("stash")
                if text:
                    self.caption_thread.update_caption(text)

            # 处理会话创建
            elif event_type == "session.created":
                LOGGER.info(
                    "Session created: %s", response.get("session", {}).get("id")
                )

            # 处理语音开始/停止
            elif event_type == "input_audio_buffer.speech_started":
                LOGGER.debug("Speech started")
            elif event_type == "input_audio_buffer.speech_stopped":
                LOGGER.debug("Speech stopped")

        except Exception as e:
            LOGGER.error("Error handling event: %s", e)


class QwenRealtimeCaptionThread(CaptionUpdaterThread):
    def __init__(
        self,
        audio_stream: AudioStream,
        parent: CaptionWindow,
        language: str = "zh",
    ) -> None:
        super().__init__(parent)
        self.audio_stream = audio_stream
        self.language = language
        self.conversation = None

    def run(self) -> None:
        # 首次运行时配置日志
        setup_logging()

        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            LOGGER.error("DASHSCOPE_API_KEY is required for Qwen realtime model.")
            self.update_caption("Missing DASHSCOPE_API_KEY for Qwen model.")
            return

        dashscope.api_key = api_key

        # 创建回调处理器
        callback = CaptionCallback(self)

        # 创建对话实例
        self.conversation = OmniRealtimeConversation(
            model=MODEL_NAME,
            url=BASE_URL,
            callback=callback,
        )

        # 连接到服务器
        try:
            self.conversation.connect()
        except Exception as e:
            LOGGER.error("Failed to connect: %s", e)
            self.update_caption(f"Connection failed: {e}")
            return

        # 配置会话参数
        transcription_params = TranscriptionParams(
            language=self.language,
            sample_rate=16000,
            input_audio_format="pcm",
        )
        turn_detection = {
            "type": "server_vad",
            "threshold": 0.2,
            "silence_duration_ms": 800,
        }
        self.conversation.update_session(
            output_modalities=[MultiModality.TEXT],
            enable_input_audio_transcription=True,
            transcription_params=transcription_params,
            turn_detection=turn_detection,
        )

        self.audio_stream.open_stream()
        try:
            while not self.isInterruptionRequested():
                chunk = self.audio_stream.read_chunk()
                if not chunk:
                    break

                encoded = base64.b64encode(chunk).decode("utf-8")
                try:
                    self.conversation.append_audio(encoded)
                except Exception as exc:  # pragma: no cover - network errors
                    LOGGER.warning("Failed to send audio: %s", exc)
                    break

        finally:
            self.audio_stream.close_stream()
            if self.conversation:
                self.conversation.close()
