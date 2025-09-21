from abc import ABC, abstractmethod
from typing import Optional


DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHUNK_RATE = 10


class AudioStream(ABC):
    """
    Abstract base class for audio stream capture.
    """

    def __init__(
        self,
        device: str,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        chunk_rate: int = DEFAULT_CHUNK_RATE,
    ):
        self.device = device
        self.chunk_rate = chunk_rate
        self.format = "s16le"
        self.channels = 1
        self.sample_rate = sample_rate
        self.chunk_size = sample_rate // chunk_rate

    @abstractmethod
    def open_stream(self) -> None:
        """Open the audio stream for capture."""
        pass

    @abstractmethod
    def read_chunk(self) -> Optional[bytes]:
        """Read a chunk of audio data. Returns None if stream is closed or error."""
        pass

    @abstractmethod
    def close_stream(self) -> None:
        """Close the audio stream."""
        pass

    def __enter__(self):
        """Context manager entry."""
        self.open_stream()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_stream()
