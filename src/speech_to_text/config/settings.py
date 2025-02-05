# File: src/speech_to_text/config/settings.py
"""
Configuration settings for the speech-to-text application.
Environment variables take precedence over default values.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import pyaudio

# Load environment variables from .env file in project root
env_path = Path(__file__).parent.parent.parent.parent / ".env"
print(f"\n=== Configuration Initialization ===")
print(f"Looking for .env at: {env_path}")
print(f".env file exists: {env_path.exists()}\n")

load_dotenv(env_path, override=True)


def get_env_bool(key: str, default: bool) -> bool:
    """Convert environment string to boolean with fallback."""
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "t", "y", "yes")


def get_env_int(key: str, default: int) -> int:
    """Convert environment string to integer with fallback."""
    try:
        return int(os.getenv(key, default))
    except (TypeError, ValueError):
        return default


def get_env_float(key: str, default: float) -> float:
    """Convert environment string to float with fallback."""
    try:
        return float(os.getenv(key, default))
    except (TypeError, ValueError):
        return default


# Logging Settings
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(levelname)s - %(message)s")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # INFO | DEBUG

# Audio Recording Settings
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
SILENCE_CHUNKS = 15  # Increase to add delay before voice processing

# Default thresholds and calibration settings
DEFAULT_SILENCE_THRESHOLD = 500
CALIBRATION_FRAMES = 30
CALIBRATION_BUFFER = 200

# Output Directory Settings - ensure it's never empty
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "src/.cache")
if not OUTPUT_DIR:
    OUTPUT_DIR = "src/.cache"
    logging.warning(f"OUTPUT_DIR was empty, using default: {OUTPUT_DIR}")

# Whisper Model Settings
MODEL_NAME = os.getenv("MODEL_NAME", "mlx-community/whisper-tiny-mlx-q4")
VERBOSE = False
WORD_TIMESTAMPS = False

# Transcription Validation Settings
MINIMUM_WORD_COUNT = get_env_int("MINIMUM_WORD_COUNT", 3)
# Prevent LLM processing due to poor audio or short word count
SUSPICIOUS_RESPONSES = ["thank you.", "thank you", "thanks", "okay", "ok", "yes", "no"]

# Text Output Settings
MLXW_OUTPUT_FILENAME = f"{OUTPUT_DIR}/transcription.txt"

# Kokoro Text-to-Speech Settings
KOKORO_BASE_URL = os.getenv("KOKORO_BASE_URL", "http://127.0.0.1:8880/v1")
KOKORO_API_KEY = os.getenv("KOKORO_API_KEY", "not-needed")
KOKORO_MODEL = os.getenv("KOKORO_MODEL", "kokoro")
KOKORO_VOICE = os.getenv("KOKORO_VOICE", "af_bella")
KOKORO_SPEED = get_env_float("KOKORO_SPEED", 1.0)
KOKORO_RESPONSE_FORMAT = "mp3"
KOKORO_OUTPUT_FILENAME = f"{OUTPUT_DIR}/mlxw_to_kokoro_output.mp3"

# LLM Integration Settings
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:1234/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "lm-studio")
LLM_MODEL = os.getenv(
    "LLM_MODEL", "mistral-small-24b-instruct-2501@4bit"
)  # Updated default
LLM_MAX_TOKENS = get_env_int("LLM_MAX_TOKENS", 2048)
LLM_TEMPERATURE = get_env_float("LLM_TEMPERATURE", 0.7)
LLM_OUTPUT_FILENAME = f"{OUTPUT_DIR}/llm_response.txt"

# Chat History Settings
CHAT_HISTORY_DIR = f"{OUTPUT_DIR}/chat_history"
CHAT_PREVIEW_MAX_LENGTH = get_env_int("CHAT_PREVIEW_MAX_LENGTH", 500)  # Maximum length for chat previews
CHAT_FILE_EXTENSION = ".json"  # Standard extension for chat history files

# API Settings
SSE_RETRY_TIMEOUT = 3000    # Client retry interval in milliseconds if connection drops
SSE_KEEPALIVE_TIMEOUT = 5   # Keepalive interval in seconds
LLM_REQUEST_TIMEOUT = 600   # LLM request timeout in seconds (10 minutes)

# Print Configuration Summary
print("\n=== Path Configuration ===")
print(f"Output Directory: {OUTPUT_DIR}")

print("\n=== Output File Paths ===")
print(f"MLXW Output: {MLXW_OUTPUT_FILENAME}")
print(f"Kokoro Output: {KOKORO_OUTPUT_FILENAME}")
print(f"LLM Output: {LLM_OUTPUT_FILENAME}")
print(f"Chat History: {CHAT_HISTORY_DIR}\n")

print("\n=== Models ===")
print(f"Whisper: {MODEL_NAME}")
print(f"Kokoro: {KOKORO_MODEL} | {KOKORO_VOICE} | {KOKORO_SPEED}")
print(f"LMStudio: {LLM_MODEL}\n\n")