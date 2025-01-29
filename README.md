# Speech to Text Transcription Tool

A comprehensive speech-to-text platform that combines real-time transcription with LLM processing, chat capabilities, and text-to-speech conversion.

## Features

- Real-time speech-to-text transcription using MLX Whisper
- Interactive chat mode with conversation history
- LLM integration for text processing and responses
- Text-to-speech conversion with Kokoro
- Voice optimization for improved speech synthesis
- Multiple output options (clipboard, file, speakers)
- Automatic silence detection and background noise calibration

## Quick Start

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install dependencies and set up development environment
uv sync

# Run with basic transcription and clipboard support
./speech_to_text.sh
```

## Setup

If you're developing the project:

1. Clone the repository
2. Make sure you have Python 3.10.16 installed
3. Setup the development environment:
```bash
uv venv
source .venv/bin/activate
uv sync
```

To update dependencies:
1. Make changes to `pyproject.toml`
2. Run `uv sync` to update your environment

## Usage

### Using the Shell Script

Make script executable, then run with clipboard support enabled:

```bash
chmod +x speech_to_text.sh
./speech_to_text.sh
```

### Using UV Run Directly

The application supports various modes and features:

```bash
# Basic Modes
uv run src/main.py --single     # Single transcription mode
uv run src/main.py             # Continuous mode
uv run src/main.py --copy      # With clipboard support

# Output Options
uv run src/main.py --output-file transcript.txt  # Save to file

# Features
uv run src/main.py --chat                # Interactive chat to text mode
uv run src/main.py --chat-voice          # Chat with voice responses
uv run src/main.py --chat-id <ID>        # Continue existing chat session
uv run src/main.py --kokoro              # Enable text-to-speech
uv run src/main.py --optimize            # Enable voice optimization
uv run src/main.py --llm                 # Enable LLM processing
```

### Command Line Options

- `--single`: Run in single transcription mode
- `--copy`: Copy transcription to clipboard
- `--output-file FILE`: Save transcription to specified file
- `--chat`: Enable interactive chat mode
- `--chat-voice`: Enable chat with voice responses
- `--chat-id ID`: Continue an existing chat session
- `--kokoro`: Convert transcribed text to speech
- `--llm`: Process transcribed text through LLM
- `--optimize`: Apply voice optimization for better speech synthesis

## Project Structure

```
speech_to_text/
├── src/
│   ├── speech_to_text/
│   │   ├── __init__.py
│   │   ├── audio/        # Audio recording and processing
│   │   ├── chat/         # Chat functionality and history
│   │   ├── config/       # Configuration settings
│   │   ├── kokoro/       # Text-to-speech integration
│   │   ├── llm/          # Language model integration
│   │   ├── transcriber/  # Whisper model integration
│   │   └── utils/        # Utility functions
│   └── main.py           
├── pyproject.toml        # Project dependencies and metadata
├── uv.lock               # Dependency lock file
├── .python-version       # Python version specification
├── speech_to_text.sh     # Convenience script for running
└── README.md            
```

## Dependencies

Core Components:
- mlx-whisper: Speech recognition engine
- numpy: Numerical operations and audio processing
- PyAudio: Real-time audio capture
- pyperclip: Clipboard operations

Extended Features:
- openai: Kokoro text-to-speech API integration
- requests: LLM API communication
- json: Chat history persistence

Dependencies are managed through `pyproject.toml` and `uv.lock`. All dependencies are defined in the project's `pyproject.toml` file.

## Storage Locations

The application stores different types of data in the following locations:

### Chat History
- Location: Configured via `CHAT_HISTORY_DIR` in settings
- Format: JSON files (`{chat_id}.json`)
- Contains: Full conversation history with user and assistant messages

### Transcribed Text
- Location: Based on `--output-file` argument or `MLXW_OUTPUT_FILENAME`
- Format: Plain text files
- Contains: Raw transcription output

### LLM Responses
- Location: Configured via `LLM_OUTPUT_FILENAME` in settings
- Format: Text file with formatted responses and separators
- Contains: Processed text from LLM

### Speech/Audio Output
- Location: Configured via `KOKORO_OUTPUT_FILENAME` in settings
- Format: Based on `KOKORO_RESPONSE_FORMAT` setting
- Contains: Generated speech audio files (when not streaming)

## API Configuration

The application requires configuration for LLM and Kokoro services. Create a configuration file with your API settings:

```python
# config/settings.py
LLM_BASE_URL = "your_llm_api_url"
LLM_MODEL = "your_model"

KOKORO_BASE_URL = "your_kokoro_api_url"
KOKORO_API_KEY = "your_api_key"
KOKORO_MODEL = "your_model"
KOKORO_VOICE = "your_voice"
```

## 
This project is based on the article ["Real-time Speech-to-Text on macOS with MLX Whisper (with copy to pasteboard capabilities)"](https://maeda.pm/2024/11/10/real-time-speech-to-text-on-macos-with-mlx-whisper-with-copy-to-pasteboard-capabilities/) by Maeda.