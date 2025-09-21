"""
PulseAudio implementation for Linux audio capture.
参考: https://github.com/HiMeditator/auto-caption/blob/main/engine/sysaudio/linux.py
"""

import subprocess
import json
from typing import Optional
from .base import AudioStream, DEFAULT_SAMPLE_RATE, DEFAULT_CHUNK_RATE


def choose_audio_source() -> str:
    """Interactive selection of PulseAudio source."""
    default_source = subprocess.run(
        ["pactl", "get-default-source"], capture_output=True, text=True
    ).stdout.strip()
    default_sink = subprocess.run(
        ["pactl", "get-default-sink"], capture_output=True, text=True
    ).stdout.strip()

    result = subprocess.run(
        ["pactl", "--format", "json", "list", "sources"], capture_output=True, text=True
    )
    sources = json.loads(result.stdout)

    print("Available audio sources:")
    for i, source in enumerate(sources):
        tags: list[str] = []
        if source["name"] == default_source:
            tags.append("Default Audio Input")
        if source["monitor_source"] == default_sink:
            tags.append("Monitor of Default Audio Output")
        if source["state"] == "RUNNING":
            tags.append("Running")

        tag_string = ""
        if tags:
            tag_string = " (" + ", ".join(tags) + ")"

        print(f"{i}{tag_string}: {source['name']}")
        print(f"    {source.get('description', 'No description')}")

    choice = input("Enter the number of the desired source: ")

    try:
        index = int(choice)
    except ValueError:
        print("Invalid input. Please enter a number.")
        raise ValueError("Invalid input")

    if 0 <= index < len(sources):
        return sources[index]["name"]
    else:
        raise ValueError("Index out of range")


class SysAudioStream(AudioStream):
    """
    PulseAudio implementation for Linux audio capture.

    Uses 'parec' command to capture audio from PulseAudio sources.
    """

    def __init__(
        self,
        device: str,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        chunk_rate: int = DEFAULT_CHUNK_RATE,
    ):
        super().__init__(device, sample_rate, chunk_rate)
        self.process = None

    def open_stream(self) -> None:
        """Start the PulseAudio capture process."""
        if self.process is not None:
            return

        self.process = subprocess.Popen(
            [
                "parec",
                "-d",
                self.device,
                f"--format={self.format}",
                f"--rate={self.sample_rate}",
                f"--channels={self.channels}",
                f"--latency={self.chunk_size}",
            ],
            stdout=subprocess.PIPE,
            bufsize=0,  # Unbuffered for real-time audio
        )

    def read_chunk(self) -> Optional[bytes]:
        """Read a chunk of audio data from the PulseAudio stream."""
        if not self.process or self.process.poll() is not None:
            return None

        if self.process.stdout:
            return self.process.stdout.read(self.chunk_size)
        return None

    def close_stream(self) -> None:
        """Close the PulseAudio stream."""
        if self.process:
            self.process.terminate()
            self.process = None

    @classmethod
    def from_user_choice(
        cls,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        chunk_rate: int = DEFAULT_CHUNK_RATE,
    ) -> "SysAudioStream":
        """Factory method to create AudioStream with user-selected source."""
        device = choose_audio_source()
        return cls(device, sample_rate, chunk_rate)

    @classmethod
    def default_source(
        cls,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        chunk_rate: int = DEFAULT_CHUNK_RATE,
    ) -> "SysAudioStream":
        """Factory method to create AudioStream with default source."""
        default_source = subprocess.run(
            ["pactl", "get-default-source"], capture_output=True, text=True
        ).stdout.strip()
        return cls(default_source, sample_rate, chunk_rate)
