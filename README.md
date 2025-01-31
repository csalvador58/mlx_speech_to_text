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

## Requirements:

Run the following apps to access API endpoints:
- [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) - Text to Speech (Default: http://localhost:8880/v1)
- [LMStudio](https://lmstudio.ai) - LLM Provider (Default: http://localhost:1234/v1)

Whisper model:
- I recommend `mlx-community/whisper-large-v3-mlx`, default is set to `mlx-community/whisper-tiny-mlx-q4`
- ***Note***: Setting the whisper model with only the name in your .env file will start a new HTTPS connection with hugging face to check for the model at each launch. Set the variable with the model's full path to avoid this.
    - See a list of mlx-community uploaded models on [Hugging Face](https://huggingface.co/collections/mlx-community/whisper-663256f9964fbb1177db93dc)

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

Make script executable. *(Current script runs the clipboard mode, adjust for your needs)*:


```bash
chmod +x speech_to_text.sh
./speech_to_text.sh
```

### Using UV Run Directly

The application supports various modes and features:

- Example uses: 
    - I run the script instance for the speech to clipboard feature. I use Apple shortcuts to bind keys to send the `Enter` command to enable listening.
        - ```uv run src/main.py --copy```
    - I'll also run another app instance to for LLM Chat with voice using "--chat-voice".
        - ```uv run src/main.py --chat-voice --optimize```

    *Tip: Using the "--optimize" flag often works better with most models. Larger models don't really need it.*

```bash
# Basic Modes
uv run src/main.py --single    # Single Speech to Text
uv run src/main.py             # Continuous Speech to Text
uv run src/main.py --copy      # Enable text to clipboard

# Output Options
uv run src/main.py --output-file transcript.txt  # Save to file

# Features
uv run src/main.py --chat             # Enable LLM speech to text mode
uv run src/main.py --chat-voice       # Enable LLM voice mode
uv run src/main.py <...> --chat-id <ID>     # Continue existing chat session
uv run src/main.py --kokoro           # Enable Speech to Voice
uv run src/main.py --llm              # Enable LLM voice-text chat
                                
uv run src/main.py <...> --optimize                  # Enable voice optimizations
uv run src/main.py <...> --doc <path to text file>   # Enable appending doc text to chat

#  See /src/.cache directory for chat history, transriptions, and audio files.
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
- `--doc PATH`: Analyze a text document and discuss it in chat mode (supports ~ for home directory)


## Manual Speech Optimizations
Adjust in [text_optimization.py](src/speech_to_text/config/text_optimizations.py) file. Use to enhance word emphasis or even correct name pronunciations.

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
        "<|START_RESPONSE|>": "",  # Manually remove tokens
        "<|END_RESPONSE|>": "",
        ".": "...",  # Extend pause
        ":": ",",    # Natural pause
        ";": ",",    # Natural pause
        "–": " ",    # Space for readability
        "—": " ",    # Space for readability
        "|": ",",    # Natural pause
        "•": ",",    # Natural pause for bullets
    }
```


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

The application stores all file in ```src/.cache```:

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


## 
This project expanded on the article ["Real-time Speech-to-Text on macOS with MLX Whisper (with copy to pasteboard capabilities)"](https://maeda.pm/2024/11/10/real-time-speech-to-text-on-macos-with-mlx-whisper-with-copy-to-pasteboard-capabilities/) by Maeda.