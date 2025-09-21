# Qt Live Caption

A lightweight PyQt6 application that automatically displays real-time captions using speech-to-text technology.

## Platform Support

**Only Linux is supported** at the moment.

## AI Model

**Only `gummy-realtime-v1` is supported** at the moment. See [Gummy实时语音识别、翻译Python SDK](https://help.aliyun.com/zh/model-studio/real-time-python-sdk#635f92ee7cbll) for details.

Set environment variables `DASHSCOPE_API_KEY` to your API key to use the model.

## Getting Started

1. Clone the repository.
2. Use `uv` to install dependencies:
   ```bash
   uv install
   ```
3. Run the application:
   ```bash
   python main.py
   ```
