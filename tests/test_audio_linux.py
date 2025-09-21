"""
Test script for PulseAudioStream in audio.linux
"""
from audio.linux import SysAudioStream

def test_interactive():
    # Method 1: Using the interactive factory method
    with SysAudioStream.from_user_choice() as audio_stream:
        print(f"Created PulseAudioStream with source: {audio_stream.device}")
        chunk = audio_stream.read_chunk()
        if chunk:
            print(f"Read {len(chunk)} bytes of audio data")

def test_default():
    # Method 2: Using the default source (non-interactive)
    with SysAudioStream.default_source() as audio_stream:
        print(f"Created PulseAudioStream with default source: {audio_stream.device}")
        chunk = audio_stream.read_chunk()
        if chunk:
            print(f"Read {len(chunk)} bytes of audio data")

if __name__ == "__main__":
    print("Running interactive test...")
    test_interactive()
    print("\nRunning default source test...")
    test_default()
