import sys

from .base import AudioStream

if sys.platform == "linux":
    from .linux import SysAudioStream
else:
    raise NotImplementedError(f"Unsupported platform: {sys.platform}")
