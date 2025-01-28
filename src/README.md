# Speech to Text Transcription Tool

A real-time speech-to-text transcription tool using MLX Whisper.

## Quick Start

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install dependencies and set up development environment
uv sync

# Run with clipboard support
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

Make script executable, then run. Will run --> uv run src/main.py --copy:

```bash
chmod +x speech_to_text.sh
./speech_to_text.sh
```



### Using UV Run Directly

The application can be run in different modes:

```bash
# Single Transcription Mode
uv run src/main.py --single

# Continuous Mode
uv run src/main.py

# With clipboard support
uv run src/main.py --copy

# Save to file
uv run src/main.py --output-file transcript.txt
```

### Command Line Options

- `--copy`: Copy transcription to clipboard
- `--output-file FILE`: Save transcription to specified file
- `--single`: Run in single transcription mode

## Project Structure

```
speech_to_text/
├── src/
│   ├── speech_to_text/
│   │   ├── __init__.py
│   │   ├── audio/        # Audio recording functionality
│   │   ├── config/       # Configuration settings
│   │   ├── transcriber/  # Whisper model integration
│   │   └── utils/        # Utility functions
│   └── main.py           
├── pyproject.toml        
├── uv.lock              
├── .python-version      
├── speech_to_text.sh    # Convenience script for running
└── README.md           
```

## Dependencies

The project uses:
- mlx-whisper: For speech recognition
- numpy: For numerical operations
- PyAudio: For audio capture
- pyperclip: For clipboard operations

Dependencies are managed through `pyproject.toml` and `uv.lock`. All dependencies are defined in the project's `pyproject.toml` file.

## 
This project is based on the article ["Real-time Speech-to-Text on macOS with MLX Whisper (with copy to pasteboard capabilities)"](https://maeda.pm/2024/11/10/real-time-speech-to-text-on-macos-with-mlx-whisper-with-copy-to-pasteboard-capabilities/) by Maeda.