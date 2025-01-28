# File: src/speech_to_text/config/settings.py
"""
Configuration settings for the speech-to-text application.
"""

import pyaudio

# Audio Recording Settings
AUDIO_FORMAT = pyaudio.paInt16  # Audio format (16-bit int)
CHANNELS = 1                    # Number of audio channels (mono)
SAMPLE_RATE = 16000            # Sampling rate (16 kHz)
CHUNK_SIZE = 1024              # Buffer size
SILENCE_CHUNKS = 50            # Number of consecutive chunks of silence before stopping

# Whisper Model Settings
# MODEL_NAME = "mlx-community/whisper-tiny"  # Default model
MODEL_NAME = "mlx-community/whisper-large-v3-mlx"
VERBOSE = False                # Verbose output from transcriber
WORD_TIMESTAMPS = False        # Whether to include word timestamps

# Logging Settings
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"              # Set to DEBUG or INFO

# Default values
DEFAULT_SILENCE_THRESHOLD = 500  # Default threshold for silence detection
CALIBRATION_FRAMES = 30         # Number of frames to use for calibration
CALIBRATION_BUFFER = 200        # Buffer to add to mean noise level

# Output Directory Settings
OUTPUT_DIR = "src/.cache"  # Base directory for output files
MLXW_OUTPUT_FILENAME = f"{OUTPUT_DIR}/mlxw_to_text.txt"

# Kokoro Text-to-Speech Settings
KOKORO_BASE_URL = "http://localhost:8880/v1"
KOKORO_API_KEY = "not-needed"
KOKORO_MODEL = "kokoro"
KOKORO_VOICE = "af"
KOKORO_RESPONSE_FORMAT = "mp3"
KOKORO_OUTPUT_FILENAME = f"{OUTPUT_DIR}/mlxw_to_kokoro_output.mp3"
TRANSCRIPTION_OUTPUT_FILENAME = f"{OUTPUT_DIR}/transcription.txt"