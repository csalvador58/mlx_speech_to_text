# MLX Speech to Text Tool

A comprehensive speech-to-text platform that combines real-time transcription with LLM processing, chat capabilities, and text-to-speech conversion. Uses [MLX-Whisper](https://github.com/ml-explore), [Kokoro](https://github.com/remsky/Kokoro-FastAPI), and [LMStudio](https://lmstudio.ai).

## Features

- Real-time speech-to-text transcription using MLX Whisper
- Interactive chat mode with conversation history
- LLM integration for text processing and responses
- Text-to-speech conversion with Kokoro
- Voice optimization for improved speech synthesis
- Multiple output options (clipboard, file, speakers)
- Automatic silence detection and background noise calibration
- Document analysis and chat integration

## Requirements

Install and Run the following apps to access API endpoints:
- [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) - Text to Speech (Default: http://127.0.0.1:8880/v1)
- [LMStudio](https://lmstudio.ai) - LLM Provider (Default: http://127.0.0.1:1234/v1)
    - *Works with any platform supporting OpenAI endpoints:* ```POST /v1/chat/completions```

Whisper model:
- I recommend `mlx-community/whisper-large-v3-mlx`, default is set to `mlx-community/whisper-tiny-mlx-q4`
- ***Note***: Setting the whisper model with only the name in your .env file will start a new HTTPS connection with hugging face to check for the model at each launch. Set the variable with the model's full path to avoid this.
    - See a list of mlx-community uploaded models on [Hugging Face](https://huggingface.co/collections/mlx-community/whisper-663256f9964fbb1177db93dc)

[PortAudio](https://www.portaudio.com):
- Needed by PyAudio library to stream audio
```bash
brew install portaudio
```

## Setup

1. Clone the repository
2. Setup the development environment:

```bash
# Setup Whisper model, Kokoro, and LMStudio settings
cp .env.example .env
```
- Set up the base urls of Kokoro and LMStudio in your .env file

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install dependencies and set up development environment
uv sync
```

## Usage

### Using the Shell Script

Make script executable *(Current script runs the clipboard mode, adjust for your needs)*:

```bash
chmod +x speech_to_text.sh
./speech_to_text.sh
```

### Using UV Run Directly

The application supports various modes and features:

```bash
# Basic Modes
uv run src/main.py --single    # Single Speech to Text
uv run src/main.py             # Continuous Speech to Text
uv run src/main.py --copy      # Enable text to clipboard

# Output Options
uv run src/main.py --output-file transcript.txt  # Save to file

# Features
uv run src/main.py --chat             # Enable LLM speech to text mode
uv run src/main.py --chat-voice       # Enable LLM voice mode (stream only)
uv run src/main.py --chat-voice-save  # Enable LLM voice mode with file saving
uv run src/main.py <...> --chat-id <ID>     # Continue existing chat session
uv run src/main.py --kokoro           # Enable Speech to Voice
uv run src/main.py --llm              # Enable LLM voice-text chat
                                
uv run src/main.py <...> --optimize                  # Enable voice optimizations
uv run src/main.py <...> --doc <path to text file>   # Enable appending doc text to chat

#  See /src/.cache directory for chat history, transriptions, and audio files.
```

### API Reference

For detailed API documentation, including endpoints, parameters, and example requests, see [API Documentation](src/docs/Speech%20To%20Text%20Endpoints.md).

### Quick API Examples

```bash
# Basic chat mode
curl -X POST "http://127.0.0.1:8081/api/connect/chat/start?mode=chat"

# Voice mode with optimization and document
curl -X POST "http://127.0.0.1:8081/api/connect/chat/start?mode=voice&optimize=true&doc=/path/to/doc.txt"

# Voice-save mode with existing chat
curl -X POST "http://127.0.0.1:8081/api/connect/chat/start?mode=voice-save&chat_id=existing_chat_id"
```

### Speech Optimizations Configuration

Adjust in [text_optimization.py](src/speech_to_text/config/text_optimizations.py) file to enhance word emphasis or correct name pronunciations:

```python
def get_default_abbreviations() -> Dict[str, str]:
    return {
        "api": "A P I",
        "url": "U R L",
        "sql": "S Q L",
        "html": "H T M L",
        "css": "C S S",
        "js": "JavaScript",
        "jwt": "J W T",
        "ui": "U I",
        "ux": "U X",
    }

def get_default_char_replacements() -> Dict[str, str]:
    return {
        "<|START_RESPONSE|>": "",  # Remove tokens
        "<|END_RESPONSE|>": "",
        ".": "...",  # Extend pause
        ":": ",",    # Natural pause
        ";": ",",    # Natural pause
    }

def get_default_pronunciations() -> Dict[str, str]:
    return {
        "pikachu": "peeka-chu",
    }
```

## Project Structure

```
speech_to_text/
├── src/
│   ├── docs/             # Documentation
│   │   └── Speech To Text Endpoints.md
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

## Local Data Storage

The application stores all generated files in [src/.cache](src/.cache):

- **Chat History**: JSON files containing conversation history (`{chat_id}.json`)
- **Transcribed Text**: Raw transcription output in plain text files
- **LLM Responses**: Processed text from LLM with formatted responses
- **Speech/Audio Output**: Generated speech audio files when not streaming

### (Optional) Add Apple Shortcut
Set a shortcut to send ENTER cmd to first session in an iTerm window: [iCloud Link to Shortcut](https://www.icloud.com/shortcuts/014c924d6e53423a8d10aefb6625ca21)

## 
This project expanded on the article ["Real-time Speech-to-Text on macOS with MLX Whisper (with copy to pasteboard capabilities)"](https://maeda.pm/2024/11/10/real-time-speech-to-text-on-macos-with-mlx-whisper-with-copy-to-pasteboard-capabilities/) by Maeda.